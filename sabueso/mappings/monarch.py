"""Original Monarch association occurrences, with native qualifiers and page scope."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

CURIE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9_.-]+\Z")
LIST_FIELDS = (
    "aggregator_knowledge_source",
    "publications",
    "has_evidence",
    "qualifiers",
    "subject_closure",
    "object_closure",
)


def entity_id(identifier):
    if not isinstance(identifier, str) or not CURIE.fullmatch(identifier):
        raise ConnectorError(
            "Monarch requires one exact namespace-qualified entity CURIE."
        )
    return identifier


def response_query(identifier, limit, offset):
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ConnectorError("Monarch page limit must be an integer from 1 to 500.")
    if type(offset) is not int or offset < 0:
        raise ConnectorError("Monarch offset must be a nonnegative integer.")
    return {
        "subject": entity_id(identifier),
        "direct": "true",
        "limit": limit,
        "offset": offset,
    }


def validate_page(payload, identifier, limit, offset):
    """Check the entire native expanded page, with exact direct-subject binding."""
    query = response_query(identifier, limit, offset)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("Monarch response is not finite JSON.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ConnectorError("Monarch response must be its native expanded page.")
    for k in ("limit", "offset", "total"):
        if type(payload.get(k)) is not int or payload[k] < 0:
            raise ConnectorError("Monarch native page counts are missing or malformed.")
    if payload["limit"] != query["limit"] or payload["offset"] != query["offset"]:
        raise ConnectorError("Monarch native page scope differs from the request.")
    count, total = len(payload["items"]), payload["total"]
    if count > limit or (count and offset + count > total):
        raise ConnectorError("Monarch page counts contradict the returned rows.")
    if not count and offset < total:
        raise ConnectorError("Monarch empty page precedes its declared total.")
    for row in payload["items"]:
        if not isinstance(row, dict):
            raise ConnectorError("Monarch native association is malformed.")
        for k in ("id", "predicate", "subject", "object"):
            entity_id(row.get(k))
        if row["subject"] != identifier:
            raise ConnectorError(
                "Monarch row does not have the exact direct query subject."
            )
        for k in ("knowledge_level", "agent_type"):
            if not isinstance(row.get(k), str) or not row[k]:
                raise ConnectorError(
                    "Monarch native knowledge/agent declaration is missing."
                )
        for k in LIST_FIELDS:
            if (
                k in row
                and row[k] is not None
                and (
                    not isinstance(row[k], list)
                    or any(not isinstance(v, str) or not v for v in row[k])
                )
            ):
                raise ConnectorError(
                    "Monarch native support/qualifier list is malformed."
                )
        for k in (
            "primary_knowledge_source",
            "original_subject",
            "original_object",
            "category",
            "subject_category",
            "object_category",
            "subject_taxon",
            "object_taxon",
        ):
            if (
                k in row
                and row[k] is not None
                and (not isinstance(row[k], str) or not row[k])
            ):
                raise ConnectorError(
                    "Monarch native source/entity context is malformed."
                )
        if (
            "negated" in row
            and row["negated"] is not None
            and type(row["negated"]) is not bool
        ):
            raise ConnectorError("Monarch negation must be its native boolean or null.")
        for k in ("evidence_count", "has_count", "has_total"):
            if (
                k in row
                and row[k] is not None
                and (type(row[k]) is not int or row[k] < 0)
            ):
                raise ConnectorError(
                    "Monarch native support/frequency count is malformed."
                )
    return payload


def page_is_partial(payload):
    return len(payload["items"]) < payload["total"]


def map_associations(envelope):
    """Retain all categories and occurrences, without protein transfer or inference.

    Native ECO pointers, agent/knowledge labels and qualifiers stay source claims.
    Gene/disease/phenotype relationships are about their declared entities; neither
    a normalized identifier nor the query's direct flag supplies physical binding.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "Monarch"
        or envelope.get("kind") != "associations"
        or envelope.get("version") is not None
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "Monarch mapping requires a native association page envelope."
        )
    query = envelope["query"]
    expected = response_query(
        query.get("subject"), query.get("limit"), query.get("offset")
    )
    if query != expected:
        raise ConnectorError("Monarch query scope is unsupported.")
    record = validate_page(
        envelope.get("record"), query["subject"], query["limit"], query["offset"]
    )
    if envelope.get("truncated") is not page_is_partial(record):
        raise ConnectorError("Monarch envelope cut differs from native page coverage.")
    response_hash, query_hash = (
        digest(canonical_json(record)),
        digest(canonical_json(query)),
    )
    assertions = []
    for index, row in enumerate(record["items"]):
        assertion = make_source_assertion(
            "associations.monarch",
            deepcopy(row),
            "Monarch",
            f"{query_hash}:{response_hash}:row:{index}:{row['id']}",
            envelope.get("retrieved_at"),
            subject_ref=f"monarch:association:{row['id']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_association": deepcopy(row),
            "native_row_index": index,
            "response_hash": response_hash,
            "query": deepcopy(query),
            "page": {
                "limit": record["limit"],
                "offset": record["offset"],
                "total": record["total"],
                "returned": len(record["items"]),
                "partial": page_is_partial(record),
            },
            "mapping_scope": {
                "identity": "native_association_and_entities; no_gene_to_protein_transfer_or_identity_merge",
                "support": "native_primary_and_aggregator_sources; ECO_pointers_are_source_claims_not_MOLI_Evidence",
                "query": "exact_direct_subject; direct_is_query_matching_not_physical_binding",
                "revision": "KG_association_entity_and_sequence_revisions_not_stated; API_version_is_separate",
                "coverage": "one_received_page; no_implicit_followup_or_absence_claim",
                "terms": "input_specific_rights; no_blanket_software_or_KG_grant",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
