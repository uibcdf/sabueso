"""SKEMPI rows → ``annotations.interface_mutations`` (#83).

One item per SKEMPI row whose complex includes the protein, as SKEMPI states it: the
structure and the chains of each side, the proteins as SKEMPI names them, the mutations,
the affinities of mutant and wild type, kinetics and thermodynamics where measured, the
temperature, the method, the publication and SKEMPI's notes.

**Joined only through stated identity.** A row joins a card when UniProt states that one
of the chains of the row's PDB entry is this protein (the entry's PDB cross-reference,
``Chains=A/B=…``). Nothing is matched by the protein names SKEMPI writes, or by
sequence.

**Placed only through stated numbering.** A mutation is written in the PDB entry's
author numbering. It is placed in UniProt numbering (rule ``rcsb_author_numbering@1``)
only when the mutated chain is this protein's, the card holds the author numbering RCSB
states for that chain of that entry (``structures=``), and the residue SKEMPI names is
UniProt's at that position. Otherwise ``not_placed`` says why:
``partner_chain``, ``structure_not_loaded``, ``author_residue_not_mapped`` or
``residue_mismatch``.

**Quantities as stated.** Affinities are in molar, kinetics in 1/(M·s) and 1/s,
ΔH in kcal/mol, ΔS in cal/(mol·K), temperatures in kelvin. A bound (``>1E-04``) keeps its
relation, "n.b." is ``no_binding``, and "298(assumed)" is 298 K with
``temperature_assumed``. ΔΔG is not stored: it is derived in the view, with its rule.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from sabueso.core.quantities import quantity_node
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "SKEMPI"
FIELD = "annotations.interface_mutations"
RULE = "rcsb_author_numbering@1"

MUTATION = re.compile(r"^([A-Z])([A-Za-z0-9])(-?\d+)([a-z]?)([A-Z])$")
NUMBER = re.compile(r"^([<>])?\s*(-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?)$")
NO_BINDING = {"n.b", "n.b."}

#: SKEMPI column → (item key, unit).
AFFINITY = {
    "Affinity_mut (M)": ("mutant", "molar"),
    "Affinity_wt (M)": ("wild_type", "molar"),
}
KINETICS = {
    "kon_mut (M^(-1)s^(-1))": ("kon_mutant", "1/(M*s)"),
    "kon_wt (M^(-1)s^(-1))": ("kon_wild_type", "1/(M*s)"),
    "koff_mut (s^(-1))": ("koff_mutant", "1/s"),
    "koff_wt (s^(-1))": ("koff_wild_type", "1/s"),
}
THERMODYNAMICS = {
    "dH_mut (kcal mol^(-1))": ("dh_mutant", "kcal/mol"),
    "dH_wt (kcal mol^(-1))": ("dh_wild_type", "kcal/mol"),
    "dS_mut (cal mol^(-1) K^(-1))": ("ds_mutant", "cal/(mol*K)"),
    "dS_wt (cal mol^(-1) K^(-1))": ("ds_wild_type", "cal/(mol*K)"),
}


def chains_of(entry: Dict[str, Any], pdb_id: str) -> set:
    """The chains UniProt states are this entry's protein in a PDB entry."""
    chains: set = set()
    for xref in entry.get("uniProtKBCrossReferences") or []:
        if xref.get("database") != "PDB" or xref.get("id", "").upper() != pdb_id:
            continue
        for prop in xref.get("properties") or []:
            if prop.get("key") != "Chains":
                continue
            for part in str(prop.get("value") or "").split(","):
                chains.update(c.strip() for c in part.split("=")[0].split("/"))
    return {c for c in chains if c}


def uniprot_position(segments: List[list] | None, author: str) -> int | None:
    """The UniProt position of an author residue id, from ``author_numbering``."""
    for beg, end, first in segments or []:
        if isinstance(first, int):
            if author.lstrip("-").isdigit() and first <= int(author) <= first + (
                end - beg
            ):
                return beg + int(author) - first
        elif str(first) == author:
            return beg
    return None


def _value(stated: str | None, unit: str, prefix: str) -> Dict[str, Any]:
    """``{prefix: quantity, prefix_relation?}``, ``{prefix_no_binding}``, or the text
    as stated when it is neither."""
    text = (stated or "").strip()
    if not text:
        return {}
    if text.lower() in NO_BINDING:
        return {f"{prefix}_no_binding": True}
    match = NUMBER.match(text)
    if not match:
        return {f"{prefix}_stated": text}
    out = {prefix: quantity_node(float(match.group(2)), unit)}
    if match.group(1):
        out[f"{prefix}_relation"] = match.group(1)
    return out


