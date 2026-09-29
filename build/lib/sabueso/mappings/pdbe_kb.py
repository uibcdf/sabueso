"""PDBe-KB ligand binding sites -> ``has_ligand_site`` relationships (#28), and interface
residues -> ``has_interface_with`` relationships (#40).

Each ligand PDBe-KB reports for a protein becomes one relationship of the protein to the
PDB chemical component (``pdb.ligand:<code>``). The qualifiers carry the residues it
contacts, in UniProt numbering, with the structures, entities and chains where each
contact is observed. They also carry PDBe-KB's own descriptors of the ligand
(``is_solvent``, ``significance``, scaffold, cross-references), kept as PDBe-KB states
them. They are not a relevance judgement Sabueso endorses: on TIM, glycerol and PEG are
not flagged as solvents. The PDB's ``subject_of_investigation`` flag, on
``has_structure``, is a separate statement and stays separate.

The relationship is supported by a PDBe-KB SourceAssertion that keeps the ligand record
verbatim.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion


def _text(value: Any) -> Any:
    return value if value not in ("", None) else None


def _residue(entry: Dict[str, Any]) -> Dict[str, Any]:
    start, end = entry.get("startIndex"), entry.get("endIndex")
    codes = [entry.get("startCode"), entry.get("endCode")]
    observed = sorted(
        (
            {
                "structure": f"pdb:{str(e.get('pdbId', '')).upper()}",
                "entity": e.get("entityId"),
                "chains": sorted(
                    c.strip()
                    for c in str(e.get("chainIds") or "").split(",")
                    if c.strip()
                ),
            }
            for e in entry.get("interactingPDBEntries") or []
        ),
        key=lambda o: (o["structure"], str(o["entity"])),
    )
    return {
        "start": start,
        "end": end if end is not None else start,
        "residue": codes[0] if start == end or end is None else "-".join(codes),
        "observed_in": observed,
    }


def map_ligand_sites(response: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map a PDBe-KB ``ligand_sites`` response (``tools.db.pdbe_kb``)."""
    accession = response["accession"]
    record = response.get("record") or {}
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for ligand in record.get("data") or []:
        code = ligand.get("accession")
        if not code:
            continue
        object_ref = f"pdb.ligand:{code}"
        residues = ligand.get("residues") or []
        index_types = {(r.get("indexType") or "").upper() for r in residues}
        # Always UniProt so far; any other numbering is kept visible, never assumed.
        numbering = "uniprot" if index_types <= {"UNIPROT"} else "mixed"
        assertion = make_source_assertion(
            "relationships.has_ligand_site",
            {"object_ref": object_ref, "ligand": ligand},
            "PDBe-KB",
            accession,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",  # PDBe-KB keys records by UniProt
        )
        source_assertions.append(assertion)
        extra = ligand.get("additionalData") or {}
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "has_ligand_site",
                object_ref,
                qualifiers={
                    "ligand_name": ligand.get("name"),
                    "numbering": numbering,
                    "residues": sorted(
                        (_residue(r) for r in residues), key=lambda r: r["start"]
                    ),
                    "structures": sorted(
                        f"pdb:{p.upper()}" for p in extra.get("pdbEntries") or []
                    ),
                    "is_solvent": extra.get("isSolvent"),
                    "significance": extra.get("significance"),
                    "num_atoms": extra.get("numAtoms"),
                    "scaffold_id": _text(extra.get("scaffoldId")),
                    "cofactor_id": _text(extra.get("coFactorId")),
                    "reaction_id": _text(extra.get("reactionId")),
                    "chembl_id": _text(extra.get("chemblId")),
                    "drugbank_id": _text(extra.get("drugBankId")),
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }


def _partner_ref(partner: Dict[str, Any]) -> str:
    """``uniprot:<acc>`` for a UniProt partner; otherwise PDBe-KB's own label, kept as
    stated (e.g. an antibody or T-cell receptor chain without a UniProt entry)."""
    accession = partner.get("accession") or ""
    kind = (partner.get("additionalData") or {}).get("type")
    if kind == "UNP":
        return f"uniprot:{accession}"
    return f"pdbe_kb.partner:{accession}"


def map_interfaces(response: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map a PDBe-KB ``interface_residues`` response (``tools.db.pdbe_kb``).

    One ``has_interface_with`` relationship per partner: the residues of this protein at
    its interface with that partner, in UniProt numbering, with the structures, entities
    and chains where each is observed. PDBe-KB derives them from the structures (PISA);
    what kind of interface it is (homomeric, a chimera with itself, a peptide in a
    complex...) is judged by ``Card.oligomer()``, never here.
    """
    accession = response["accession"]
    record = response.get("record") or {}
    source_assertions: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    for partner in record.get("data") or []:
        if not partner.get("accession"):
            continue
        object_ref = _partner_ref(partner)
        residues = partner.get("residues") or []
        index_types = {(r.get("indexType") or "").upper() for r in residues}
        numbering = "uniprot" if index_types <= {"UNIPROT"} else "mixed"
        assertion = make_source_assertion(
            "relationships.has_interface_with",
            {"object_ref": object_ref, "partner": partner},
            "PDBe-KB",
            accession,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        source_assertions.append(assertion)
        mapped_residues = sorted(
            (_residue(r) for r in residues), key=lambda r: r["start"]
        )
        # Where the interface is observed (``interactingPDBEntries``), not every entry
        # where a residue is resolved (``allPDBEntries``).
        structures = sorted(
            {o["structure"] for r in mapped_residues for o in r["observed_in"]}
        )
        relationships.append(
            make_relationship(
                f"uniprot:{accession}",
                "has_interface_with",
                object_ref,
                qualifiers={
                    "partner_name": partner.get("name"),
                    "partner_type": (partner.get("additionalData") or {}).get("type"),
                    "numbering": numbering,
                    "residues": mapped_residues,
                    "structures": structures,
                },
                source_assertion_ids=[assertion["id"]],
            )
        )
    return {
        "fields": {},
        "source_assertions": source_assertions,
        "field_source_assertions": {},
        "relationships": relationships,
    }
