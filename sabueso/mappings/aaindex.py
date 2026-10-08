"""Parse native AAindex1 records and retain amino-acid reference assertions.

AAindex defines the paired row order in its format documentation:
https://www.genome.jp/aaindex/aaindex_help.html
Units are not inferred from a description or from the July prototype's labels.
"""

from __future__ import annotations

import math
import re

from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(r"[A-Z]{4}[0-9]{6}\Z")
AMINO_ACIDS = frozenset("ARNDCQEGHILKMFPSTWYV")


def validate_identifier(identifier: str) -> None:
    """Refuse malformed native accessions before source access."""
    if not ACCESSION.fullmatch(identifier):
        raise ConnectorError(
            "AAindex1 identifiers have four uppercase letters and six digits."
        )


def parse_index(text: str, identifier: str) -> dict:
    """Read a complete native document before reporting presence or absence."""
    validate_identifier(identifier)
    if not text.rstrip().endswith("//"):
        raise ConnectorError("AAindex1 document has an unterminated record.")
    entries = []
    seen = set()
    for block in text.split("//"):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if not lines[0].startswith("H "):
            raise ConnectorError("The response is not an AAindex1 document.")
        native_id = lines[0][2:].strip()
        validate_identifier(native_id)
        if native_id in seen:
            raise ConnectorError(
                f"AAindex response repeats {native_id}; identity is ambiguous."
            )
        seen.add(native_id)
        fields, numbers, pairs = {}, [], []
        current = None
        for line in lines[1:]:
            if len(line) > 1 and line[1] == " " and not line[0].isspace():
                current = line[0]
                if current == "I":
                    pairs = line[2:].split()
                else:
                    fields[current] = line[2:].strip()
            elif current == "I":
                numbers.extend(line.split())
            elif current:
                fields[current] = (fields.get(current, "") + " " + line.strip()).strip()
        if len(pairs) != 10 or any(len(pair.split("/")) != 2 for pair in pairs):
            raise ConnectorError(
                f"AAindex {identifier} has an invalid amino-acid row header."
            )
        order = [pair.split("/")[row] for row in (0, 1) for pair in pairs]
        if len(numbers) != 20 or set(order) != AMINO_ACIDS:
            raise ConnectorError(
                f"AAindex {identifier} does not state exactly 20 amino-acid values."
            )
        values = {}
        for amino_acid, literal in zip(order, numbers):
            try:
                value = None if literal == "NA" else float(literal)
            except ValueError as error:
                raise ConnectorError(
                    f"AAindex {identifier} has an invalid numeric value."
                ) from error
            if value is not None and not math.isfinite(value):
                raise ConnectorError(f"AAindex {identifier} has a non-finite value.")
            values[amino_acid] = value
        entries.append(
            {
                "accession": native_id,
                "description": fields.get("D"),
                "references": fields.get("R", "").split(),
                "authors": fields.get("A"),
                "title": fields.get("T"),
                "journal": fields.get("J"),
                "native_fields": fields,
                "values": values,
                "native_values": dict(zip(order, numbers)),
                "unit_basis": "not_stated_in_structured_record",
            }
        )
    if not seen:
        raise ConnectorError("The response is not an AAindex1 document.")
    for entry in entries:
        if entry["accession"] == identifier:
            return entry
    raise RecordNotFoundError(
        f"AAindex1 does not list {identifier} in the consulted document."
    )


def map_index(envelope: dict) -> list[dict]:
    """Reference assertions about amino-acid types, separately from protein positions.

    A native index value is retained literally with its scale and unit gap. This
    mapping does not calculate a protein property or claim a positional prediction.
    """
    record = envelope["record"]
    assertions = []
    for amino_acid, literal in record["native_values"].items():
        assertion = make_source_assertion(
            "amino_acid.indices",
            {
                "amino_acid": amino_acid,
                "index_id": record["accession"],
                "description": record["description"],
                "native_value": literal,
                "unit_basis": record["unit_basis"],
            },
            "AAindex",
            record["accession"],
            envelope["retrieved_at"],
            subject_ref=f"amino_acid:{amino_acid}",
        )
        assertion["source"]["version"] = envelope.get("version")
        assertion["source_metadata"] = {
            key: record[key] for key in ("authors", "title", "journal", "references")
        }
        assertions.append(assertion)
    return assertions
