"""KLIFS kinases → a protein card's kinase classification, pocket and structures (#83).

**Joined only through stated identity.** A KLIFS kinase joins a card when KLIFS states
the card's UniProt accession for it (``kinase_names``). A protein with two kinase
domains (a JAK's kinase and pseudokinase) is two KLIFS kinases.

It states:

- ``annotations.kinase_classification``: per kinase, KLIFS's id and name, its group,
  family and subfamily, and the sequence of its 85 pocket residues (``_`` for a gap);
- ``annotations.kinase_structures``: per KLIFS structure (a PDB entry, chain and
  alternate location), the conformation as KLIFS classifies it (``dfg``, ``ac_helix``:
  in, out, out-like, na), the orthosteric and allosteric ligands (PDB chemical component
  ids), KLIFS's quality score, the resolution, and the missing residues and atoms;
- ``annotations.kinase_pocket``: per kinase, the 85 pocket positions in KLIFS's
  numbering (``GK.45`` is the gatekeeper, ``hinge.46``-``48``, ``xDFG.80``-``83``…),
  each with its residue.

**Placed only through stated numbering.** KLIFS states the pocket positions in one
structure's author numbering (``interactions_match_residues``). One structure is chosen
by rule ``klifs_pocket_reference@1``: among the kinase's structures whose PDB entry the
card holds with RCSB's author numbering for that chain, one whose pocket is the kinase's
(no mutation, no gap) first, then the highest quality score, the fewest missing residues
and atoms, the best resolution, and the lowest KLIFS structure id. Its author residues
are placed in UniProt numbering through the numbering RCSB states (rule
``rcsb_author_numbering@1``), and the residue must be UniProt's there. Otherwise
``not_placed`` says why: ``no_structure_loaded`` (no structure of the kinase is on the
card with its author numbering), ``missing_in_structure``, ``author_residue_not_mapped``
or ``residue_mismatch``; a gap in the kinase's pocket is ``gap``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sabueso.core.quantities import LENGTH_UNIT, quantity_node
from sabueso.core.source_assertion_store import make_source_assertion

from .skempi import RULE as AUTHOR_RULE
from .skempi import chains_of, uniprot_position

SOURCE = "KLIFS"
CLASSIFICATION = "annotations.kinase_classification"
STRUCTURES = "annotations.kinase_structures"
POCKET = "annotations.kinase_pocket"
REFERENCE_RULE = "klifs_pocket_reference@1"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ligand(value: Any) -> str | None:
    """A PDB chemical component id, or None (KLIFS writes 0 or an empty string)."""
    return None if value in (None, "", 0, "0") else str(value)


def classification(kinase: Dict[str, Any]) -> Dict[str, Any]:
    item = {
        "kinase_id": kinase.get("kinase_ID"),
        "name": kinase.get("name"),
        "group": kinase.get("group"),
        "family": kinase.get("family"),
        "subfamily": kinase.get("subfamily"),
        "pocket_sequence": kinase.get("pocket"),
    }
    return {k: v for k, v in item.items() if v not in (None, "")}


def structure(kinase: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    resolution = _number(row.get("resolution"))
    item = {
        "kinase_id": kinase.get("kinase_ID"),
        "klifs_structure_id": row.get("structure_ID"),
        "structure": f"pdb:{str(row.get('pdb')).upper()}",
        "chain": row.get("chain"),
        "alt": row.get("alt") or None,
        "dfg": row.get("DFG"),
        "ac_helix": row.get("aC_helix"),
        "ligand": _ligand(row.get("ligand")),
        "allosteric_ligand": _ligand(row.get("allosteric_ligand")),
        "quality_score": _number(row.get("quality_score")),
        "resolution": quantity_node(resolution, LENGTH_UNIT)
        if resolution is not None
        else None,
        "missing_residues": row.get("missing_residues"),
        "missing_atoms": row.get("missing_atoms"),
    }
    return {k: v for k, v in item.items() if v not in (None, "")}


def reference(
    kinase: Dict[str, Any],
    rows: List[Dict[str, Any]],
    entry: Dict[str, Any],
    numbering: Dict[str, Dict[str, List[list]]],
) -> Dict[str, Any] | None:
    """The structure whose author numbering places the pocket (``klifs_pocket_reference@1``,
    see the module docstring), or None."""
    usable = []
    for row in rows:
        pdb_id = str(row.get("pdb")).upper()
        chain = row.get("chain")
        if chain not in chains_of(entry, pdb_id):
            continue
        if not (numbering.get(pdb_id) or {}).get(chain):
            continue
        usable.append(row)

    def order(row: Dict[str, Any]) -> Tuple:
        resolution = _number(row.get("resolution"))
        return (
            row.get("pocket") != kinase.get("pocket"),
            -(_number(row.get("quality_score")) or 0.0),
            row.get("missing_residues") or 0,
            row.get("missing_atoms") or 0,
            resolution if resolution is not None else float("inf"),
            row.get("structure_ID") or 0,
        )

    return min(usable, key=order) if usable else None


def pocket(
    kinase: Dict[str, Any],
    chosen: Dict[str, Any] | None,
    residues: List[Dict[str, Any]] | None,
    sequence: str,
    numbering: Dict[str, Dict[str, List[list]]],
) -> List[Dict[str, Any]]:
    """The 85 pocket positions of a kinase, placed through the chosen structure."""
    letters = kinase.get("pocket") or ""
    by_index = {r.get("index"): r for r in residues or []}
    labels = [r.get("KLIFS_position") for r in residues or []]
    items = []
    for index, residue in enumerate(letters, start=1):
        stated = by_index.get(index) or {}
        item: Dict[str, Any] = {
            "kinase_id": kinase.get("kinase_ID"),
            "index": index,
            "klifs_position": stated.get("KLIFS_position")
            or (labels[index - 1] if index <= len(labels) else None),
        }
        if residue == "_":
            item["not_placed"] = "gap"
            items.append({k: v for k, v in item.items() if v is not None})
            continue
        item["residue"] = residue
        if chosen is None:
            item["not_placed"] = "no_structure_loaded"
        else:
            pdb_id = str(chosen.get("pdb")).upper()
            chain = chosen.get("chain")
            author = str(stated.get("Xray_position") or "").strip()
            if not author or author in ("_", "0"):
                item["not_placed"] = "missing_in_structure"
            else:
                position = uniprot_position(numbering[pdb_id][chain], author)
                if position is None:
                    item["not_placed"] = "author_residue_not_mapped"
                elif not (0 < position <= len(sequence)) or (
                    sequence[position - 1] != residue
                ):
                    item["not_placed"] = "residue_mismatch"
                else:
                    item["location"] = {"start": position, "end": position}
                item["placed_via"] = {
                    "rule": AUTHOR_RULE,
                    "reference_rule": REFERENCE_RULE,
                    "structure": f"pdb:{pdb_id}",
                    "chain": chain,
                    "author_position": author,
                }
        item["numbering"] = "uniprot" if "location" in item else "klifs"
        items.append({k: v for k, v in item.items() if v is not None})
    return items


def map_kinases(
    kinases: List[Dict[str, Any]],
    accession: str,
    entry: Dict[str, Any],
    numbering: Dict[str, Dict[str, List[list]]],
    retrieved_at: str,
    limit: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """``kinases`` are ``{"kinase", "structures", "reference", "pocket"}`` per KLIFS
    kinase. Returns the mapping and what the enrichment record reports."""
    sequence = (entry.get("sequence") or {}).get("value") or ""
    fields: Dict[str, List[Dict[str, Any]]] = {
        CLASSIFICATION: [],
        STRUCTURES: [],
        POCKET: [],
    }
    assertions: Dict[str, List[Dict[str, Any]]] = {k: [] for k in fields}
    total = 0

    def state(field: str, item: Dict[str, Any], reference: str) -> None:
        made = make_source_assertion(
            field,
            item,
            SOURCE,
            reference,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        fields[field].append(item)
        assertions[field].append(made)

    for found in kinases:
        kinase = found["kinase"]
        kid = kinase.get("kinase_ID")
        state(CLASSIFICATION, classification(kinase), f"kinase:{kid}")
        rows = found.get("structures") or []
        total += len(rows)
        for row in rows[: max(0, limit - len(fields[STRUCTURES]))]:
            state(
                STRUCTURES,
                structure(kinase, row),
                f"structure:{row.get('structure_ID')}",
            )
        for item in pocket(
            kinase, found.get("reference"), found.get("pocket"), sequence, numbering
        ):
            state(POCKET, item, f"kinase:{kid}:pocket:{item['index']}")
    placed = sum(1 for i in fields[POCKET] if "location" in i)
    mapping = {
        "fields": {k: v for k, v in fields.items() if v},
        "source_assertions": [a for v in assertions.values() for a in v],
        "field_source_assertions": {
            k: [a["id"] for a in v] for k, v in assertions.items() if v
        },
        "relationships": [],
    }
    return mapping, {
        "kinases": [k["kinase"].get("kinase_ID") for k in kinases],
        "count": len(fields[STRUCTURES]),
        "total_count": total,
        "truncated": total > len(fields[STRUCTURES]),
        "pocket_placed": placed,
        "pocket_references": [
            {
                "kinase_id": k["kinase"].get("kinase_ID"),
                "structure": f"pdb:{str(k['reference'].get('pdb')).upper()}",
                "chain": k["reference"].get("chain"),
                "klifs_structure_id": k["reference"].get("structure_ID"),
            }
            for k in kinases
            if k.get("reference")
        ],
    }
