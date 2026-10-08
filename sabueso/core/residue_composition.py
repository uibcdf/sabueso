"""Derived composition of an explicitly selected set on one source sequence axis."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from copy import deepcopy

from .errors import ArgumentError, SchemaError
from .residue_knowledge import _sequence, _support
from .residues import canonical_sequence, item_support

RULE = "residue_set_composition@1"
# Concrete sequence symbols, including genetically encoded U and O. Ambiguous
# B/J/X/Z are retained separately, without selecting a concrete amino-acid type.
CONCRETE = frozenset("ACDEFGHIKLMNPQRSTVWYOU")


def _axis(card, sequence_ref, supplied):
    canonical, canonical_id, node = canonical_sequence(card)
    subject = f"uniprot:{card.get('identifiers.uniprot')['value']}"
    if sequence_ref == "canonical":
        coverage = item_support(card, "sequence.primary", node, canonical)
        assertions = card.source_assertion_store.to_list()
        support = [
            _support(assertion, "card_store", index)
            for index, assertion in enumerate(assertions)
            if assertion["id"] in coverage["source_assertion_ids"]
        ]
        selected = {"id": canonical_id, "value": canonical}
        context = {
            "basis": "stored_canonical",
            **coverage,
            "support": support,
            "excluded_declarations": [],
        }
    else:
        candidates, excluded = [], []
        for origin, assertions in (
            ("card_store", card.source_assertion_store.to_list()),
            ("supplied", supplied or []),
        ):
            for index, assertion in enumerate(assertions):
                metadata = assertion.get("source_metadata")
                stated = (
                    metadata.get("sequence") if isinstance(metadata, dict) else None
                )
                if not isinstance(stated, dict) or stated.get("id") != sequence_ref:
                    continue
                support = _support(assertion, origin, index)
                if assertion["subject_ref"] != subject:
                    declared, reason = None, "SourceAssertion subject differs"
                else:
                    declared, reason = _sequence(assertion, subject)
                if declared is None:
                    excluded.append({"reason": reason, "support": support})
                else:
                    candidates.append((declared, support))
        if not candidates:
            raise SchemaError(
                "Selected sequence has no valid subject-bound source declaration."
            )
        if len({candidate[0]["value"] for candidate in candidates}) != 1:
            raise SchemaError(
                "Selected source sequence has contradictory declarations."
            )
        selected = candidates[0][0]
        context = {
            "basis": "source_sequence_declaration",
            "support_status": "incomplete" if excluded else "complete",
            "support": [support for _, support in candidates],
            "excluded_declarations": excluded,
        }
    sequence = selected["value"]
    if not re.fullmatch(r"[A-Z]+", sequence):
        raise SchemaError(
            "Composition requires a nonempty uppercase sequence alphabet."
        )
    return selected, context


def residue_composition(card, residues, sequence_ref, source_assertions):
    """Count unique requested positions, keeping unknown types in the denominator."""
    if not isinstance(residues, list) or any(
        not isinstance(position, int) or isinstance(position, bool) or position < 1
        for position in residues
    ):
        raise ArgumentError(
            argument="residues",
            value=residues,
            reason="expected a list of positive 1-based integer positions",
        )
    if not isinstance(sequence_ref, str) or not (
        sequence_ref == "canonical"
        or ":" in sequence_ref
        and all(sequence_ref.split(":", 1))
        and not any(c.isspace() for c in sequence_ref)
    ):
        raise ArgumentError(argument="sequence_ref", value=sequence_ref)
    if source_assertions is not None and (
        not isinstance(source_assertions, list)
        or any(not isinstance(assertion, dict) for assertion in source_assertions)
    ):
        raise ArgumentError(argument="source_assertions", value=source_assertions)
    selected, sequence_support = _axis(card, sequence_ref, source_assertions)
    sequence = selected["value"]
    if any(position > len(sequence) for position in residues):
        raise IndexError("Selected residue position exceeds source sequence length.")
    positions, duplicates, seen = [], [], set()
    for index, position in enumerate(residues):
        if position in seen:
            duplicates.append({"input_index": index, "position": position})
        else:
            seen.add(position)
            positions.append(position)
    positions.sort()
    members = [
        {
            "position": position,
            "amino_acid": sequence[position - 1],
            "type_status": "concrete"
            if sequence[position - 1] in CONCRETE
            else "ambiguous",
        }
        for position in positions
    ]
    counts = dict(
        sorted(
            Counter(
                m["amino_acid"] for m in members if m["type_status"] == "concrete"
            ).items()
        )
    )
    unresolved = dict(
        sorted(
            Counter(
                m["amino_acid"] for m in members if m["type_status"] == "ambiguous"
            ).items()
        )
    )
    total = len(positions)
    unresolved_count = sum(unresolved.values())
    return {
        "rule": RULE,
        "status": "empty"
        if not total
        else "partial"
        if unresolved_count or sequence_support["support_status"] != "complete"
        else "complete",
        "card_ref": card.pinned_ref() if card.id else None,
        "subject_ref": f"uniprot:{card.get('identifiers.uniprot')['value']}",
        "sequence_ref": selected["id"],
        "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
        "sequence_length": len(sequence),
        "indexing": "1-based",
        "sequence_support": sequence_support,
        "selection": {
            "basis": "caller_selected_sequence_positions; cavity_membership_not_established",
            "requested_positions": deepcopy(residues),
            "unique_positions": positions,
            "duplicate_occurrences": duplicates,
            "supplied_assertions_not_used": len(source_assertions or [])
            if sequence_ref == "canonical"
            else None,
        },
        "denominator": {
            "basis": "all_unique_selected_positions_including_ambiguous_types",
            "count": total,
        },
        "total": total,
        "concrete_count": total - unresolved_count,
        "unresolved_count": unresolved_count,
        "counts": counts,
        "unresolved_counts": unresolved,
        "fractions": {letter: count / total for letter, count in counts.items()},
        "unresolved_fraction": unresolved_count / total if total else None,
        "members": members,
    }
