"""A protein card crossed with a deck of SmallMoleculeCards (uibcdf/sabueso#23, #25).

A ProteinCard refers to molecules by source record: ChEMBL molecules in its
``has_bioactivity`` relationships and PDB chemical components among the ligands of its
``has_structure`` relationships. A SmallMoleculeCard lists the records of one molecule as
``same_as`` links to its InChIKey anchor. Crossing both tells, per molecule, what was
measured on the protein and in which structures it was observed.

These views only bring together what the cards already hold. Activity classes are the
derived ones of ``Card.bioactivities()`` (rule ``bioactivity_class@2``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from .bioactivities import CLASS_ORDER


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
        entry["molecule"],
    )


def ligands_view(
    card: Any,
    deck: Any,
    include_indirect: bool = False,
    thresholds: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Per molecule of ``deck``: its bioactivity on ``card`` and its structures.

    Returns ``{"items", "unmatched", "scope", "classification"}``. Each item lists the
    structures where the molecule is observed and, among them, those where the PDB
    declares it subject of investigation. ``unmatched`` lists the molecule records of the
    protein card that no card of the deck covers.
    """
    bio = card.bioactivities(include_indirect=include_indirect, thresholds=thresholds)
    by_molecule = {item["molecule_ref"]: item for item in bio["items"]}
    excluded: Dict[str, int] = {}
    for x in bio["excluded"]:
        excluded[x["molecule_ref"]] = excluded.get(x["molecule_ref"], 0) + 1
    in_structures = _structure_ligands(card)
    sites = {}
    if card.relationships("has_ligand_site"):
        from .ligand_sites import ligand_sites_view

        sites = {i["ligand"]: i for i in ligand_sites_view(card)["items"]}

    items: List[Dict[str, Any]] = []
    covered: Set[str] = set()
    for molecule_card in deck.cards:
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
        name = molecule_card.get("names.canonical_name")
        items.append(
            {
                "molecule": molecule_card.id,
                "name": (name or {}).get("value")
                or next(
                    (
                        rel["qualifiers"].get("name")
                        for rel in molecule_card.relationships("same_as")
                        if (rel.get("qualifiers") or {}).get("name")
                    ),
                    None,
                ),
                "records": sorted(
                    r for r in records if r.startswith(("chembl:", "pdb.ligand:"))
                ),
                "bioactivity": {
                    "class": best["class"],
                    "best_pchembl": max(
                        (m["best_pchembl"] for m in measured if m["best_pchembl"]),
                        default=None,
                    ),
                    "measurements": sum(len(m["measurements"]) for m in measured),
                }
                if best
                else None,
                "excluded_measurements": n_excluded,
                "structures": structures,
                "structures_of_interest": sorted(s for s, f in seen.items() if f),
                "sites": [
                    {
                        k: site[k]
                        for k in ("ligand", "positions", "site_class", "spans_chains")
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
    items.sort(key=_rank)
    # Structure ligands count as molecules of the protein only where the PDB declares them
    # subject of investigation; additives and ions stay out of ``unmatched``.
    of_interest = {r for r, flags in in_structures.items() if any(flags.values())}
    referenced = set(by_molecule) | set(excluded) | of_interest
    return {
        "items": items,
        "unmatched": sorted(referenced - covered),
        "scope": bio["scope"],
        "classification": bio["classification"],
    }


def compare_ligands(
    card: Any,
    deck: Any,
    other: Any,
    other_deck: Any,
    include_indirect: bool = False,
    thresholds: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Molecules related to both proteins, side by side, and those related to only one.

    Returns ``{"shared", "only_self", "only_other", "classification"}``. The comparison
    juxtaposes the two ligand views and derives nothing new.
    """
    mine = {
        i["molecule"]: i
        for i in ligands_view(card, deck, include_indirect, thresholds)["items"]
    }
    view = ligands_view(other, other_deck, include_indirect, thresholds)
    theirs = {i["molecule"]: i for i in view["items"]}

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
            "molecule": mid,
            "name": mine[mid]["name"] or theirs[mid]["name"],
            "self": side(mine[mid]),
            "other": side(theirs[mid]),
        }
        for mid in sorted(set(mine) & set(theirs))
    ]
    return {
        "self": card.id,
        "other": other.id,
        "shared": shared,
        "only_self": sorted(set(mine) - set(theirs)),
        "only_other": sorted(set(theirs) - set(mine)),
        "classification": view["classification"],
    }
