"""PubChem → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.evidence_store import generate_evidence_id


def map_compound(pubchem_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal PubChem fields into canonical card fields.

    Supports PUG-REST property table shape:
      PropertyTable.Properties[0].MolecularWeight, CanonicalSMILES
    """
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    props = get_in(pubchem_json, ['PropertyTable', 'Properties']) or []
    if props:
        p0 = props[0]
        mw = p0.get('MolecularWeight')
        if mw is not None:
            fp = 'properties.physchem.molecular_weight'
            fields[fp] = mw
            ev = {
                'field': fp,
                'value': mw,
                'source': {'type': 'database', 'name': 'PubChem', 'record_id': str(p0.get('CID', ''))},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('PubChem', str(p0.get('CID', '')), fp, mw)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            field_evidence[fp] = [ev_id]
        smiles = p0.get('CanonicalSMILES') or p0.get('IsomericSMILES') or p0.get('ConnectivitySMILES')
        if smiles:
            fp = 'identifiers.smiles'
            fields[fp] = smiles
            ev = {
                'field': fp,
                'value': smiles,
                'source': {'type': 'database', 'name': 'PubChem', 'record_id': str(p0.get('CID', ''))},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('PubChem', str(p0.get('CID', '')), fp, smiles)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            field_evidence[fp] = [ev_id]

        formula = p0.get('MolecularFormula')
        if formula:
            fp = 'properties.physchem.formula'
            fields[fp] = formula
            ev = {
                'field': fp,
                'value': formula,
                'source': {'type': 'database', 'name': 'PubChem', 'record_id': str(p0.get('CID', ''))},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('PubChem', str(p0.get('CID', '')), fp, formula)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            field_evidence[fp] = [ev_id]

        inchikey = p0.get('InChIKey')
        if inchikey:
            fp = 'identifiers.inchikey'
            fields[fp] = inchikey
            ev = {
                'field': fp,
                'value': inchikey,
                'source': {'type': 'database', 'name': 'PubChem', 'record_id': str(p0.get('CID', ''))},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('PubChem', str(p0.get('CID', '')), fp, inchikey)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            field_evidence[fp] = [ev_id]

    cid = get_in(pubchem_json, ['PropertyTable', 'Properties', 0, 'CID'])
    if cid is not None:
        fp = 'identifiers.secondary_ids.pubchem'
        fields[fp] = str(cid)
        ev = {
            'field': fp,
            'value': str(cid),
            'source': {'type': 'database', 'name': 'PubChem', 'record_id': str(cid)},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('PubChem', str(cid), fp, str(cid))
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    return {'fields': fields, 'evidences': evidences, 'field_evidence': field_evidence}
