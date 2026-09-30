"""GPCRdb receptor → a protein card's GPCR classification, residues and structures (#83).

**Joined only through stated identity.** GPCRdb's receptor entry states its UniProt
accession (``protein/accession/<acc>``); nothing is matched by name or sequence.

It states:

- ``annotations.gpcr_classification``: GPCRdb's entry name, the receptor's class and
  family, and the numbering scheme GPCRdb uses for it;
- ``annotations.gpcr_segments``: the segments (N-term, TM1-7, the loops, H8, C-term),
  each a run of consecutive residues GPCRdb assigns to it;
- ``annotations.gpcr_residues``: the residues with a generic number, each with its
  residue, segment, GPCRdb's display number (``3.32x32``) and its number in every
  scheme GPCRdb states (Ballesteros-Weinstein, Wootten, Pin, Wang, the GPCRdb schemes
  of each class…);
- ``annotations.gpcr_structures``: per structure, the PDB entry, the receptor's chain,
  its activation state, the method and resolution, the publication, and the ligands
  (name, PDB chemical component, type, function) and signalling protein as stated. A
  structure GPCRdb states has no ligand ("Apo (no ligand)") is ``apo``, with no
  ligand item.

**Placed only through stated numbering.** GPCRdb numbers residues on the sequence its
entry states. Its numbers are UniProt's only when that sequence is the card's UniProt
sequence (rule ``gpcrdb_sequence_numbering@1``), and each residue must still match.
Otherwise segments and residues are kept in GPCRdb's numbering with ``not_placed``
(``sequence_differs`` or ``residue_mismatch``).
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Tuple

from sabueso.core.quantities import LENGTH_UNIT, quantity_node
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "GPCRdb"
CLASSIFICATION = "annotations.gpcr_classification"
SEGMENTS = "annotations.gpcr_segments"
RESIDUES = "annotations.gpcr_residues"
STRUCTURES = "annotations.gpcr_structures"
NUMBERING_RULE = "gpcrdb_sequence_numbering@1"


def _plain(text: Any) -> Any:
    """GPCRdb's names carry HTML (``&beta;<sub>2</sub>``); the plain text."""
    if not isinstance(text, str):
        return text
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def _placed(numbered: bool, position: int, residue: str, sequence: str) -> Dict:
    if not numbered:
        return {"not_placed": "sequence_differs", "numbering": "gpcrdb"}
    if not (0 < position <= len(sequence)) or sequence[position - 1] != residue:
        return {"not_placed": "residue_mismatch", "numbering": "gpcrdb"}
    return {
        "location": {"start": position, "end": position},
        "numbering": "uniprot",
    }


