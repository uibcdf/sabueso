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

    pref_name = chembl_json.get('pref_name')
    if pref_name:
        fp = 'names.canonical_name'
        fields[fp] = pref_name
        ev = {
            'field': fp,
            'value': pref_name,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, pref_name)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    molecule_type = chembl_json.get('molecule_type')
    if molecule_type:
        fp = 'properties.physchem.molecule_type'
        fields[fp] = molecule_type
        ev = {
            'field': fp,
            'value': molecule_type,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, molecule_type)
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

    hbd = get_in(chembl_json, ['molecule_properties', 'hbd'])
    if hbd is not None:
        fp = 'properties.physchem.hbd'
        fields[fp] = hbd
        ev = {
            'field': fp,
            'value': hbd,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, hbd)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    hba = get_in(chembl_json, ['molecule_properties', 'hba'])
    if hba is not None:
        fp = 'properties.physchem.hba'
        fields[fp] = hba
        ev = {
            'field': fp,
            'value': hba,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, hba)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    psa = get_in(chembl_json, ['molecule_properties', 'psa'])
    if psa is not None:
        fp = 'properties.physchem.tpsa'
        fields[fp] = psa
        ev = {
            'field': fp,
            'value': psa,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, psa)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    rtb = get_in(chembl_json, ['molecule_properties', 'rtb'])
    if rtb is not None:
        fp = 'properties.physchem.rotatable_bonds'
        fields[fp] = rtb
        ev = {
            'field': fp,
            'value': rtb,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, rtb)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    arom = get_in(chembl_json, ['molecule_properties', 'aromatic_rings'])
    if arom is not None:
        fp = 'properties.physchem.aromatic_rings'
        fields[fp] = arom
        ev = {
            'field': fp,
            'value': arom,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, arom)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    mw_freebase = get_in(chembl_json, ['molecule_properties', 'mw_freebase'])
    if mw_freebase is not None:
        fp = 'properties.physchem.molecular_weight'
        fields[fp] = mw_freebase
        ev = {
            'field': fp,
            'value': mw_freebase,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, mw_freebase)
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

    inchi = get_in(chembl_json, ['molecule_structures', 'standard_inchi'])
    if inchi:
        fp = 'identifiers.inchi'
        fields[fp] = inchi
        ev = {
            'field': fp,
            'value': inchi,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, inchi)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    inchikey = get_in(chembl_json, ['molecule_structures', 'standard_inchi_key'])
    if inchikey:
        fp = 'identifiers.inchikey'
        fields[fp] = inchikey
        ev = {
            'field': fp,
            'value': inchikey,
            'source': {'type': 'database', 'name': 'ChEMBL', 'record_id': chembl_id or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('ChEMBL', chembl_id or '', fp, inchikey)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    return {'fields': fields, 'evidences': evidences, 'field_evidence': field_evidence}
