"""Source-declared Pharos target identity and development-level metadata."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://pharos-api.ncats.io/graphql"
QUERY = "query SabuesoTarget($accession: String!) { target(q: {uniprot: $accession}) { name sym uniprot tdl fam } }"
FIELDS = ("name", "sym", "uniprot", "tdl", "fam")


def response_query(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[A-Z0-9]{6,10}", identifier
    ):
        raise ConnectorError("Pharos requires one exact base accession literal.")
    return {"uniprot": identifier, "operation": "target", "fields": list(FIELDS)}


def validate_target(payload, identifier):
    """Reject GraphQL errors and identity mismatches; retain native null distinctly."""
    response_query(identifier)
    try:
        canonical_json(payload)
    except (StorageError, ValueError, TypeError) as error:
        raise ConnectorError("Pharos requires finite native JSON.") from error
    if (
        not isinstance(payload, dict)
        or "errors" in payload
        or not isinstance(payload.get("data"), dict)
        or set(payload["data"]) != {"target"}
    ):
        raise ConnectorError("Pharos response is malformed or contains GraphQL errors.")
    target = payload["data"]["target"]
    if target is None:
        return None
    if (
        not isinstance(target, dict)
        or set(target) != set(FIELDS)
        or target.get("uniprot") != identifier
        or any(target[k] is not None and not isinstance(target[k], str) for k in FIELDS)
    ):
        raise ConnectorError(
            "Pharos target identity or selected fields are unsupported."
        )
    return target


def map_target(envelope):
    """Retain the provider's TDL class; do not compute a druggability score."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "Pharos/TCRD"
        or envelope.get("kind") != "target"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("Pharos requires a complete target envelope.")
    query = envelope["query"]
    if query != response_query(query.get("uniprot")):
        raise ConnectorError("Unsupported Pharos field or query scope.")
    target = validate_target(envelope.get("record"), query["uniprot"])
    if target is None:
        return []
    response_hash = digest(canonical_json(envelope["record"]))
    assertion = make_source_assertion(
        "annotations.target_development_context",
        deepcopy(target),
        "Pharos/TCRD",
        f"{target['uniprot']}:{response_hash}",
        envelope.get("retrieved_at"),
        subject_ref=f"pharos:target:{target['uniprot']}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_response": deepcopy(envelope["record"]),
        "response_hash": response_hash,
        "query": deepcopy(query),
        "mapping_scope": {
            "identity": "exact_native_uniprot; no_name_similarity_or_gene_protein_merge",
            "classification": "Pharos_TCRD_native_tdl_literal; no_rank_or_Sabueso_rule",
            "revision": "dataset_record_sequence_and_TDL_rule_revisions_not_stated",
            "coverage": "five_requested_target_fields; aggregate_associations_and_ligands_unqueried",
            "terms": "separate_data_grant_NOT_STATED; contributing_source_rights_separate",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return [assertion]
