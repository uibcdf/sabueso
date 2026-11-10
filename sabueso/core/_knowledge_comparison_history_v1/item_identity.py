"""Original declared list identities; no source or resolver operations."""

from __future__ import annotations

from typing import Any, Callable, Dict, Tuple


def _positions(item: Dict[str, Any]) -> Tuple[int, ...]:
    sequence = (item.get("location") or {}).get("sequence") or {}
    spans = sequence.get("fragments") or [
        {"start": sequence.get("start"), "end": sequence.get("end")}
    ]
    return tuple(
        sorted(
            {
                p
                for s in spans
                if s.get("start") is not None
                for p in range(s["start"], (s.get("end") or s["start"]) + 1)
            }
        )
    )


CONTEXT_KEYS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "annotations.stage_expression": (
        ("stage", "observation"),
        ("host", "method", "level", "note"),
    ),
    "annotations.essentiality": (
        ("method", "phenotype"),
        ("stage", "host", "condition", "call", "note"),
    ),
    "annotations.accessibility": (
        ("compartment",),
        ("exposure", "stage", "host", "method", "note"),
    ),
    "annotations.metabolic_role": (
        ("pathway", "role"),
        ("stage", "host", "method", "note"),
    ),
}

CONTEXT_FIELDS = tuple(CONTEXT_KEYS)


def _context_key(*keys: str) -> Callable[[Any], Any]:
    return lambda i: tuple((i.get(k) or "").strip().casefold() for k in keys)


def _substitution(item: Dict[str, Any]) -> tuple:
    """A deletion (``missing``, #80) is its own substitution, never an unstated one."""
    s = item.get("substitution") or {}
    return (
        s.get("original"),
        tuple(s.get("alternatives") or []),
        bool(s.get("missing")),
    )


ITEM_IDENTITY: Dict[str, Callable[[Any], Any] | None] = {
    "features_positional.mutagenesis": lambda i: (_positions(i), _substitution(i)),
    "features_positional.natural_variant": lambda i: (_positions(i), _substitution(i)),
    "features_positional.binding_site": lambda i: (
        _positions(i),
        ((i.get("ligand") or {}).get("name") or "").lower(),
    ),
    "features_positional.active_site": _positions,
    "features_positional.disulfide_bond": _positions,
    "features_positional.glycosylation": _positions,
    "features_positional.modified_residue": _positions,
    "annotations.disease": lambda i: i.get("accession") or i.get("name", "").lower(),
    "annotations.catalytic_activity": lambda i: i.get("rhea_id") or i.get("reaction"),
    "annotations.subcellular_location": lambda i: (i.get("location") or "").lower(),
    # Biological context (#60): the same statement is the same condition (stage, host,
    # method...); a different observation there differs.
    "annotations.stage_expression": _context_key("stage", "host", "method"),
    "annotations.essentiality": _context_key("method", "stage", "host", "condition"),
    "annotations.accessibility": _context_key("compartment", "stage", "host"),
    "annotations.metabolic_role": _context_key("pathway", "stage", "host"),
    # A name a publication uses for the protein, e.g. a paralog's "TIM2" (#55). Resolving
    # by that name through a curation store anchors it to this entry.
    "names.synonyms": lambda i: (i.get("name") or "").strip().casefold(),
    # A typed free-text claim (#43): recorded and listed by topic, never compared.
    "literature.claims": None,
    "annotations.function": None,
    "annotations.pathway": None,
    "annotations.subunit": None,
    "annotations.ptm": None,
    "annotations.polymorphism": None,
    "annotations.tissue_specificity": None,
}
