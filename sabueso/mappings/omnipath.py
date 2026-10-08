"""Native OmniPath interaction occurrences with independent effects and support."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)
FLAGS = (
    "is_directed",
    "is_stimulation",
    "is_inhibition",
    "consensus_direction",
    "consensus_stimulation",
    "consensus_inhibition",
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("OmniPath requires one exact base UniProt accession.")
    return identifier.upper()


def response_query(identifier):
    return {
        "partners": accession(identifier),
        "datasets": "omnipath",
        "organisms": 9606,
        "fields": "sources,references",
        "format": "json",
        "license": "academic",
    }


def validate_interactions(payload, identifier):
    """Validate every received row; an HTTP-200 application error is not empty."""
    identifier = accession(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("OmniPath response is not finite JSON.") from error
    if not isinstance(payload, list):
        raise ConnectorError("OmniPath response must be its native row array.")
    for row in payload:
        if not isinstance(row, dict):
            raise ConnectorError("OmniPath row or application response is malformed.")
        if any(
            not isinstance(row.get(k), str) or not row[k] or row[k] != row[k].strip()
            for k in ("source", "target")
        ):
            raise ConnectorError("OmniPath native participants are malformed.")
        if identifier not in (row["source"], row["target"]):
            raise ConnectorError(
                "OmniPath row does not contain the exact query partner."
            )
        if any(type(row.get(k)) is not bool for k in FLAGS):
            raise ConnectorError(
                "OmniPath native direction/effect flags must be booleans."
            )
        sources = row.get("sources")
        if not isinstance(sources, list) or any(
            not isinstance(v, str) or not v or v != v.strip() for v in sources
        ):
            raise ConnectorError("OmniPath resource support is malformed.")
        references = row.get("references")
        if not isinstance(references, str) or (
            references
            and any(
                not re.fullmatch(r"[^:;\s]+:[^;\s]+", v) for v in references.split(";")
            )
        ):
            raise ConnectorError("OmniPath resource-prefixed references are malformed.")
    return payload


def map_interactions(envelope):
    """Retain each native aggregate occurrence, without a unified effect or class.

    Resource/reference annotations can include support outside the queried dataset;
    no client-side strict-evidence reconstruction is performed. Direction and signs
    are source declarations, without a direct-binding or experimental inference.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "OmniPath"
        or envelope.get("kind") != "interactions"
        or not isinstance(envelope.get("query"), dict)
        or canonical_json(envelope["query"])
        != canonical_json(response_query(envelope["query"].get("partners")))
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "OmniPath mapping requires the exact native query envelope."
        )
    query = envelope["query"]
    rows = validate_interactions(envelope.get("record"), query["partners"])
    response_hash = digest(canonical_json(rows))
    query_hash = digest(canonical_json(query))
    assertions = []
    for index, row in enumerate(rows):
        row_hash = digest(canonical_json(row))
        pair_hash = digest(canonical_json([row["source"], row["target"]]))
        assertion = make_source_assertion(
            "interactions.omnipath",
            deepcopy(row),
            "OmniPath",
            f"{query_hash}:{response_hash}:row:{index}:{row_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"omnipath:interaction:{pair_hash}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "native_row_index": index,
            "response_hash": response_hash,
            "query": deepcopy(query),
            "mapping_scope": {
                "identity": "native_ordered_participant_pair; no_gene_label_or_protein_identity_merge",
                "effect": "independent_native_flags_and_consensus; no_precedence_or_binding_class",
                "support": "original_aggregate_resources_and_prefixed_references; not_strict_dataset_filtered",
                "taxonomy": "human_query; observed_participant_taxonomy_not_returned",
                "revision": "dataset_interaction_and_support_revisions_not_stated",
                "coverage": "all_received_occurrences; no_native_total_or_database_completeness_claim",
                "terms": "resource_specific_rights; academic_filter_is_not_a_reuse_grant",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
