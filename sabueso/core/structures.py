"""Protein–structure relationships: coverage, derived classification and the card view.

Structures are not Cards in the MVP. A ProteinCard exposes them through a view over its
``has_structure`` Relationships (``devguide/archive/entity_resolver.md``, #6;
re-evaluation in #20). The coverage class is derived knowledge: it carries the rule and
thresholds that produced it and is never stored as a SourceAssertion.
"""

from __future__ import annotations

import re
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
#: Keys ``group_by`` accepts, beyond the state keys: ``ligands:interest`` reads the
#: ligand state coarsely (a ligand of interest, none, or unstated: ``no_ligands`` and
#: ``no_ligand_of_interest`` are both ``none_of_interest``), and ``substitutions`` groups
#: mutants by their substitutions, in the reference numbering when residue maps are given.
GROUP_KEYS = STATE_KEYS + ("ligands:interest", "substitutions")
_LIGANDS_OF_INTEREST = {
    "ligand_of_interest": "ligand_of_interest",
    "no_ligand_of_interest": "none_of_interest",
    "no_ligands": "none_of_interest",
    "unstated": "unstated",
}
_SUBSTITUTION = re.compile(r"^([A-Z])(\d+)([A-Z])$")


def _in_reference(
    labels: List[str] | None, mapping: Dict[int, int] | None
) -> List[Dict[str, Any]] | None:
    """Substitutions as ``{position, reference_position, residue, label}``; the reference
    position is None when the card has no map, or its map does not cover the position."""
    if labels is None:
        return None
    out = []
    for label in labels:
        match = _SUBSTITUTION.match(label)
        if not match:
            continue
        position = int(match.group(2))
        out.append(
            {
                "label": label,
                "position": position,
                "reference_position": None
                if mapping is None
                else mapping.get(position),
                "residue": match.group(3),
            }
        )
    return out


def structure_inventory(
    cards: Sequence[Any],
    regions: Any = None,
    include_fragments: bool = False,
    group_by: Sequence[str] | None = None,
    residue_maps: Dict[str, Dict[int, int]] | None = None,
    reference: str | None = None,
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
    ``{card_id: region}``, since numbering differs between proteins.

    ``group_by`` chooses the keys of a group, among ``GROUP_KEYS`` (default: every state
    key, ``STATE_KEYS``). ``residue_maps`` (``{card_id: {position: reference position}}``,
    e.g. from a MolSysMT alignment) places each card's substitutions in the numbering of
    the ``reference`` card, whose own positions need no map. Substitutions at one
    reference position with one residue, in several proteins, are then listed
    (``shared_substitutions``), and ``substitutions`` groups them together. Equal numbers
    in two proteins are never taken as equivalent positions: a card without a map keeps
    its own numbering, and its substitutions match no other card's.

    Choosing a structure stays with the reader; the inventory states facts and groups
    them by a named rule, whose parameters record the choices above.
    """
    from .relationship_store import make_derivation

    keys = tuple(group_by) if group_by else STATE_KEYS
    maps = {card_id: dict(m) for card_id, m in (residue_maps or {}).items()}
    if reference is not None:
        maps.setdefault(reference, None)  # identity: the reference numbering itself
    items: List[Dict[str, Any]] = []
    not_inventoried: Dict[str, List[Dict[str, str]]] = {}
    excluded: Dict[str, List[str]] = {}
    states: Dict[tuple, Dict[str, List[str]]] = {}
    substituted: Dict[tuple, Dict[str, set]] = {}
    ids = [card.id for card in cards]
    for card in cards:
        region = regions.get(card.id) if isinstance(regions, dict) else regions
        fetched = {
            f"pdb:{e['structure']}": e.get("status")
            for e in card.quality.get("enrichments") or []
            if e.get("source") == "RCSB PDB" and e.get("structure")
        }
        if card.id == reference:
            mapping = None
            in_frame = True
        else:
            mapping = maps.get(card.id)
            in_frame = mapping is not None
        view = structures_view(card, include_fragments=include_fragments, region=region)
        if view["excluded"]:
            excluded[card.id] = view["excluded"]
        for item in view["items"]:
            state = dict(item["state"])
            mapped = _in_reference(item.get("substitutions"), mapping)
            if card.id == reference and mapped is not None:
                for m in mapped:
                    m["reference_position"] = m["position"]
            row = {"card_id": card.id, **item, "substitutions_in_reference": mapped}
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
            state["ligands:interest"] = _LIGANDS_OF_INTEREST.get(state["ligands"])
            state["substitutions"] = tuple(
                sorted(
                    (m["reference_position"], m["residue"])
                    if in_frame and m["reference_position"] is not None
                    else (card.id, m["label"])
                    for m in mapped or []
                )
            )
            for m in mapped or []:
                if in_frame and m["reference_position"] is not None:
                    found = substituted.setdefault(
                        (m["reference_position"], m["residue"]), {}
                    )
                    found.setdefault(card.id, set()).add(item["structure_ref"])
            key = tuple(state[k] for k in keys)
            states.setdefault(key, {}).setdefault(card.id, []).append(
                item["structure_ref"]
            )

    def shown(key: str, value: Any) -> Any:
        if key != "substitutions":
            return value
        return [
            f"{pos}{res}" if isinstance(pos, int) else f"{res} ({pos})"
            for pos, res in value
        ]

    grouped = [
        {
            "state": {k: shown(k, v) for k, v in zip(keys, key)},
            "structures": {i: sorted(by_card.get(i, [])) for i in ids},
            "shared": all(by_card.get(i) for i in ids),
        }
        for key, by_card in states.items()
    ]
    grouped.sort(key=lambda g: (not g["shared"], [str(v) for v in g["state"].values()]))
    shared_substitutions = [
        {
            "reference_position": position,
            "residue": residue,
            "structures": {i: sorted(found[i]) for i in ids if i in found},
        }
        for (position, residue), found in sorted(substituted.items())
        if len(found) > 1
    ]
    parameters: Dict[str, Any] = {"state": list(keys), "state_rule": STATE_RULE}
    if residue_maps or reference:
        parameters["reference"] = reference
        parameters["mapped"] = sorted(c for c in maps if c != reference)
    return {
        "rule": make_derivation(
            INVENTORY_RULE, inputs=["has_structure"], parameters=parameters
        ),
        "items": items,
        "states": grouped,
        "shared_substitutions": shared_substitutions,
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
