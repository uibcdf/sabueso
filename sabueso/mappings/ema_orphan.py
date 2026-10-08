"""Native EMA orphan-designation pages without product or protein identity inference."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "EMA Orphan Designations"
FIELDS = (
    "medicine_name",
    "related_ema_product_number",
    "active_substance",
    "date_of_designation_or_refusal",
    "intended_use",
    "eu_designation_number",
    "status",
    "first_published_date",
    "last_updated_date",
    "orphan_designation_url",
)


def designation_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"EU/3/[0-9]{2}/[0-9]+", identifier
    ):
        raise ConnectorError(
            "EMA orphan access requires one exact EU/3/YY/number identifier."
        )
    return identifier


def response_query(identifier):
    return {
        "eu_designation_number": designation_id(identifier),
        "dataset": "orphan_designation_pages",
    }


def validate_export(payload):
    """Validate declared coverage and every original page before exact selection.

    The native EU-number field includes unknown/absent-number literals and other
    EMA references. Preserve those original strings; page URLs identify source
    pages independently of EU-number query matching. Future fields remain raw.
    """
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("EMA orphan export must be finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("meta"), dict)
        or not isinstance(payload.get("data"), list)
    ):
        raise ConnectorError("EMA orphan native meta/data export is malformed.")
    meta = payload["meta"]
    count = meta.get("total_records")
    timestamp = meta.get("timestamp")
    if (
        type(count) is not int
        or count < 0
        or count != len(payload["data"])
        or not isinstance(timestamp, str)
        or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", timestamp
        )
    ):
        raise ConnectorError(
            "EMA orphan declared total or generation timestamp is malformed."
        )
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as error:
        raise ConnectorError("EMA orphan generation timestamp is invalid.") from error
    for row in payload["data"]:
        if (
            not isinstance(row, dict)
            or any(not isinstance(row.get(k), str) for k in FIELDS)
            or not row["eu_designation_number"]
            or not re.fullmatch(
                r"https://www\.ema\.europa\.eu/en/medicines/human/orphan-designations/[a-z0-9][a-z0-9-]*",
                row["orphan_designation_url"],
            )
        ):
            raise ConnectorError(
                "EMA orphan native page shape or identity is malformed."
            )
    return payload


def map_designations(envelope):
    """Keep independent page occurrences and literal procedural declarations.

    A designation/procedural status is not marketing authorisation, efficacy,
    drug modality, molecule identity or a protein-target relationship. Repeated
    EU numbers, different pages/dates, unknown labels and absent fields survive.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != SOURCE
        or envelope.get("kind") != "designations"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"eu_designation_number", "dataset"}
        or envelope["query"]["dataset"] != "orphan_designation_pages"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "EMA orphan mapping requires a qualified complete native export."
        )
    identifier = designation_id(envelope["query"]["eu_designation_number"])
    payload = validate_export(envelope.get("record"))
    response_hash = digest(canonical_json(payload))
    out = []
    for index, row in enumerate(payload["data"]):
        if row["eu_designation_number"] != identifier:
            continue
        url = row["orphan_designation_url"]
        assertion = make_source_assertion(
            "regulatory.orphan_designations.ema",
            deepcopy(row),
            SOURCE,
            f"{url}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"ema:orphan_page:{url}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "native_export_metadata": deepcopy(payload["meta"]),
            "query_eu_designation_number": identifier,
            "mapping_scope": {
                "identity": "exact_native_EU_number_match; independent_source_pages; no_product_molecule_or_protein_merge",
                "regulatory": "literal_designation_procedure; no_marketing_authorisation_efficacy_or_modality_inference",
                "dates": "native_generation_publication_update_and_designation_dates; retrieval_time_is_separate",
                "coverage": "all_received_rows_validated; native_total_matches_received_rows; no_independent_registry_total",
                "revisions": "dataset_designation_product_and_sequence_revisions_not_stated",
                "absence": "not_listed_is_not_no_designation_no_approval_or_negative_clinical_relevance",
            },
        }
        for key in ("snapshot_receipt", "download_sha256"):
            if key in envelope:
                assertion["source_metadata"][key] = deepcopy(envelope[key])
        out.append(assertion)
    return out
