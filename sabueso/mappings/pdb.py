"""PDB (RCSB) → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.evidence_store import generate_evidence_id


def map_structure(pdb_entry: Dict[str, Any], pdb_id: str, retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal PDB entry fields into canonical card fields.

    Expected (if present):
      - entry.struct.title
      - entry.rcsb_entry_info.experimental_method
      - entry.rcsb_entry_info.resolution_combined
    """
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    title = get_in(pdb_entry, ['entry', 'struct', 'title'])
    if title:
        fp = 'structure.entry_metadata.title'
        fields[fp] = title
        ev = {
            'field': fp,
            'value': title,
            'source': {'type': 'database', 'name': 'RCSB PDB', 'record_id': pdb_id},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('RCSB PDB', pdb_id, fp, title)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    method = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'experimental_method'])
    if method:
        fp = 'structure.entry_metadata.experimental_method'
        fields[fp] = method
        ev = {
            'field': fp,
            'value': method,
            'source': {'type': 'database', 'name': 'RCSB PDB', 'record_id': pdb_id},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('RCSB PDB', pdb_id, fp, method)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    res = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'resolution_combined'])
    if res:
        fp = 'structure.entry_metadata.resolution'
        fields[fp] = res
        ev = {
            'field': fp,
            'value': res,
            'source': {'type': 'database', 'name': 'RCSB PDB', 'record_id': pdb_id},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('RCSB PDB', pdb_id, fp, res)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    return {'fields': fields, 'evidences': evidences, 'field_evidence': field_evidence}