def segments(residues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs of consecutive residues GPCRdb assigns to one segment."""
    runs: List[Dict[str, Any]] = []
    for residue in sorted(residues, key=lambda r: r.get("sequence_number") or 0):
        number = residue.get("sequence_number")
        name = residue.get("protein_segment")
        if number is None or not name:
            continue
        last = runs[-1] if runs else None
        if last and last["segment"] == name and last["end"] == number - 1:
            last["end"] = number
        else:
            runs.append({"segment": name, "start": number, "end": number})
    return runs


def _apo(ligand: Dict[str, Any]) -> bool:
    """GPCRdb writes a structure without ligand as a ligand named "Apo (no ligand)"."""
    return str(ligand.get("PDB") or "").lower() == "apo"


def structure(row: Dict[str, Any]) -> Dict[str, Any]:
    stated = row.get("ligands") or []
    ligands = [
        {
            k: v
            for k, v in {
                "name": _plain(ligand.get("name")),
                "pdb_ccd": ligand.get("PDB") or None,
                "type": ligand.get("type")
                if ligand.get("type") not in (None, "", "None")
                else None,
                "function": ligand.get("function") or None,
            }.items()
            if v is not None
        }
        for ligand in stated
        if not _apo(ligand)
    ]
    signalling = row.get("signalling_protein") or {}
    partners = sorted(
        e.get("entry_name")
        for e in (signalling.get("data") or {}).values()
        if isinstance(e, dict) and e.get("entry_name")
    )
    resolution = row.get("resolution")
    item = {
        "structure": f"pdb:{str(row.get('pdb_code')).upper()}",
        "chain": row.get("preferred_chain"),
        "state": row.get("state"),
        "method": row.get("type"),
        "resolution": quantity_node(float(resolution), LENGTH_UNIT)
        if isinstance(resolution, (int, float))
        else None,
        "publication": row.get("publication"),
        "publication_date": row.get("publication_date"),
        "ligands": ligands,
        "apo": True if stated and all(_apo(ligand) for ligand in stated) else None,
        "signalling_protein": {"type": signalling.get("type"), "partners": partners}
        if signalling.get("type")
        else None,
    }
    return {k: v for k, v in item.items() if v not in (None, "", [])}


def map_receptor(
    receptor: Dict[str, Any],
    residues: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    accession: str,
    sequence: str,
    retrieved_at: str,
    limit: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    numbered = bool(sequence) and receptor.get("sequence") == sequence
    fields: Dict[str, List[Any]] = {}
    assertions: Dict[str, List[Dict[str, Any]]] = {}
    entry_name = receptor.get("entry_name")

    def state(field: str, item: Any, reference: str) -> None:
        made = make_source_assertion(
            field,
            item,
            SOURCE,
            reference,
            retrieved_at,
            subject_ref=f"uniprot:{accession}",
        )
        fields.setdefault(field, []).append(item)
        assertions.setdefault(field, []).append(made)

    classification = {
        "entry_name": entry_name,
        "name": _plain(receptor.get("name")),
        "receptor_class": receptor.get("receptor_class"),
        "family": _plain(receptor.get("family")),
        "numbering_scheme": receptor.get("residue_numbering_scheme"),
    }
    state(
        CLASSIFICATION,
        {k: v for k, v in classification.items() if v},
        f"receptor:{entry_name}",
    )
    for run in segments(residues):
        item = {"segment": run["segment"], "gpcrdb_start": run["start"]}
        item["gpcrdb_end"] = run["end"]
        if numbered:
            item["location"] = {"start": run["start"], "end": run["end"]}
            item["numbering"] = "uniprot"
        else:
            item["not_placed"] = "sequence_differs"
            item["numbering"] = "gpcrdb"
        state(SEGMENTS, item, f"residues:{entry_name}:{run['segment']}:{run['start']}")
    placed = 0
    for residue in residues:
        if not residue.get("display_generic_number"):
            continue
        number = residue.get("sequence_number")
        item = {
            "gpcrdb_position": number,
            "residue": residue.get("amino_acid"),
            "segment": residue.get("protein_segment"),
            "generic_number": residue.get("display_generic_number"),
            "generic_numbers": [
                {"scheme": a.get("scheme"), "label": a.get("label")}
                for a in residue.get("alternative_generic_numbers") or []
            ],
            **_placed(numbered, number, residue.get("amino_acid") or "", sequence),
        }
        if "location" in item:
            item["placed_via"] = {"rule": NUMBERING_RULE}
            placed += 1
        state(RESIDUES, item, f"residues:{entry_name}:{number}")
    for row in rows[:limit]:
        state(STRUCTURES, structure(row), f"structure:{row.get('pdb_code')}")
    mapping = {
        "fields": fields,
        "source_assertions": [a for v in assertions.values() for a in v],
        "field_source_assertions": {
            k: [a["id"] for a in v] for k, v in assertions.items()
        },
        "relationships": [],
    }
    return mapping, {
        "entry_name": entry_name,
        "sequence_matches": numbered,
        "residues_placed": placed,
        "count": min(len(rows), limit),
        "total_count": len(rows),
        "truncated": len(rows) > limit,
    }
