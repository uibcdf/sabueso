"""Native archived representative protein metadata, without residue projection."""

from __future__ import annotations

import hashlib
import math
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.quantities import quantity_node
from sabueso.core.source_assertion_store import make_source_assertion

RELEASE = "2024_12"
ARTIFACT = "human__2024_12__representative__proteins.dat"
URL = "https://interactome3d.irbbarcelona.org/data/previous_releases/2024_12/human/representative/proteins.dat"
COLUMNS = (
    "UNIPROT_AC",
    "RANK_MAJOR",
    "RANK_MINOR",
    "TYPE",
    "PDB_ID",
    "CHAIN",
    "SEQ_IDENT",
    "COVERAGE",
    "SEQ_BEGIN",
    "SEQ_END",
    "GA431",
    "MPQS",
    "ZDOPE",
    "FILENAME",
)
HEADER = "\t".join(COLUMNS)
ACCESSION = re.compile(r"[A-Z0-9]{6,10}(?:-[1-9][0-9]*)?\Z")
UNIT_BASIS = {
    "unit": "percent",
    "provider_fields": ["SEQ_IDENT", "COVERAGE"],
    "statement": "https://interactome3d.irbbarcelona.org/help.php",
    "reviewed": "2026-10-07",
    "qualification": "native_proteins_dat_column_descriptions_state_percentage",
    "qualification_page_sha256": "e65af6994408c1f72a37b9ee9b4d64e17fd3fd103c006582cc2654fcd8224061",
}


def response_query(identifier, release=RELEASE):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier):
        raise ConnectorError(
            "Interactome3D requires one exact uppercase accession literal."
        )
    if release != RELEASE:
        raise ConnectorError(
            "Only the qualified Interactome3D 2024_12 archive is supported."
        )
    return {
        "uniprot_ac": identifier,
        "release": release,
        "organism": "human",
        "set": "representative",
        "export": "proteins.dat",
    }


def parse_proteins(text):
    """Validate all 14-column rows; preserve blank chains and original literals."""
    if not isinstance(text, str) or not text:
        raise ConnectorError("Interactome3D requires nonempty native protein TSV text.")
    lines = text.splitlines()
    if not lines or lines[0] != HEADER:
        raise ConnectorError("Unsupported Interactome3D native protein header.")
    rows = []
    for number, line in enumerate(lines[1:], 2):
        fields = line.split("\t")
        if len(fields) != len(COLUMNS) or any(
            (index != 5 and not value.strip())
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            for index, value in enumerate(fields)
        ):
            raise ConnectorError(f"Unsupported Interactome3D row at line {number}.")
        response_query(fields[0])
        if fields[3] not in ("Structure", "Model") or not re.fullmatch(
            r"[1-9][A-Za-z0-9]{3}", fields[4]
        ):
            raise ConnectorError(
                "Unsupported Interactome3D type or native PDB literal."
            )
        if any(not re.fullmatch(r"[0-9]+", fields[i]) for i in (1, 2, 8, 9)):
            raise ConnectorError("Unsupported Interactome3D rank or sequence bounds.")
        if int(fields[8]) < 1 or int(fields[9]) < int(fields[8]):
            raise ConnectorError("Unsupported Interactome3D sequence endpoint order.")
        try:
            percentages = [float(fields[i]) for i in (6, 7)]
        except ValueError as error:
            raise ConnectorError("Unsupported Interactome3D percentage.") from error
        if not all(math.isfinite(v) and 0 <= v <= 100 for v in percentages):
            raise ConnectorError("Unsupported Interactome3D percentage range.")
        rows.append({"line": number, "fields": fields, "raw_line": line})
    return rows


def selected_rows(rows, identifier):
    response_query(identifier)
    return [row for row in rows if row["fields"][0] == identifier]


def map_protein_structures(envelope):
    """Keep each native source structure/model occurrence and its original support."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "Interactome3D"
        or envelope.get("kind") != "protein_structures"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("Interactome3D requires a full native protein envelope.")
    query = envelope["query"]
    if query != response_query(query.get("uniprot_ac"), query.get("release")):
        raise ConnectorError("Unsupported Interactome3D query/export scope.")
    rows = parse_proteins(envelope.get("record"))
    export_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    assertions = []
    for row in selected_rows(rows, query["uniprot_ac"]):
        native = dict(zip(COLUMNS, row["fields"], strict=True))
        value = {k: v for k, v in native.items() if k not in ("SEQ_IDENT", "COVERAGE")}
        value["sequence_identity"] = quantity_node(
            float(native["SEQ_IDENT"]), "percent"
        )
        value["coverage"] = quantity_node(float(native["COVERAGE"]), "percent")
        assertion = make_source_assertion(
            "annotations.structure_model_occurrences",
            value,
            "Interactome3D",
            f"{query['release']}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"interactome3d:protein:{query['uniprot_ac']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "export_hash": export_hash,
            "query": deepcopy(query),
            "received_export_count": len(rows),
            "percentage_unit_basis": deepcopy(UNIT_BASIS),
            "mapping_scope": {
                "identity": "exact_native_UNIPROT_AC_selector; no_similar_protein_or_structure_merge",
                "type": "native_Structure_or_Model_literal; template_PDB_not_model_experimental_method",
                "coordinates": "source_sequence_endpoints_only; not_exact_full_chain_correspondence_or_current_canonical_placement",
                "chains": "native_case_and_blank_or_whitespace_preserved; no_chain_repair",
                "scores": "GA431_MPQS_ZDOPE_original_literals_including_negative_sentinels; no_probability_quality_threshold_or_units_inferred",
                "coverage": "all_received_representative_protein_rows; complete_set_and_interaction_pair_export_unqueried; not_listed_not_biological_absence",
                "revision": "2024_12_selected_archive_route; native_export_PDB_and_sequence_revisions_not_stated",
                "access": "metadata_only; no_filename_or_coordinate_acquisition_modelling_alignment_or_card_intake",
                "terms": "data_grant_NOT_STATED; original_factual_artifact_local_unreleased; input_rights_separate",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
