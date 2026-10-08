"""Native drug-target observations without target-group or potency inference."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)
COLUMNS = (
    "DRUG_NAME",
    "STRUCT_ID",
    "TARGET_NAME",
    "TARGET_CLASS",
    "ACCESSION",
    "GENE",
    "SWISSPROT",
    "ACT_VALUE",
    "ACT_UNIT",
    "ACT_TYPE",
    "ACT_COMMENT",
    "ACT_SOURCE",
    "RELATION",
    "MOA",
    "MOA_SOURCE",
    "ACT_SOURCE_URL",
    "MOA_SOURCE_URL",
    "ACTION_TYPE",
    "TDL",
    "ORGANISM",
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier):
        raise ConnectorError("DrugCentral requires one exact base UniProt accession.")
    return identifier


def response_query(identifier):
    return {"accession": accession(identifier), "dataset": "drug_target_interactions"}


def parse_export(text):
    """Validate the complete 20-column TSV before exact native token selection.

    Fields remain original strings, including empty activity units and MOA labels.
    Pipe-separated native target identifiers describe the original target group;
    a match to one token does not transfer the observation to that protein alone.
    """
    if not isinstance(text, str) or not text or "\x00" in text:
        raise ConnectorError("DrugCentral requires original native TSV text.")
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter="\t", strict=True))
    except csv.Error as error:
        raise ConnectorError(f"Malformed DrugCentral TSV: {error}") from error
    if not rows or tuple(rows[0]) != COLUMNS:
        raise ConnectorError("DrugCentral native header is malformed.")
    out = []
    for index, values in enumerate(rows[1:]):
        if len(values) != len(COLUMNS):
            raise ConnectorError("DrugCentral native row width is malformed.")
        row = dict(zip(COLUMNS, values))
        tokens = row["ACCESSION"].split("|")
        if (
            not re.fullmatch(r"[1-9][0-9]*", row["STRUCT_ID"])
            or not row["DRUG_NAME"]
            or not row["TARGET_NAME"]
            or not all(ACCESSION.fullmatch(token) for token in tokens)
        ):
            raise ConnectorError(
                "DrugCentral native drug/target identity is malformed."
            )
        out.append({"native_row_index": index, "fields": row, "accessions": tokens})
    return {"rows": out}


def map_target_relations(envelope):
    """Keep each matched observation on its original source target or target group.

    Native drug IDs are not merged by names. Activity values, units and relations
    remain raw, without assuming a logarithmic scale, physical units or potency.
    MOA, action and supporting-source declarations remain independent of generic
    binding/function, efficacy, indication and clinical interpretation.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "DrugCentral"
        or envelope.get("kind") != "target_relations"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"accession", "dataset"}
        or envelope["query"]["dataset"] != "drug_target_interactions"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("DrugCentral mapping requires a qualified native export.")
    identifier = accession(envelope["query"]["accession"])
    native = parse_export(envelope.get("record"))
    response_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    out = []
    for item in native["rows"]:
        if identifier not in item["accessions"]:
            continue
        row = item["fields"]
        index = item["native_row_index"]
        assertion = make_source_assertion(
            "relationships.drug_target.drugcentral",
            deepcopy(row),
            "DrugCentral",
            f"drug:{row['STRUCT_ID']}:target:{row['ACCESSION']}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"drugcentral:target:{row['ACCESSION']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "received_export_rows": len(native["rows"]),
            "query_accession": identifier,
            "native_target_accessions": deepcopy(item["accessions"]),
            "mapping_scope": {
                "identity": "exact_native_token; target_group_not_expanded; no_drug_or_protein_identity_merge",
                "activity": "native_value_unit_type_and_relation_literals; no_scale_or_potency_conversion",
                "interpretation": "native_MOA_action_and_support; no_generic_binding_or_clinical_inference",
                "revisions": "export_target_drug_and_sequence_revisions_not_stated",
                "coverage": "all_received_export_rows_validated; no_independent_database_total",
                "absence": "not_listed_is_not_no_interaction_or_no_drug",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        if "download_sha256" in envelope:
            assertion["source_metadata"]["download_sha256"] = envelope[
                "download_sha256"
            ]
        out.append(assertion)
    return out
