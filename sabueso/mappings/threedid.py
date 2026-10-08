"""Native 3did domain-motif structural instances and literal source axes."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://3did.irbbarcelona.org/download/current/3did_dmi_flat.gz"
PDB = re.compile(r"[1-9][a-z0-9]{3}\Z")
RANGE = re.compile(r"[^:\s]+:[+-]?[0-9]+[A-Za-z]?-[+-]?[0-9]+[A-Za-z]?\Z")


def response_query(identifier):
    if not isinstance(identifier, str) or not PDB.fullmatch(identifier):
        raise ConnectorError("3did requires one exact lowercase four-character PDB ID.")
    return {"pdb_id": identifier, "export": "3did_dmi_flat"}


def parse_motif_interactions(text):
    """Validate the complete ID/PT/3D/end grammar without interpreting patterns.

    PDB bounds remain literals, including chain case, insertions, gaps or negative
    numbers. Motif sequence length is not substituted for the PDB-number span.
    Patterns/dates, count and topology declarations stay source text.
    """
    if not isinstance(text, str) or not text:
        raise ConnectorError("3did requires nonempty original domain-motif flat text.")
    blocks, block = [], None
    for number, line in enumerate(text.splitlines(), 1):
        fields = line.split("\t")
        if any(not x or any(ord(c) < 32 or ord(c) == 127 for c in x) for x in fields):
            raise ConnectorError(f"Invalid 3did literal at line {number}.")
        native = {"line": number, "fields": fields, "raw_line": line}
        if fields[0] == "#=ID":
            if block is not None or len(fields) != 5:
                raise ConnectorError(f"Invalid 3did block start at line {number}.")
            block = {"id": native, "pattern": None, "instances": []}
        elif fields[0] == "#=PT":
            if (
                block is None
                or block["pattern"] is not None
                or len(fields) != 2
                or block["instances"]
            ):
                raise ConnectorError(f"Invalid 3did pattern order at line {number}.")
            block["pattern"] = native
        elif fields[0] == "#=3D":
            if (
                block is None
                or block["pattern"] is None
                or len(fields) != 7
                or not PDB.fullmatch(fields[1])
                or not RANGE.fullmatch(fields[2])
                or not RANGE.fullmatch(fields[3])
                or not re.fullmatch(r"[A-Z]+", fields[4])
                or not re.fullmatch(r"[0-9]+", fields[5])
                or not re.fullmatch(r"[0-9]+", fields[6])
            ):
                raise ConnectorError(f"Invalid 3did structural row at line {number}.")
            block["instances"].append(native)
        elif line == "//":
            if block is None or block["pattern"] is None or not block["instances"]:
                raise ConnectorError(f"Invalid 3did block end at line {number}.")
            block["end_line"] = number
            blocks.append(block)
            block = None
        else:
            raise ConnectorError(f"Unsupported 3did flat line {number}.")
    if block is not None or not blocks:
        raise ConnectorError("3did export is empty or has an unterminated block.")
    return blocks


def selected_instances(blocks, identifier):
    response_query(identifier)
    return [
        (block, row)
        for block in blocks
        for row in block["instances"]
        if row["fields"][1] == identifier
    ]


def map_motif_interactions(envelope):
    """Keep every declared domain-motif occurrence without protein projection."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "3did"
        or envelope.get("kind") != "domain_motif_interactions"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("3did requires a full native domain-motif envelope.")
    identifier = envelope["query"].get("pdb_id")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("3did mapping query scope is unsupported.")
    blocks = parse_motif_interactions(envelope.get("record"))
    export_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    count = sum(len(b["instances"]) for b in blocks)
    assertions = []
    for block, row in selected_instances(blocks, identifier):
        parent = block["id"]["fields"]
        fields = row["fields"]
        assertion = make_source_assertion(
            "annotations.domain_motif_interactions",
            {
                "domain_name": parent[1],
                "domain_source_literal": parent[2],
                "motif_name": parent[3],
                "motif_source_literal": parent[4],
                "pattern_literal": block["pattern"]["fields"][1],
                "pdb_id": fields[1],
                "domain_range_literal": fields[2],
                "motif_range_literal": fields[3],
                "motif_sequence_literal": fields[4],
                "contextual_contacts_literal": fields[5],
                "topology_literal": fields[6],
            },
            "3did",
            f"{identifier}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"3did:structure:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "native_id": deepcopy(block["id"]),
            "native_pattern": deepcopy(block["pattern"]),
            "native_end_line": block["end_line"],
            "export_hash": export_hash,
            "query": deepcopy(envelope["query"]),
            "received_pair_count": len(blocks),
            "received_instance_count": count,
            "mapping_scope": {
                "identity": "exact_native_PDB_literal; source_domain_motif_and_chain_literals; no_protein_merge",
                "coordinates": "original_PDB_numbering; no_sequence_span_arithmetic_or_canonical_projection",
                "chain": "native_case_and_repeated_lowercase_tokens_unchanged; no_SQL_encoding_repair",
                "pattern": "opaque_source_pattern_and_date; no_regex_execution_motif_search_or_new_prediction",
                "counts": "contextual_contact_and_topology_literals; zero_retained; no_binding_strength_or_probability",
                "revision": "mutable_current_export; scientific_PDB_Pfam_sequence_and_pattern_revisions_unqualified",
                "support": "native_structural_instance_declaration; no_contact_atom_method_function_or_MOLI_Evidence_inferred",
                "coverage": "all_received_blocks_validated; no_native_total_or_current_database_completeness_claim",
                "terms": "separate_export_grant_NOT_STATED; provider_and_input_attribution; local_unreleased",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
