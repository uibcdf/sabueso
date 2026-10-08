"""Original ClinGen gene-disease validity declarations from the native CSV export."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from copy import deepcopy
from datetime import date, datetime

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

GENE = re.compile(r"HGNC:[1-9][0-9]*\Z")
DISEASE = re.compile(r"MONDO:[0-9]{7}\Z")
REPORT = re.compile(
    r"https://search\.clinicalgenome\.org/kb/gene-validity/"
    r"(?:CGGV|CGGCIEX):assertion_[A-Za-z0-9_.:-]+\Z"
)
COLUMNS = (
    "GENE SYMBOL",
    "GENE ID (HGNC)",
    "DISEASE LABEL",
    "DISEASE ID (MONDO)",
    "MOI",
    "SOP",
    "CLASSIFICATION",
    "ONLINE REPORT",
    "CLASSIFICATION DATE",
    "GCEP",
)
PAGE = "https://search.clinicalgenome.org/kb/gene-validity"


def gene_id(identifier):
    if not isinstance(identifier, str) or not GENE.fullmatch(identifier):
        raise ConnectorError("ClinGen requires one exact HGNC gene identifier.")
    return identifier


def response_query(identifier):
    return {"hgnc_id": gene_id(identifier), "dataset": "gene_disease_validity"}


def _separator(row):
    return len(row) == len(COLUMNS) and all(re.fullmatch(r"\++", v) for v in row)


def parse_export(text):
    """Validate the complete native export, including unrelated rows, before selection.

    File creation and classification dates are native labels, not dataset/sequence
    revisions or independently observed retrieval times. Legacy report namespaces
    and classification dates with unspecified timezone are retained literally.
    """
    if not isinstance(text, str) or not text or "\x00" in text:
        raise ConnectorError("ClinGen requires original native CSV text.")
    try:
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except csv.Error as error:
        raise ConnectorError(f"Malformed ClinGen CSV: {error}") from error
    if (
        len(rows) < 6
        or any(len(r) != len(COLUMNS) for r in rows)
        or rows[0] != ["CLINGEN GENE DISEASE VALIDITY CURATIONS"] + [""] * 9
        or not rows[1][0].startswith("FILE CREATED: ")
        or any(rows[1][1:])
        or rows[2] != [f"WEBPAGE: {PAGE}"] + [""] * 9
        or not _separator(rows[3])
        or tuple(rows[4]) != COLUMNS
        or not _separator(rows[5])
    ):
        raise ConnectorError("ClinGen native preamble/header/row width is malformed.")
    file_created = rows[1][0].removeprefix("FILE CREATED: ")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", file_created):
        raise ConnectorError("ClinGen native file creation date is malformed.")
    try:
        date.fromisoformat(file_created)
    except ValueError as error:
        raise ConnectorError(
            "ClinGen native file creation date is malformed."
        ) from error
    out = []
    for index, values in enumerate(rows[6:]):
        row = dict(zip(COLUMNS, values))
        if (
            any(not v for v in values)
            or not GENE.fullmatch(row["GENE ID (HGNC)"])
            or not DISEASE.fullmatch(row["DISEASE ID (MONDO)"])
            or not REPORT.fullmatch(row["ONLINE REPORT"])
        ):
            raise ConnectorError(
                "ClinGen native curation identity/context is malformed."
            )
        try:
            datetime.fromisoformat(row["CLASSIFICATION DATE"])
        except ValueError as error:
            raise ConnectorError(
                "ClinGen native classification date is malformed."
            ) from error
        out.append({"native_row_index": index, "fields": row})
    return {"file_created": file_created, "rows": out}


def map_gene_validity(envelope):
    """Keep every matched gene declaration and its full native context independently.

    Classification, inheritance, SOP, date and expert-panel labels remain source
    assertions. No strongest-class selection, gene/protein identity merge, variant
    interpretation, clinical recommendation, score or experimental class is derived.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "ClinGen"
        or envelope.get("kind") != "gene_validity"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"hgnc_id", "dataset"}
        or envelope["query"]["dataset"] != "gene_disease_validity"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("ClinGen mapping requires a qualified native gene export.")
    identifier = gene_id(envelope["query"]["hgnc_id"])
    native = parse_export(envelope.get("record"))
    response_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    out = []
    for item in native["rows"]:
        row = item["fields"]
        if row["GENE ID (HGNC)"] != identifier:
            continue
        index = item["native_row_index"]
        assertion = make_source_assertion(
            "disease.gene_validity.clingen",
            deepcopy(row),
            "ClinGen",
            f"{row['ONLINE REPORT']}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"clingen:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "received_export_rows": len(native["rows"]),
            "native_file_created": native["file_created"],
            "mapping_scope": {
                "identity": "exact_native_gene; no_protein_isoform_or_variant_identity_merge",
                "interpretation": "native_classification_inheritance_SOP_and_panel; no_ranking_or_clinical_inference",
                "revisions": "dataset_gene_and_sequence_revisions_not_stated; dates_are_not_revisions",
                "coverage": "all_received_export_rows_validated; no_independent_database_total",
                "absence": "not_listed_in_received_export_is_not_no_disease_relationship",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        out.append(assertion)
    return out
