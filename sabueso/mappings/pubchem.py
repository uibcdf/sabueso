"""PubChem → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict

from .base import get_in


def map_compound(pubchem_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map minimal PubChem fields into canonical card fields.

    Supports PUG-REST property table shape:
      PropertyTable.Properties[0].MolecularWeight, CanonicalSMILES
    """
    fields: Dict[str, Any] = {}

    props = get_in(pubchem_json, ['PropertyTable', 'Properties']) or []
    if props:
        p0 = props[0]
        mw = p0.get('MolecularWeight')
        if mw is not None:
            fields['properties.physchem.molecular_weight'] = mw
        smiles = p0.get('CanonicalSMILES') or p0.get('IsomericSMILES')
        if smiles:
            fields['identifiers.smiles'] = smiles

    cid = get_in(pubchem_json, ['PropertyTable', 'Properties', 0, 'CID'])
    if cid is not None:
        fields['identifiers.secondary_ids.pubchem'] = str(cid)

    return {'fields': fields}
