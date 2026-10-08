"""Native CIViC accepted items on complete molecular-profile subjects."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

COLUMNS = (
    "molecular_profile",
    "molecular_profile_id",
    "disease",
    "doid",
    "phenotypes",
    "therapies",
    "therapy_interaction_type",
    "evidence_type",
    "evidence_direction",
    "evidence_level",
    "significance",
    "evidence_statement",
    "citation_id",
    "source_type",
    "asco_abstract_id",
    "citation",
    "nct_ids",
    "rating",
    "evidence_status",
    "evidence_id",
    "variant_origin",
    "last_review_date",
    "evidence_civic_url",
    "molecular_profile_civic_url",
    "is_flagged",
)
MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def profile_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[1-9][0-9]*", identifier):
        raise ConnectorError(
            "CIViC requires one exact positive molecular-profile ID string."
        )
    return identifier


def monthly_release(release):
    if (
        not isinstance(release, str)
        or not re.fullmatch(r"01-[A-Z][a-z]{2}-[0-9]{4}", release)
        or release[3:6] not in MONTHS
        or int(release[-4:]) == 0
    ):
        raise ConnectorError(
            "CIViC requires an explicit monthly release, such as 01-Oct-2026."
        )
    return release


def response_query(identifier, release):
    return {
        "molecular_profile_id": profile_id(identifier),
        "release": monthly_release(release),
        "dataset": "accepted_clinical_evidence_summaries",
    }


def parse_export(text):
    """Validate every native row before selection; retain original field strings."""
    if not isinstance(text, str) or not text or "\x00" in text:
        raise ConnectorError(
            "CIViC requires original native accepted-evidence TSV text."
        )
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter="\t", strict=True))
    except csv.Error as error:
        raise ConnectorError(f"Malformed CIViC TSV: {error}") from error
    if not rows or tuple(rows[0]) != COLUMNS:
        raise ConnectorError("CIViC native header is malformed.")
    out = []
    for index, values in enumerate(rows[1:]):
        if len(values) != len(COLUMNS):
            raise ConnectorError("CIViC native row width is malformed.")
        row = dict(zip(COLUMNS, values))
        if (
            not re.fullmatch(r"[1-9][0-9]*", row["molecular_profile_id"])
            or not re.fullmatch(r"[1-9][0-9]*", row["evidence_id"])
            or not row["molecular_profile"]
            or row["evidence_status"] != "accepted"
            or row["evidence_civic_url"]
            != "https://civicdb.org/links/evidence_items/" + row["evidence_id"]
            or row["molecular_profile_civic_url"]
            != "https://civicdb.org/links/molecular_profiles/"
            + row["molecular_profile_id"]
        ):
            raise ConnectorError(
                "CIViC native identity, link or accepted status is malformed."
            )
        out.append({"native_row_index": index, "fields": row})
    return {"rows": out}


def map_molecular_profile_items(envelope):
    """Preserve each accepted item without expanding profiles or therapy combinations.

    CIViC Evidence Items and CIViC Assertions are source concepts, not MOLI
    Evidence. Directions, significance, ratings and levels stay literal; no
    consensus, efficacy, protein identity or clinical interpretation is inferred.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "CIViC"
        or envelope.get("kind") != "molecular_profile_items"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"molecular_profile_id", "release", "dataset"}
        or envelope["query"]["dataset"] != "accepted_clinical_evidence_summaries"
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "CIViC mapping requires a qualified monthly accepted-items export."
        )
    identifier = profile_id(envelope["query"]["molecular_profile_id"])
    release = monthly_release(envelope["query"]["release"])
    if envelope.get("version") != release:
        raise ConnectorError(
            "CIViC source revision differs from the requested release."
        )
    native = parse_export(envelope.get("record"))
    response_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    out = []
    for item in native["rows"]:
        row = item["fields"]
        if row["molecular_profile_id"] != identifier:
            continue
        index = item["native_row_index"]
        assertion = make_source_assertion(
            "genetics.civic.molecular_profile_items",
            deepcopy(row),
            "CIViC",
            f"item:{row['evidence_id']}:release:{release}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"civic:molecular_profile:{identifier}",
        )
        assertion["source"]["version"] = release
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "received_export_rows": len(native["rows"]),
            "query_molecular_profile_id": identifier,
            "mapping_scope": {
                "identity": "exact_native_molecular_profile_ID; no_variant_gene_or_protein_merge",
                "interpretation": "native_item_fields; no_profile_or_therapy_expansion_consensus_or_clinical_inference",
                "source_concepts": "CIViC_Evidence_Item_is_not_MOLI_Evidence; accepted_is_not_unflagged",
                "revisions": "explicit_monthly_export_label; entity_and_sequence_revisions_not_stated",
                "coverage": "all_received_accepted_export_rows_validated; no_independent_database_total",
                "absence": "not_listed_is_not_negative_association_or_no_clinical_relevance",
            },
        }
        for key in ("snapshot_receipt", "download_sha256"):
            if key in envelope:
                assertion["source_metadata"][key] = deepcopy(envelope[key])
        out.append(assertion)
    return out
