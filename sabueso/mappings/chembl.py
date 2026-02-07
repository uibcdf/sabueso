"""ChEMBL → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.evidence_store import generate_evidence_id


def map_molecule(chembl_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal ChEMBL molecule fields into canonical card fields.

    Expected (if present):
      - molecule_chembl_id
      - molecule_properties.alogp
      - molecule_structures.canonical_smiles
    """
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    chembl_id = chembl_json.get('molecule_chembl_id')
    if chembl_id:
        fp = 'identifiers.secondary_ids.chembl'
        fields[fp] = chembl_id
        ev = {
            'field': fp,
            'value': chembl_id,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id, fp, chembl_id)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    alogp = get_in(chembl_json, ['molecule_properties', 'alogp'])
    if alogp is not None:
        fp = 'properties.physchem.logp'
        fields[fp] = alogp
        ev = {
            'field': fp,
            'value': alogp,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, alogp)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    smiles = get_in(chembl_json, ['molecule_structures', 'canonical_smiles'])
    if smiles:
        fp = 'identifiers.smiles'
        fields[fp] = smiles
        ev = {
            'field': fp,
            'value': smiles,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, smiles)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    return {'fields': fields, 'evidences': evidences, 'field_evidence': field_evidence}
