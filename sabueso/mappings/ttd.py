"""Native TTD target listings, without accession inference or clinical conclusions."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import datetime

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

ARTIFACT = "P2-01-TTD_uniprot_all.txt"
URL = "https://ttd.idrblab.cn/files/download/" + ARTIFACT
FIELDS = ("TARGETID", "UNIPROID", "TARGNAME", "TARGTYPE")
INDEX = ("TTD Target ID", "Uniprot ID", "Target Name", "Target Type")


def response_query(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"T[0-9]{5}", identifier):
        raise ConnectorError(
            "TTD requires one exact native TTD target ID (T plus five digits)."
        )
    return {"target_id": identifier, "artifact": ARTIFACT}


def parse_targets(text):
    """Validate the original header and every four-field target block before selection."""
    if not isinstance(text, str) or not text:
        raise ConnectorError("TTD requires the original nonempty target listing text.")
    lines = text.splitlines()
    start = next((n for n, line in enumerate(lines) if line), None)
    if (
        start is None
        or lines[start : start + 2]
        != [
            "TTD - Therapeutic Targets Database Full Data Download File",
            "Title - Uniprot IDs for all TTD targets",
        ]
        or len(lines) <= start + 2
    ):
        raise ConnectorError("TTD native listing title is unsupported.")
    revision = re.fullmatch(
        r"Version ([0-9]+(?:\.[0-9]+)+) \(([0-9]{4}\.[0-9]{2}\.[0-9]{2})\)",
        lines[start + 2],
    )
    if revision is None:
        raise ConnectorError("TTD native release declaration is unsupported.")
    try:
        datetime.strptime(revision[2], "%Y.%m.%d")
        index = lines.index("Abbreviation Index:", start + 3)
    except ValueError as error:
        raise ConnectorError(
            "TTD release date or abbreviation index is invalid."
        ) from error
    if (
        lines[index + 1 : index + 5]
        != [f"{key}\t{label}" for key, label in zip(FIELDS, INDEX)]
        or len(lines) <= index + 5
        or not re.fullmatch(r"-{3,}", lines[index + 5])
    ):
        raise ConnectorError("TTD native field declarations are unsupported.")
    body_start = index + 6
    rows = []
    block = []

    def finish():
        if not block:
            return
        if len(block) != len(FIELDS):
            raise ConnectorError(
                "TTD target block is partial or contains additional fields."
            )
        fields = {}
        for (number, line), key in zip(block, FIELDS):
            parts = line.split("\t")
            if (
                len(parts) != 2
                or parts[0] != key
                or any(ord(c) < 32 or ord(c) == 127 for c in parts[1])
            ):
                raise ConnectorError(f"Unsupported TTD target field at line {number}.")
            fields[key] = parts[1]
        response_query(fields["TARGETID"])
        rows.append(
            {"line": block[0][0], "fields": fields, "raw_lines": [r[1] for r in block]}
        )
        block.clear()

    for number, line in enumerate(lines[body_start:], body_start + 1):
        if not line:
            finish()
        else:
            block.append((number, line))
    finish()
    return {
        "version": revision[1],
        "release_date_literal": revision[2],
        "native_header_lines": lines[:body_start],
        "rows": rows,
    }


def selected_rows(parsed, identifier):
    response_query(identifier)
    return [r for r in parsed["rows"] if r["fields"]["TARGETID"] == identifier]


def map_target_listing(envelope):
    """Retain source labels and cross-reference literals on an independent TTD subject."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "TTD"
        or envelope.get("kind") != "target_listing"
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "TTD mapping requires the qualified native listing envelope."
        )
    identifier = envelope["query"].get("target_id")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("Unsupported TTD listing query scope.")
    parsed = parse_targets(envelope.get("record"))
    if envelope.get("version") != parsed["version"]:
        raise ConnectorError("TTD envelope release differs from its native header.")
    export_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for row in selected_rows(parsed, identifier):
        assertion = make_source_assertion(
            "annotations.therapeutic_target_listing",
            deepcopy(row["fields"]),
            "TTD",
            f"{identifier}:{export_hash}:line:{row['line']}",
            envelope.get("retrieved_at"),
            subject_ref=f"ttd:target:{identifier}",
        )
        assertion["source"]["version"] = parsed["version"]
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "native_header_lines": parsed["native_header_lines"],
            "release_date_literal": parsed["release_date_literal"],
            "export_hash": export_hash,
            "query": deepcopy(envelope["query"]),
            "received_export_count": len(parsed["rows"]),
            "mapping_scope": {
                "identity": "native_TTD_target_ID; UNIPROID_is_a_literal_including_entry_names_and_NOUNIPROTAC; no_accession_gene_protein_or_complex_merge",
                "classification": "native_TARGTYPE_literal; no_Sabueso_druggability_or_clinical_finding",
                "support": "independent_occurrence; original_labels_inconsistencies_and_blanks_retained",
                "revision": "native_export_header_release; individual_target_and_UniProt_revisions_unknown",
                "coverage": "all_received_export_rows; no_current_database_completeness_or_biological_absence_claim",
                "terms": "NOT_STATED; automated_use_and_sharing_unknown; original_factual_export_local_unreleased",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
