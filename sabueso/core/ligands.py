"""A protein card crossed with a deck of SmallMoleculeCards (uibcdf/sabueso#23, #25).

A ProteinCard refers to molecules by source record: ChEMBL molecules in its
``has_bioactivity`` relationships and PDB chemical components among the ligands of its
``has_structure`` relationships. A SmallMoleculeCard lists the records of one molecule as
``same_as`` links to its InChIKey anchor. Crossing both tells, per molecule, what was
measured on the protein and in which structures it was observed.

These views only bring together what the cards already hold. Activity classes are the
derived ones of ``Card.bioactivities()`` (rule ``bioactivity_class@3``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from .bioactivities import CLASS_ORDER
from .labels import molecule_label
from .relationship_store import make_derivation

COUNTING_RULE = "ligand_measurement_count@2"


def _records(molecule_card: Any) -> Set[str]:
    anchor = (molecule_card.id or "").split(":", 2)[-1]
    return {
        rel["subject_ref"]
        for rel in molecule_card.relationships("same_as")
        if rel["object_ref"] == anchor
    }


def _structure_ligands(card: Any) -> Dict[str, Dict[str, bool | None]]:
    """``pdb.ligand:<code>`` -> {structure: subject of investigation (True/False/None)}."""
    out: Dict[str, Dict[str, bool | None]] = {}
    for rel in card.relationships("has_structure"):
        for ligand in rel.get("qualifiers", {}).get("ligands") or []:
            if ligand.get("comp_id"):
                flags = out.setdefault(f"pdb.ligand:{ligand['comp_id']}", {})
                flag = ligand.get("subject_of_investigation")
                flags[rel["object_ref"]] = flags.get(rel["object_ref"]) or flag
    return out


def _rank(entry: Dict[str, Any]) -> tuple:
    bio = entry["bioactivity"]
    return (
        CLASS_ORDER.index(bio["class"]) if bio else len(CLASS_ORDER),
        -((bio or {}).get("best_pchembl") or 0.0),
        entry["molecule_ref"],
    )


def ligands_view(
    card: Any,
    deck: Any,
    include_indirect: bool = False,
    thresholds: Dict[str, Any] | None = None,
    *,
    counting_rule: str = COUNTING_RULE,
    _support=None,
) -> Dict[str, Any]:
    """Per molecule of ``deck``: its bioactivity on ``card`` and its structures.

    Returns items, unmatched records, scope, classification and measurement counting.
    ``ligand_measurement_count@2`` counts distinct included measurement groups across
    matched molecule records. ``@1`` reproduces the legacy source-record counter.
    ``bioactivity.records`` always counts distinct included source relationships.
    Each item lists the structures where the molecule is observed and, among them,
    those where the PDB
    declares it subject of investigation. ``unmatched`` lists the molecule records of the
    protein card that no card of the deck covers.
    """
    if counting_rule not in {"ligand_measurement_count@1", COUNTING_RULE}:
        raise ValueError(f"Unknown ligand counting rule: {counting_rule!r}")
    bio = card.bioactivities(include_indirect=include_indirect, thresholds=thresholds)
    by_molecule = {item["molecule_ref"]: item for item in bio["items"]}
    excluded: Dict[str, int] = {}
    for x in bio["excluded"]:
        excluded[x["molecule_ref"]] = excluded.get(x["molecule_ref"], 0) + 1
    in_structures = _structure_ligands(card)
    sites = {}
    if card.relationships("has_ligand_site"):
        from .ligand_sites import ligand_sites_view

        sites = {i["ligand_ref"]: i for i in ligand_sites_view(card)["items"]}

    items: List[Dict[str, Any]] = []
    covered: Set[str] = set()
    decisions = []
    for index, molecule_card in enumerate(deck.cards):
        records = _records(molecule_card)
        measured = [by_molecule[r] for r in sorted(records) if r in by_molecule]
        seen = {s: f for r in records for s, f in in_structures.get(r, {}).items()}
        structures = sorted(seen)
        n_excluded = sum(excluded.get(r, 0) for r in records)
        own_sites = [sites[r] for r in sorted(records) if r in sites]
        if not (measured or structures or n_excluded or own_sites):
            continue
        covered |= records
        best = min(measured, key=lambda m: CLASS_ORDER.index(m["class"]), default=None)
        measured_records = {
            m["relationship_id"]: m for entry in measured for m in entry["measurements"]
        }
        groups = sorted({m["group"] for m in measured_records.values()})
        record_ids = sorted(measured_records)
        name = molecule_card.get("names.canonical_name")
        name_link = next(
            (
                rel
                for rel in molecule_card.relationships("same_as")
                if (rel.get("qualifiers") or {}).get("name")
            ),
            None,
        )
        name_basis = (
            "names.canonical_name"
            if (name or {}).get("value")
            else "same_as_name"
            if name_link
            else "not_stated"
        )
        name = (name or {}).get("value") or (
            name_link["qualifiers"]["name"] if name_link else None
        )
        shown = sorted(r for r in records if r.startswith(("chembl:", "pdb.ligand:")))
        text, source = molecule_label(name, shown, molecule_card.id)
        items.append(
            {
                "molecule_ref": molecule_card.id,
                "label": text,
                "label_source": source,
                "name": name,
                "records": shown,
                "bioactivity": {
                    "class": best["class"],
                    "best_pchembl": max(
                        (m["best_pchembl"] for m in measured if m["best_pchembl"]),
                        default=None,
                    ),
                    "measurements": len(groups)
                    if counting_rule == COUNTING_RULE
                    else sum(len(m["measurements"]) for m in measured),
                    "records": len(record_ids),
                }
                if best
                else None,
                "excluded_measurements": n_excluded,
                "structures": structures,
                "structures_of_interest": sorted(s for s, f in seen.items() if f),
                "sites": [
                    {
                        k: site[k]
                        for k in (
                            "ligand_ref",
                            "positions",
                            "site_class",
                            "spans_chains",
                        )
                    }
                    for site in own_sites
                ],
                "observed_in": [
                    kind
                    for kind, present in (
                        ("bioactivity", bool(measured or n_excluded)),
                        ("structure", bool(structures or own_sites)),
                    )
                    if present
                ],
            }
        )
        if _support is not None:
            decisions.append(
                {
                    "deck_index": index,
                    "item": items[-1],
                    "records": sorted(records),
                    "measured_refs": [m["molecule_ref"] for m in measured],
                    "measurement_group_ids": groups,
                    "measurement_record_ids": record_ids,
                    "best_class_ref": best["molecule_ref"] if best else None,
                    "structure_flags": seen,
                    "site_relationship_ids": [
                        site["relationship_id"] for site in own_sites
                    ],
                    "name_basis": name_basis,
                    "name_relationship_id": name_link["id"]
                    if name_basis == "same_as_name"
                    else None,
                }
            )
    items.sort(key=_rank)
    # Structure ligands count as molecules of the protein only where the PDB declares them
    # subject of investigation; additives and ions stay out of ``unmatched``.
    of_interest = {r for r, flags in in_structures.items() if any(flags.values())}
    referenced = set(by_molecule) | set(excluded) | of_interest
    if _support is not None:
        _support.update(decisions=decisions, bioactivity=bio, site_lookup=sites)
    return {
        "items": items,
        "unmatched": sorted(referenced - covered),
        "scope": bio["scope"],
        "classification": bio["classification"],
        "measurement_counting": make_derivation(
            counting_rule,
            inputs=[card.pinned_ref(), *[c.pinned_ref() for c in deck.cards]],
            parameters={
                "measurement_identity": bio["measurement_identity"]["rule"],
                "measurements": "distinct included measurement group ids across matched molecule items"
                if counting_rule == COUNTING_RULE
                else "included source records summed across matched molecule items (legacy)",
                "records": "distinct included source relationship ids across matched molecule items",
            },
        ),
    }


def compare_ligands(
    card: Any,
    deck: Any,
    other: Any,
    other_deck: Any,
    include_indirect: bool = False,
    thresholds: Dict[str, Any] | None = None,
    *,
    counting_rule: str = COUNTING_RULE,
) -> Dict[str, Any]:
    """Molecules related to both proteins, side by side, and those related to only one.

    Returns protein refs, shared/unique molecules, classification and both pinned
    counting derivations. The comparison juxtaposes the two ligand views and
    derives nothing new.
    """
    mine_view = ligands_view(
        card, deck, include_indirect, thresholds, counting_rule=counting_rule
    )
    mine = {i["molecule_ref"]: i for i in mine_view["items"]}
    view = ligands_view(
        other, other_deck, include_indirect, thresholds, counting_rule=counting_rule
    )
    theirs = {i["molecule_ref"]: i for i in view["items"]}

    def side(entry: Dict[str, Any]) -> Dict[str, Any]:
        keys = (
            "bioactivity",
            "structures",
            "structures_of_interest",
            "sites",
            "observed_in",
        )
        return {k: entry[k] for k in keys}

    shared = [
        {
            "molecule_ref": mid,
            "label": mine[mid]["label"],
            "label_source": mine[mid]["label_source"],
            "name": mine[mid]["name"] or theirs[mid]["name"],
            "self": side(mine[mid]),
            "other": side(theirs[mid]),
        }
        for mid in sorted(set(mine) & set(theirs))
    ]
    return {
        "self_ref": card.id,
        "other_ref": other.id,
        "shared": shared,
        "only_self": sorted(set(mine) - set(theirs)),
        "only_other": sorted(set(theirs) - set(mine)),
        "classification": view["classification"],
        "measurement_counting": {
            "self": mine_view["measurement_counting"],
            "other": view["measurement_counting"],
        },
    }
