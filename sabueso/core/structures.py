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


STATE_RULE = "structure_state@1"


def state_derivation() -> Dict[str, Any]:
    from .relationship_store import make_derivation

    return make_derivation(
        STATE_RULE,
        inputs=[
            "has_structure.mutations",
            "has_structure.sequence_differences",
            "has_structure.chimeric_with",
            "has_structure.ligands",
            "has_structure.assemblies",
            "has_structure.other_entities",
            "has_structure.observed",
        ],
        parameters={
            "sequence": {
                "mutant": "RCSB states an engineered mutation",
                "chimera": "the entities also map to other proteins",
                "differs": "aligned residues differ from the reference sequence, "
                "none stated as engineered (a variant, a conflict or unannotated)",
                "reference": "no difference and no engineered mutation",
            },
            "ligands": "PDB subject-of-investigation flag",
            "oligomer": "RCSB global symmetry of the first assembly",
            "unknown": "None: the structure was not fetched from RCSB with these data",
        },
    )


def _sequence_state(q: Dict[str, Any]) -> tuple:
    """(state, substitutions, modified residues) of a has_structure relationship."""
    if "mutations" not in q:
        return None, None, None
    mutations = q.get("mutations") or []
    differences = q.get("sequence_differences")
    stated = [
        m
        for m in mutations
        if m.get("reference") and m.get("residue") and m["reference"] != m["residue"]
    ]
    changed = differences if differences is not None else stated
    substitutions = sorted(
        {f"{d['reference']}{d['position']}{d['residue']}" for d in changed},
        key=lambda label: int("".join(c for c in label if c.isdigit()) or 0),
    )
    modified = sorted(
        {
            f"{m['reference']}{m['position']}"
            for m in mutations
            if m.get("name") != "engineered mutation"
            and m.get("reference")
            and m.get("reference") == m.get("residue")
        }
    )
    if q.get("chimeric_with"):
        state = "chimera"
    elif any(m.get("name") == "engineered mutation" for m in mutations):
        state = "mutant"
    elif substitutions:
        state = "differs"
    elif differences is None:
        state = None  # no reference sequence to compare with
    else:
        state = "reference"
    return state, substitutions, modified


def _ligand_state(ligands: List[Dict[str, Any]] | None) -> str | None:
    if ligands is None:
        return None
    if not ligands:
        return "no_ligands"
    flags = [lig.get("subject_of_investigation") for lig in ligands]
    if any(flag is True for flag in flags):
        return "ligand_of_interest"
    if all(flag is False for flag in flags):
        return "no_ligand_of_interest"
    return "unstated"


def _missing(
    q: Dict[str, Any], region: Sequence[int] | None
) -> Dict[str, List[int]] | None:
    """Per chain, the region's positions without coordinates in that chain."""
    observed = q.get("observed")
    if region is None or observed is None:
        return None
    out = {}
    for chain, ranges in sorted(observed.items()):
        have = {p for beg, end in ranges for p in range(beg, end + 1)}
        out[chain] = [p for p in region if p not in have]
    return out


def structures_view(
    card: Any, include_fragments: bool = False, region: Sequence[int] | None = None
) -> Dict[str, Any]:
    """Protein-centric summary of the card's ``has_structure`` relationships.

    Returns ``{"items", "excluded", "classification", "state_rule"}``. Fragments and
    peptides are excluded by default, and the exclusion is reported, never silent.
    ``region`` (UniProt positions) adds, per chain, the region's residues without
    coordinates (``missing_in_region``) and the chains that have them all
    (``complete_chains``).
    """
    items: List[Dict[str, Any]] = []
    excluded: List[str] = []
    for rel in card.relationships(predicate="has_structure"):
        q = rel.get("qualifiers", {})
        sequence_state, substitutions, modified = _sequence_state(q)
        assemblies = q.get("assemblies")
        refinement = [r for r in q.get("refinement") or [] if r.get("r_free")]
        missing = _missing(q, region)
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
            "released": q.get("released"),
            "r_free": refinement[0]["r_free"] if refinement else None,
            "substitutions": substitutions,
            "modified_residues": modified,
            "ligands_of_interest": None
            if q.get("ligands") is None
            else sorted(
                {
                    lig["comp_id"]
                    for lig in q["ligands"]
                    if lig.get("subject_of_investigation") and lig.get("comp_id")
                }
            ),
            "expression_host": None
            if q.get("construct") is None
            else sorted(
                {
                    h["name"]
                    for c in q["construct"]
                    for h in c.get("expression_host") or []
                    if h.get("name")
                }
            ),
            "observed": q.get("observed"),
            "missing_in_region": missing,
            "complete_chains": None
            if missing is None
            else sorted(chain for chain, gaps in missing.items() if not gaps),
            "state": {
                "method": q.get("method"),
                "coverage": coverage_class(q.get("coverage")),
                "sequence": sequence_state,
                "ligands": _ligand_state(q.get("ligands")),
                "oligomer": assemblies[0].get("oligomeric_state")
                if assemblies
                else None,
                "in_complex": bool(q["other_entities"])
                if "other_entities" in q
                else None,
            },
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
        "state_rule": state_derivation(),
    }


