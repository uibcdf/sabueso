"""PubChem → SmallMoleculeCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.source_assertion_store import make_source_assertion


def map_compound(pubchem_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal PubChem fields into canonical card fields.

    Supports PUG-REST property table shape:
      PropertyTable.Properties[0].MolecularWeight, CanonicalSMILES
    """
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    props = get_in(pubchem_json, ['PropertyTable', 'Properties']) or []
    if props:
        p0 = props[0]
        mw = p0.get('MolecularWeight')
        if mw is not None:
            fp = 'properties.physchem.molecular_weight'
            fields[fp] = mw
            assertion = make_source_assertion(fp, mw, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]
        smiles = p0.get('CanonicalSMILES') or p0.get('IsomericSMILES') or p0.get('ConnectivitySMILES')
        if smiles:
            fp = 'identifiers.smiles'
            fields[fp] = smiles
            assertion = make_source_assertion(fp, smiles, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        formula = p0.get('MolecularFormula')
        if formula:
            fp = 'properties.physchem.formula'
            fields[fp] = formula
            assertion = make_source_assertion(fp, formula, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        inchikey = p0.get('InChIKey')
        if inchikey:
            fp = 'identifiers.inchikey'
            fields[fp] = inchikey
            assertion = make_source_assertion(fp, inchikey, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        inchi = p0.get('InChI')
        if inchi:
            fp = 'identifiers.inchi'
            fields[fp] = inchi
            assertion = make_source_assertion(fp, inchi, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        xlogp = p0.get('XLogP')
        if xlogp is not None:
            fp = 'properties.physchem.logp'
            fields[fp] = xlogp
            assertion = make_source_assertion(fp, xlogp, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        tpsa = p0.get('TPSA')
        if tpsa is not None:
            fp = 'properties.physchem.tpsa'
            fields[fp] = tpsa
            assertion = make_source_assertion(fp, tpsa, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        hbd = p0.get('HBondDonorCount')
        if hbd is not None:
            fp = 'properties.physchem.hbd'
            fields[fp] = hbd
            assertion = make_source_assertion(fp, hbd, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        hba = p0.get('HBondAcceptorCount')
        if hba is not None:
            fp = 'properties.physchem.hba'
            fields[fp] = hba
            assertion = make_source_assertion(fp, hba, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

        rtb = p0.get('RotatableBondCount')
        if rtb is not None:
            fp = 'properties.physchem.rotatable_bonds'
            fields[fp] = rtb
            assertion = make_source_assertion(fp, rtb, 'PubChem', str(p0.get('CID', '')), retrieved_at)
            source_assertions.append(assertion)
            field_source_assertions[fp] = [assertion['source_assertion_id']]

    cid = get_in(pubchem_json, ['PropertyTable', 'Properties', 0, 'CID'])
    if cid is not None:
        fp = 'identifiers.pubchem'
        fields[fp] = str(cid)
        assertion = make_source_assertion(fp, str(cid), 'PubChem', str(cid), retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['source_assertion_id']]

    return {'fields': fields, 'source_assertions': source_assertions, 'field_source_assertions': field_source_assertions}
