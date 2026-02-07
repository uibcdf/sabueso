"""PDB (RCSB) → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict

from .base import get_in


def map_structure(pdb_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map minimal PDB entry fields into canonical card fields.

    Expected (if present):
      - entry.struct.title
      - entry.rcsb_entry_info.experimental_method
      - entry.rcsb_entry_info.resolution_combined
    """
    fields: Dict[str, Any] = {}

    title = get_in(pdb_entry, ['entry', 'struct', 'title'])
    if title:
        fields['structure.entry_metadata.title'] = title

    method = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'experimental_method'])
    if method:
        fields['structure.entry_metadata.experimental_method'] = method

    res = get_in(pdb_entry, ['entry', 'rcsb_entry_info', 'resolution_combined'])
    if res:
        fields['structure.entry_metadata.resolution'] = res

    return {'fields': fields}