def _block(row: Dict[str, str], columns: Dict[str, tuple]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for column, (key, unit) in columns.items():
        out.update(_value(row.get(column), unit, key))
    return out


def _temperature(stated: str | None) -> Dict[str, Any]:
    text = (stated or "").strip()
    if not text:
        return {}
    assumed = text.endswith("(assumed)")
    number = text.replace("(assumed)", "").strip()
    try:
        out: Dict[str, Any] = {"temperature": quantity_node(float(number), "kelvin")}
    except ValueError:
        return {"temperature_stated": text}
    if assumed:
        out["temperature_assumed"] = True
    return out


def _mutation(
    stated: str,
    mine: set,
    numbering: Dict[str, List[list]] | None,
    sequence: str,
    pdb_ref: str,
    location_class: str | None,
) -> Dict[str, Any]:
    match = MUTATION.match(stated.strip())
    if not match:
        return {"stated": stated, "not_placed": "unparsed_mutation"}
    original, chain, number, insertion, change = match.groups()
    author = f"{number}{insertion.upper()}" if insertion else number
    item: Dict[str, Any] = {
        "chain": chain,
        "author_residue": author,
        "original": original,
        "change": change,
        "location_class": location_class,
        "on": "this_protein" if chain in mine else "partner",
    }
    if chain not in mine:
        item["not_placed"] = "partner_chain"
    elif not numbering or chain not in numbering:
        item["not_placed"] = "structure_not_loaded"
    else:
        position = uniprot_position(numbering[chain], author)
        if position is None:
            item["not_placed"] = "author_residue_not_mapped"
        elif not sequence or not 0 < position <= len(sequence):
            item["not_placed"] = "author_residue_not_mapped"
        elif sequence[position - 1] != original:
            item["not_placed"] = "residue_mismatch"
        else:
            item["location"] = {"start": position, "end": position}
            item["placed_via"] = {"rule": RULE, "structure": pdb_ref}
    return {k: v for k, v in item.items() if v is not None}


def map_rows(
    rows: Dict[str, List[Dict[str, str]]],
    accession: str,
    entry: Dict[str, Any],
    numbering: Dict[str, Dict[str, List[list]]],
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    """``numbering``: per PDB entry, the card's ``author_numbering`` of this protein."""
    sequence = (entry.get("sequence") or {}).get("value") or ""
    items, assertions = [], []
    for pdb_id in sorted(rows):
        mine = chains_of(entry, pdb_id)
        pdb_ref = f"pdb:{pdb_id}"
        for index, row in enumerate(rows[pdb_id]):
            parts = (row.get("#Pdb") or "").split("_")
            sides = [list(p) for p in parts[1:3]]
            if not mine & {c for side in sides for c in side}:
                continue
            classes = (row.get("iMutation_Location(s)") or "").split(",")
            stated = [m for m in (row.get("Mutation(s)_PDB") or "").split(",") if m]
            mutations = [
                _mutation(
                    m,
                    mine,
                    numbering.get(pdb_id),
                    sequence,
                    pdb_ref,
                    classes[i].strip() if i < len(classes) and classes[i] else None,
                )
                for i, m in enumerate(stated)
            ]
            reference = (row.get("Reference") or "").strip()
            item = {
                "structure": pdb_ref,
                "complex": row.get("#Pdb"),
                "sides": sides,
                "protein_chains": sorted(mine & {c for s in sides for c in s}),
                "proteins": [row.get("Protein 1"), row.get("Protein 2")],
                "mutations": mutations,
                "affinity": _block(row, AFFINITY),
                "kinetics": _block(row, KINETICS) or None,
                "thermodynamics": _block(row, THERMODYNAMICS) or None,
                **_temperature(row.get("Temperature")),
                "method": row.get("Method") or None,
                "reference": f"pubmed:{reference}" if reference.isdigit() else None,
                "reference_stated": None if reference.isdigit() else reference or None,
                "notes": row.get("Notes") or None,
                "hold_out_type": row.get("Hold_out_type") or None,
                "skempi_version": row.get("SKEMPI version") or None,
            }
            item = {k: v for k, v in item.items() if v not in (None, "", [], {})}
            assertion = make_source_assertion(
                FIELD,
                item,
                SOURCE,
                f"{row.get('#Pdb')}:{row.get('Mutation(s)_PDB')}:{index}",
                retrieved_at,
                subject_ref=f"uniprot:{accession}",
            )
            if version is not None:
                assertion["source"]["version"] = str(version)
            items.append(item)
            assertions.append(assertion)
    return {
        "fields": {FIELD: items} if items else {},
        "source_assertions": assertions,
        "field_source_assertions": {FIELD: [a["id"] for a in assertions]}
        if assertions
        else {},
        "relationships": [],
    }
