"""Literal native TCDB accession-to-system occurrences, without role inference."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://tcdb.org/cgi-bin/projectv/public/acc2tcid.py"
ACCESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
TC_SYSTEM = re.compile(r"[1-9]\.[A-Z](?:\.[0-9]+){3,4}\Z")


def accession_literal(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier):
        raise ConnectorError(
            "TCDB requires one exact nonempty native accession literal."
        )
    return identifier


def response_query(identifier):
    return {"accession_literal": accession_literal(identifier), "export": "acc2tcid"}


def parse_assignments(text):
    """Validate every native headerless row, retaining blank accessions and case.

    The qualified export has two columns and five- or six-component TC codes.
    Thirteen observed rows omit the accession: retain these as unbound rows,
    never reconstruct a namespace, ID or relation from a neighbouring row.
    Empty HTTP/file bodies and arbitrary errors are not valid empty exports.
    """
    if not isinstance(text, str) or not text:
        raise ConnectorError("TCDB requires nonempty original native TSV text.")
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        fields = line.split("\t")
        if len(fields) != 2:
            raise ConnectorError(
                f"TCDB native column count is unsupported at line {number}."
            )
        identifier, tc_system = fields
        if identifier:
            accession_literal(identifier)
        if not TC_SYSTEM.fullmatch(tc_system):
            raise ConnectorError(
                f"TCDB native system literal is unsupported at line {number}."
            )
        rows.append({"line": number, "fields": fields, "raw_line": line})
    if not rows:
        raise ConnectorError("TCDB export contains no native rows.")
    return rows


def selected_rows(rows, identifier):
    identifier = accession_literal(identifier)
    return [r for r in rows if r["fields"][0] == identifier]


def map_assignments(envelope):
    """Retain each selected native assignment without taxonomy or function transfer."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "TCDB"
        or envelope.get("kind") != "accession_assignments"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "TCDB mapping requires a native full-export assignment envelope."
        )
    identifier = accession_literal(envelope["query"].get("accession_literal"))
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("TCDB mapping query scope is unsupported.")
    rows = parse_assignments(envelope.get("record"))
    export_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    unbound = sum(not r["fields"][0] for r in rows)
    assertions = []
    for row in selected_rows(rows, identifier):
        assertion = make_source_assertion(
            "annotations.transporter_classifications",
            {"accession_literal": row["fields"][0], "tc_system": row["fields"][1]},
            "TCDB",
            f"{identifier}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"tcdb:accession:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "export_hash": export_hash,
            "query": deepcopy(envelope["query"]),
            "received_export_count": len(rows),
            "received_unbound_count": unbound,
            "mapping_scope": {
                "identity": "exact_case_sensitive_accession_literal; namespace_unspecified; no_UniProt_RefSeq_or_protein_merge",
                "classification": "native_TC_system_literal; five_or_six_components_not_collapsed_or_expanded",
                "function": "no_substrate_mechanism_transporter_role_taxonomy_or_sequence_inferred",
                "support": "source_assignment_only; no_experimental_method_or_MOLI_Evidence_assigned",
                "unbound": "blank_accessions_retained_in_full_export; no_relation_or_identity_reconstruction",
                "revision": "export_assignment_and_sequence_revisions_not_stated; website_dates_are_separate",
                "coverage": "all_received_export_rows; no_native_total_or_current_database_completeness_claim",
                "terms": "export_grant_NOT_STATED; website_text_and_input_rights_are_separate",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
