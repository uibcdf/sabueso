"""Literal ProBiS reference-chain catalog occurrences, without similarity transfer."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

ARTIFACT = "nrpdb-2015-07-31.txt"
URL = "http://probis.cmm.ki.si/download/" + ARTIFACT
CHAIN = re.compile(r"[1-9][a-z0-9]{3}\.[A-Za-z0-9]\Z")


def response_query(identifier):
    if not isinstance(identifier, str) or not CHAIN.fullmatch(identifier):
        raise ConnectorError(
            "ProBiS catalog requires one exact lowercase PDB.case-sensitive-chain literal."
        )
    return {"chain_literal": identifier, "artifact": ARTIFACT}


def parse_chain_catalog(text):
    """Validate every headerless five-column row before literal selection.

    Column 3/4 supply the source PDB/chain selector. Columns 1, 2 and 5 are
    retained without assigning undocumented index, cluster, weight or score roles.
    Native padding, gaps in column 1 and repeated chains are not repaired.
    """
    if not isinstance(text, str) or not text:
        raise ConnectorError(
            "ProBiS requires nonempty original chain-catalog TSV text."
        )
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        fields = line.split("\t")
        if len(fields) != 5 or any(
            not x.strip() or any(ord(c) < 32 or ord(c) == 127 for c in x)
            for x in fields
        ):
            raise ConnectorError(f"Unsupported ProBiS catalog row at line {number}.")
        response_query(fields[2] + "." + fields[3])
        rows.append({"line": number, "fields": fields, "raw_line": line})
    if not rows:
        raise ConnectorError("ProBiS catalog contains no native rows.")
    return rows


def selected_rows(rows, identifier):
    response_query(identifier)
    return [r for r in rows if r["fields"][2] + "." + r["fields"][3] == identifier]


def map_chain_catalog(envelope):
    """Keep independent listing occurrences, not representative-query relations."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "ProBiS-Database"
        or envelope.get("kind") != "reference_chain_catalog"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "ProBiS mapping requires a full native reference-chain envelope."
        )
    identifier = envelope["query"].get("chain_literal")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("Unsupported ProBiS catalog mapping scope.")
    rows = parse_chain_catalog(envelope.get("record"))
    export_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    assertions = []
    for row in selected_rows(rows, identifier):
        fields = row["fields"]
        assertion = make_source_assertion(
            "annotations.reference_chain_listing",
            {
                "column_1_literal": fields[0],
                "column_2_literal": fields[1],
                "native_pdb_literal": fields[2],
                "native_chain_literal": fields[3],
                "column_5_literal": fields[4],
            },
            "ProBiS-Database",
            f"{identifier}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"probis:catalog_chain:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "export_hash": export_hash,
            "query": deepcopy(envelope["query"]),
            "received_export_count": len(rows),
            "mapping_scope": {
                "identity": "literal_PDB_chain_catalog_selector; case_preserved; no_protein_or_similar_chain_merge",
                "columns": "five_native_columns; PDB_and_chain_literal_shapes_in_columns_3_4; columns_1_2_5_semantics_unqualified",
                "membership": "listed_in_this_received_nrPDB_artifact; no_query_to_representative_relation_or_working_API_claim",
                "duplicates": "every_native_occurrence_retained; no_deduplication_or_column_1_identity_assignment",
                "scores": "opaque_original_columns; no_cluster_size_weight_probability_Z_score_units_or_function_inferred",
                "revision": "dated_filename_is_an_artifact_label; dataset_PDB_and_sequence_revisions_not_stated",
                "coverage": "all_received_rows_validated; no_current_source_completeness_or_biological_absence_claim",
                "terms": "data_grant_NOT_STATED; native_artifact_local_unreleased; article_software_and_input_rights_separate",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
