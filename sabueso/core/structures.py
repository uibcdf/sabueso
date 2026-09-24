"""Protein–structure relationships: coverage, derived classification and the card view.

Structures are not Cards in the MVP. A ProteinCard exposes them through a view over its
``has_structure`` Relationships (``devguide/archive/entity_resolver.md``, #6;
re-evaluation in #20). The coverage class is derived knowledge: it carries the rule and
thresholds that produced it and is never stored as a SourceAssertion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .quantities import to_quantity

# Derived coverage classes. "domain" cannot be told from coverage alone (it needs domain
# annotations), so the MVP uses "partial" for intermediate coverage.
COVERAGE_CLASS_RULE = "structure_coverage_class@1"
COVERAGE_THRESHOLDS = {"full_length_min": 0.9, "partial_min": 0.3}


# Experimental-method vocabulary: RCSB spellings normalized to UniProt's, so the same
# method stated by both sources does not look like a disagreement. Unknown methods are
# kept verbatim (a real difference then stays visible as a qualifier conflict).
METHOD_ALIASES = {
    "X-RAY DIFFRACTION": "X-ray",
    "ELECTRON MICROSCOPY": "EM",
    "SOLUTION NMR": "NMR",
    "SOLID-STATE NMR": "NMR",
    "NEUTRON DIFFRACTION": "Neutron",
    "FIBER DIFFRACTION": "Fiber",
}


def normalize_methods(methods: Sequence[str]) -> str | None:
    """One method label, e.g. ['X-RAY DIFFRACTION'] -> 'X-ray'; hybrids joined by '+'."""
    labels = sorted({METHOD_ALIASES.get(m.upper(), m) for m in methods if m})
    return "+".join(labels) if labels else None


def merge_ranges(ranges: Sequence[Sequence[int]]) -> List[List[int]]:
    """Sorted, non-overlapping inclusive ranges."""
    merged: List[List[int]] = []
    for beg, end in sorted((int(b), int(e)) for b, e in ranges):
        if merged and beg <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([beg, end])
    return merged


def coverage(ranges: Sequence[Sequence[int]], length: int | None) -> float | None:
    """Fraction of a reference sequence of ``length`` residues covered by ``ranges``."""
    if not length or not ranges:
        return None
    covered = sum(end - beg + 1 for beg, end in merge_ranges(ranges))
    return round(min(covered / length, 1.0), 3)


def coverage_class(value: float | None) -> str | None:
    if value is None:
        return None
    if value >= COVERAGE_THRESHOLDS["full_length_min"]:
        return "full_length"
    if value >= COVERAGE_THRESHOLDS["partial_min"]:
        return "partial"
    return "fragment_or_peptide"


def coverage_derivation() -> Dict[str, Any]:
    from .relationship_store import make_derivation

    return make_derivation(
        COVERAGE_CLASS_RULE,
        inputs=["has_structure.coverage"],
        parameters=dict(COVERAGE_THRESHOLDS),
    )


def structures_view(card: Any, include_fragments: bool = False) -> Dict[str, Any]:
    """Protein-centric summary of the card's ``has_structure`` relationships.

    Returns ``{"items", "excluded", "classification"}``. Fragments and peptides are
    excluded by default, and the exclusion is reported, never silent.
    """
    items: List[Dict[str, Any]] = []
    excluded: List[str] = []
    for rel in card.relationships(predicate="has_structure"):
        q = rel.get("qualifiers", {})
        summary = {
            "structure_ref": rel["object_ref"],
            "relationship_id": rel["id"],
            "method": q.get("method"),
            "resolution": to_quantity(q["resolution"]) if q.get("resolution") else None,
            "chains": q.get("chains"),
            "ranges": q.get("ranges"),
            "coverage": q.get("coverage"),
            "coverage_class": coverage_class(q.get("coverage")),
            "other_entities": q.get("other_entities"),
            "ligands": q.get("ligands"),
            "sources": sorted(
                {
                    card.source_assertion_store.get(sa)["source"]["name"]
                    for sa in rel.get("source_assertion_ids", [])
                    if card.source_assertion_store.get(sa)
                }
            ),
            "qualifier_conflicts": rel.get("qualifier_conflicts"),
        }
        if summary["coverage_class"] == "fragment_or_peptide" and not include_fragments:
            excluded.append(rel["object_ref"])
            continue
        items.append(summary)
    items.sort(key=lambda s: s["structure_ref"])
    return {
        "items": items,
        "excluded": sorted(excluded),
        "classification": coverage_derivation(),
    }
