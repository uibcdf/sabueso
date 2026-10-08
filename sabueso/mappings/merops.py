"""Native MEROPS accession classifications with unresolved rows kept explicit."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://ftp.ebi.ac.uk/pub/databases/merops/current_release/dnld_list.txt"
RULE = "merops_accession_rows@1"
ACCESSION = re.compile(r'(?:Trembl|swissprot|PIR):"?[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z')
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
FAMILY = re.compile(r"[A-Z][1-9][0-9]*[A-Z]?\Z")
TAXONOMY = re.compile(r" *[0-9]* *\Z")
PREFIXES = {"Trembl:", "swissprot:", "PIR:"}


def accession_literal(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier):
        raise ConnectorError(
            "MEROPS requires one exact native prefixed accession literal."
        )
    return identifier


def response_query(identifier):
    return {"accession_literal": accession_literal(identifier), "export": "dnld_list"}


def parse_assignments(text):
    """Retain all native lines; four-column rows have no assigned column semantics.

    The received export differs from its older format description. Its three
    displaced four-column rows are preserved, never joined, shifted or discarded.
    Taxonomy is a literal, including blanks/spaces, without namespace resolution.
    """
    if not isinstance(text, str) or not text:
        raise ConnectorError("MEROPS requires nonempty original native TSV text.")
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        fields = line.split("\t")
        if len(fields) == 3:
            accession_literal(fields[0])
            family, taxonomy = fields[1:]
        elif len(fields) == 4:
            if fields[0] not in PREFIXES or not TOKEN.fullmatch(fields[1]):
                raise ConnectorError(
                    f"Unsupported MEROPS four-column row at line {number}."
                )
            family, taxonomy = fields[2:]
        else:
            raise ConnectorError(f"Unsupported MEROPS column count at line {number}.")
        # Shape guards do not assign fields or biological identity to four-column rows.
        if not FAMILY.fullmatch(family) or not TAXONOMY.fullmatch(taxonomy):
            raise ConnectorError(f"Unsupported MEROPS field literal at line {number}.")
        rows.append({"line": number, "fields": fields, "raw_line": line})
    return rows


def representation_issues(rows):
    return [
        {
            "rule": RULE,
            "issue": "four_columns_unassigned"
            if len(row["fields"]) == 4
            else "quoted_accession_literal_unresolved",
            "native_row": deepcopy(row),
            "action": "retain_without_column_repair_or_identity_assignment",
        }
        for row in rows
        if len(row["fields"]) == 4 or ':"' in row["fields"][0]
    ]


def selected_rows(rows, identifier):
    identifier = accession_literal(identifier)
    return [r for r in rows if len(r["fields"]) == 3 and r["fields"][0] == identifier]


def map_assignments(envelope):
    """Assert qualified three-column occurrences; unresolved rows remain support.

    A family literal does not assert peptidase/inhibitor activity, role, substrate,
    mechanism or cleavage. Native prefixes are not rewritten into protein identity.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "MEROPS"
        or envelope.get("kind") != "accession_assignments"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "MEROPS requires a native full-export assignment envelope."
        )
    identifier = accession_literal(envelope["query"].get("accession_literal"))
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("MEROPS mapping query scope is unsupported.")
    rows = parse_assignments(envelope.get("record"))
    issues = representation_issues(rows)
    if envelope.get("representation_issues") != issues or envelope.get(
        "selection_complete"
    ) is not (not issues):
        raise ConnectorError(
            "MEROPS representation/selection qualifiers differ from native rows."
        )
    export_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for row in selected_rows(rows, identifier):
        assertion = make_source_assertion(
            "annotations.peptidase_inhibitor_classifications",
            dict(
                zip(
                    ("accession_literal", "family_literal", "taxonomy_literal"),
                    row["fields"],
                    strict=True,
                )
            ),
            "MEROPS",
            f"{identifier}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"merops:accession:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "export_hash": export_hash,
            "query": deepcopy(envelope["query"]),
            "received_export_count": len(rows),
            "representation_issues": deepcopy(issues),
            "selection_complete": not issues,
            "mapping_scope": {
                "identity": "exact_case_sensitive_native_prefixed_literal; no_namespace_rewrite_or_protein_merge",
                "classification": "native_family_and_taxonomy_literals; spaces_blanks_and_occurrences_retained",
                "function": "no_activity_role_substrate_mechanism_cleavage_sequence_or_MOLI_Evidence_inferred",
                "representation": "merops_accession_rows@1; four_columns_unassigned_and_quoted_literals_without_repair",
                "revision": "export_assignment_sequence_and_taxonomy_revisions_not_stated",
                "coverage": "all_received_rows_retained; unresolved_rows_preclude_complete_selection_claim",
                "terms": "GNU_Library_GPL_declared_version_unspecified; local_unreleased_use; sharing_obligations_unqualified",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