INVENTORY_RULE = "structure_inventory@1"
STATE_KEYS = ("method", "coverage", "sequence", "ligands", "oligomer", "in_complex")


def structure_inventory(
    cards: Sequence[Any],
    regions: Any = None,
    include_fragments: bool = False,
) -> Dict[str, Any]:
    """The experimental structures of several proteins, side by side, grouped by state.

    Each protein's structures are summarised as in ``Card.structures()``. Structures
    in the same state (coverage class, sequence, ligands, oligomer, complex) are listed
    together, one list per protein, so that like can be compared with like. A state
    shared by every protein is marked ``shared``. Structures whose state is unknown,
    because they were not fetched from RCSB with the data a state needs, are listed
    apart (``not_inventoried``) with the reason: ``not_requested`` (build the card with
    ``structures="all"``), ``not_found`` or ``error`` (RCSB did not answer), or
    ``fetched_without_state`` (a card built before schema 0.3.4: refresh it).

    ``regions`` is one region (UniProt positions and ranges) for every card, or
    ``{card_id: region}``, since numbering differs between proteins. Choosing a
    structure stays with the reader; the inventory states facts and groups them by a
    named rule.
    """
    from .relationship_store import make_derivation

    items: List[Dict[str, Any]] = []
    not_inventoried: Dict[str, List[Dict[str, str]]] = {}
    excluded: Dict[str, List[str]] = {}
    states: Dict[tuple, Dict[str, List[str]]] = {}
    ids = [card.id for card in cards]
    for card in cards:
        region = regions.get(card.id) if isinstance(regions, dict) else regions
        fetched = {
            f"pdb:{e['structure']}": e.get("status")
            for e in card.quality.get("enrichments") or []
            if e.get("source") == "RCSB PDB" and e.get("structure")
        }
        view = structures_view(card, include_fragments=include_fragments, region=region)
        if view["excluded"]:
            excluded[card.id] = view["excluded"]
        for item in view["items"]:
            state = item["state"]
            row = {"card_id": card.id, **item}
            items.append(row)
            if state["sequence"] is None:
                status = fetched.get(item["structure_ref"])
                reason = {None: "not_requested", "added": "fetched_without_state"}.get(
                    status, status
                )
                not_inventoried.setdefault(card.id, []).append(
                    {"structure_ref": item["structure_ref"], "reason": reason}
                )
                continue
            key = tuple(state[k] for k in STATE_KEYS)
            states.setdefault(key, {}).setdefault(card.id, []).append(
                item["structure_ref"]
            )
    grouped = [
        {
            "state": dict(zip(STATE_KEYS, key)),
            "structures": {i: sorted(by_card.get(i, [])) for i in ids},
            "shared": all(by_card.get(i) for i in ids),
        }
        for key, by_card in states.items()
    ]
    grouped.sort(key=lambda g: (not g["shared"], [str(v) for v in g["state"].values()]))
    return {
        "rule": make_derivation(
            INVENTORY_RULE,
            inputs=["has_structure"],
            parameters={"state": list(STATE_KEYS), "state_rule": STATE_RULE},
        ),
        "items": items,
        "states": grouped,
        "not_inventoried": not_inventoried,
        "excluded": excluded,
    }


def predicted_structures_view(card: Any) -> Dict[str, Any]:
    """The card's predicted models (``has_predicted_structure``, #57), never mixed with
    experimental structures.

    Each item: the model reference, version and tool, the mean pLDDT and its bands, the
    UniProt range it covers and its coverage of the sequence, and whether the modelled
    sequence is the entry's current one. A model of an isoform names it (``isoform``) and
    has no coverage of the entry.
    """
    length = (card.get("sequence.length") or {}).get("value")
    items = []
    for rel in card.relationships(predicate="has_predicted_structure"):
        q = rel.get("qualifiers") or {}
        start, end = (list(q.get("range") or []) + [None, None])[:2]
        items.append(
            {
                "model_ref": rel["object_ref"],
                "model_version": q.get("model_version"),
                "tool": q.get("tool"),
                "mean_plddt": q.get("mean_plddt"),
                "plddt_fractions": q.get("plddt_fractions"),
                "range": q.get("range"),
                "isoform": q.get("isoform"),
                "coverage": round((end - start + 1) / length, 3)
                if length and start and end and not q.get("isoform")
                else None,
                "sequence_matches": q.get("sequence_matches"),
            }
        )
    return {"items": sorted(items, key=lambda i: i["model_ref"])}
