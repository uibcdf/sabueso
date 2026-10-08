"""Read source-stated linear annotations at a canonical protein position.

Recovered from the July prototype, with exact item support and explicit sequence
scope. This view neither aligns sequences nor projects onto structure numbering.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import SchemaError
from .source_assertion_store import assertion_value

RULE = "residue_annotations@1"


def field_nodes(sections: dict, prefix: str = ""):
    """Walk actual field nodes, without treating nested source values as fields."""
    for key, node in sections.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(node, dict):
            if "value" in node and "source_assertion_ids" in node:
                yield path, node
            else:
                yield from field_nodes(node, path)


def item_support(card, path: str, node: dict, item: Any) -> dict:
    """Return only assertions that actually support this selected item."""
    supported, missing, incompatible = [], [], []
    accession = (card.get("identifiers.uniprot") or {}).get("value")
    subject = f"uniprot:{accession}" if accession else None
    for identifier in node.get("source_assertion_ids") or []:
        assertion = card.source_assertion_store.get(identifier)
        if assertion is None:
            missing.append(identifier)
        elif subject is None or assertion.get("subject_ref") != subject:
            incompatible.append(identifier)
        elif assertion.get("field_path") == path:
            value = assertion_value(assertion)
            if value == item or isinstance(value, list) and item in value:
                supported.append(identifier)
    return {
        "source_assertion_ids": supported,
        "missing_source_assertion_ids": missing,
        "incompatible_source_assertion_ids": incompatible,
        "support_status": (
            "complete"
            if supported and not missing and not incompatible
            else "incomplete"
        ),
    }


def canonical_sequence(card):
    if card.meta.get("entity_type") != "protein":
        raise SchemaError("A residue view requires a protein card.")
    node = card.get("sequence.primary") or {}
    sequence = node.get("value")
    if not isinstance(sequence, str) or not sequence:
        raise SchemaError("The canonical sequence is not stored on this card.")
    accession = (card.get("identifiers.uniprot") or {}).get("value")
    if not isinstance(accession, str) or not accession:
        raise SchemaError("The canonical sequence has no stored UniProt identity.")
    return sequence, f"UniProt:{accession}", node


def _prepare(card):
    sequence, sequence_id, sequence_node = canonical_sequence(card)
    sequence_versions = {
        assertion.get("source_metadata", {}).get("sequence_version")
        for identifier in sequence_node.get("source_assertion_ids") or []
        if (assertion := card.source_assertion_store.get(identifier)) is not None
        and assertion.get("subject_ref") == "uniprot:" + sequence_id.split(":", 1)[1]
        and assertion.get("source", {}).get("name") == "UniProt"
        and assertion.get("field_path") == "sequence.primary"
        and assertion_value(assertion) == sequence
        and assertion.get("source_metadata", {}).get("sequence_version") is not None
    }
    annotations, unmapped = [], []
    for path, node in field_nodes(card.sections):
        if not path.startswith("features_positional."):
            continue
        for index, item in enumerate(node.get("value") or []):
            if not isinstance(item, dict):
                continue
            location = item.get("location") or {}
            coordinates = location.get("sequence") or {}
            reference = {"field_path": path, "index": index}
            if location.get("kind") != "sequence":
                continue
            stated_id = coordinates.get("sequence_id")
            begin, end = coordinates.get("start"), coordinates.get("end")
            if not stated_id or not isinstance(stated_id, str):
                unmapped.append({**reference, "reason": "sequence identity not stated"})
                continue
            if stated_id.casefold() != sequence_id.casefold():
                continue
            support = item_support(card, path, node, item)
            feature_versions = {
                assertion.get("source_metadata", {}).get("sequence_version")
                for identifier in support["source_assertion_ids"]
                if (assertion := card.source_assertion_store.get(identifier))
                is not None
                and assertion.get("source", {}).get("name") == "UniProt"
                and assertion.get("source_metadata", {}).get("sequence_version")
                is not None
            }
            if (
                feature_versions
                and sequence_versions
                and feature_versions != sequence_versions
            ):
                unmapped.append(
                    {**reference, "reason": "source sequence version differs"}
                )
                continue
            if (
                coordinates.get("indexing") != "1-based"
                or any(
                    coordinates.get(f"{endpoint}_modifier") not in (None, "EXACT")
                    for endpoint in ("start", "end")
                )
                or any(
                    isinstance(n, bool) or not isinstance(n, int) for n in (begin, end)
                )
                or not 1 <= begin <= end <= len(sequence)
            ):
                unmapped.append(
                    {**reference, "reason": "location not an exact valid range"}
                )
                continue
            annotations.append(
                (
                    begin,
                    end,
                    path == "features_positional.disulfide_bond",
                    {
                        **reference,
                        "annotation": deepcopy(item),
                        **support,
                    },
                )
            )
    return (
        sequence,
        sequence_id,
        card.pinned_ref() if card.id else None,
        item_support(card, "sequence.primary", sequence_node, sequence),
        annotations,
        unmapped,
    )


def residue_view(card, position: int, prepared=None) -> dict:
    primary, sequence_id, card_ref, support, records, unmapped = prepared or _prepare(
        card
    )
    if position > len(primary):
        raise IndexError(
            f"Residue position {position} exceeds sequence length {len(primary)}"
        )
    return {
        "rule": RULE,
        "card_ref": card_ref,
        "sequence_id": sequence_id,
        "position": position,
        "indexing": "1-based",
        "amino_acid": primary[position - 1],
        "sequence_support": deepcopy(support),
        "annotations": [
            deepcopy(record)
            for begin, end, endpoints, record in records
            if (position in (begin, end) if endpoints else begin <= position <= end)
        ],
        "unmapped": deepcopy(unmapped),
    }


def residues_view(card) -> list:
    prepared = _prepare(card)
    return [
        residue_view(card, position, prepared)
        for position in range(1, len(prepared[0]) + 1)
    ]
