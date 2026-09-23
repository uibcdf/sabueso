"""ChEMBL → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.source_assertion_store import make_source_assertion


def map_molecule(chembl_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal ChEMBL molecule fields into canonical card fields.

    Expected (if present):
      - molecule_chembl_id
      - molecule_properties.alogp
      - molecule_structures.canonical_smiles
    """
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    chembl_id = chembl_json.get('molecule_chembl_id')
    if chembl_id:
        fp = 'identifiers.chembl'
        fields[fp] = chembl_id
        assertion = make_source_assertion(fp, chembl_id, 'ChEMBL', chembl_id, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    pref_name = chembl_json.get('pref_name')
    if pref_name:
        fp = 'names.canonical_name'
        fields[fp] = pref_name
        assertion = make_source_assertion(fp, pref_name, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    molecule_type = chembl_json.get('molecule_type')
    if molecule_type:
        fp = 'properties.physchem.molecule_type'
        fields[fp] = molecule_type
        assertion = make_source_assertion(fp, molecule_type, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    alogp = get_in(chembl_json, ['molecule_properties', 'alogp'])
    if alogp is not None:
        fp = 'properties.physchem.logp'
        fields[fp] = alogp
        assertion = make_source_assertion(fp, alogp, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    hbd = get_in(chembl_json, ['molecule_properties', 'hbd'])
    if hbd is not None:
        fp = 'properties.physchem.hbd'
        fields[fp] = hbd
        assertion = make_source_assertion(fp, hbd, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    hba = get_in(chembl_json, ['molecule_properties', 'hba'])
    if hba is not None:
        fp = 'properties.physchem.hba'
        fields[fp] = hba
        assertion = make_source_assertion(fp, hba, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    psa = get_in(chembl_json, ['molecule_properties', 'psa'])
    if psa is not None:
        fp = 'properties.physchem.tpsa'
        fields[fp] = psa
        assertion = make_source_assertion(fp, psa, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    rtb = get_in(chembl_json, ['molecule_properties', 'rtb'])
    if rtb is not None:
        fp = 'properties.physchem.rotatable_bonds'
        fields[fp] = rtb
        assertion = make_source_assertion(fp, rtb, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    arom = get_in(chembl_json, ['molecule_properties', 'aromatic_rings'])
    if arom is not None:
        fp = 'properties.physchem.aromatic_rings'
        fields[fp] = arom
        assertion = make_source_assertion(fp, arom, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    mw_freebase = get_in(chembl_json, ['molecule_properties', 'mw_freebase'])
    if mw_freebase is not None:
        fp = 'properties.physchem.molecular_weight'
        fields[fp] = mw_freebase
        assertion = make_source_assertion(fp, mw_freebase, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    smiles = get_in(chembl_json, ['molecule_structures', 'canonical_smiles'])
    if smiles:
        fp = 'identifiers.smiles'
        fields[fp] = smiles
        assertion = make_source_assertion(fp, smiles, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    inchi = get_in(chembl_json, ['molecule_structures', 'standard_inchi'])
    if inchi:
        fp = 'identifiers.inchi'
        fields[fp] = inchi
        assertion = make_source_assertion(fp, inchi, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    inchikey = get_in(chembl_json, ['molecule_structures', 'standard_inchi_key'])
    if inchikey:
        fp = 'identifiers.inchikey'
        fields[fp] = inchikey
        assertion = make_source_assertion(fp, inchikey, 'ChEMBL', chembl_id or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    return {'fields': fields, 'source_assertions': source_assertions, 'field_source_assertions': field_source_assertions}
