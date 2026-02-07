"""ChEMBL → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict

from .base import get_in


def map_molecule(chembl_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map minimal ChEMBL molecule fields into canonical card fields.

    Expected (if present):
      - molecule_chembl_id
      - molecule_properties.alogp
      - molecule_structures.canonical_smiles
    """
    fields: Dict[str, Any] = {}

    chembl_id = chembl_json.get('molecule_chembl_id')
    if chembl_id:
        fields['identifiers.secondary_ids.chembl'] = chembl_id

    alogp = get_in(chembl_json, ['molecule_properties', 'alogp'])
    if alogp is not None:
        fields['properties.physchem.logp'] = alogp

    smiles = get_in(chembl_json, ['molecule_structures', 'canonical_smiles'])
    if smiles:
        fields['identifiers.smiles'] = smiles

    return {'fields': fields}
