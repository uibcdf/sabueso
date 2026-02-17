"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.evidence_store import generate_evidence_id


def map_protein(uniprot_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map UniProt payload data into canonical Sabueso structures.

    Returns a dictionary with canonical mappings, including:
    - ``fields``: ``field_path -> value``
    - ``features``: ``feature_field_path -> list[feature]``
    - ``evidences`` and ``field_evidence`` links for provenance
    """
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    # identifiers
    primary = uniprot_json.get('primaryAccession')
    if primary:
        fp = 'identifiers.uniprot'
        fields[fp] = primary
        ev = {
            'field': fp,
            'value': primary,
            'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('UniProt', primary, fp, primary)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    # canonical name
    name = get_in(uniprot_json, ['proteinDescription', 'recommendedName', 'fullName', 'value'])
    if name:
        fp = 'names.canonical_name'
        fields[fp] = name
        ev = {
            'field': fp,
            'value': name,
            'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('UniProt', primary or '', fp, name)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    # function (commentType == FUNCTION)
    comments = uniprot_json.get('comments', []) or []
    func_texts: List[str] = []
    pathway_texts: List[str] = []
    subunit_texts: List[str] = []
    catalytic_texts: List[str] = []
    subcell_texts: List[str] = []
    tissue_texts: List[str] = []
    ptm_texts: List[str] = []
    polymorphism_texts: List[str] = []
    for c in comments:
        if c.get('commentType') == 'FUNCTION':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    func_texts.append(v)
        if c.get('commentType') == 'CATALYTIC ACTIVITY':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    catalytic_texts.append(v)
        if c.get('commentType') == 'PATHWAY':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    pathway_texts.append(v)
        if c.get('commentType') == 'SUBUNIT':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    subunit_texts.append(v)
        if c.get('commentType') == 'SUBCELLULAR LOCATION':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    subcell_texts.append(v)
        if c.get('commentType') == 'TISSUE SPECIFICITY':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    tissue_texts.append(v)
        if c.get('commentType') == 'PTM':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    ptm_texts.append(v)
        if c.get('commentType') == 'POLYMORPHISM':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    polymorphism_texts.append(v)
    if func_texts:
        fp = 'annotations.function'
        fields[fp] = func_texts
        ev_ids: List[str] = []
        for txt in func_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if catalytic_texts:
        fp = 'annotations.catalytic_activity'
        fields[fp] = catalytic_texts
        ev_ids = []
        for txt in catalytic_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if pathway_texts:
        fp = 'annotations.pathway'
        fields[fp] = pathway_texts
        ev_ids = []
        for txt in pathway_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if subunit_texts:
        fp = 'annotations.subunit'
        fields[fp] = subunit_texts
        ev_ids = []
        for txt in subunit_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if subcell_texts:
        fp = 'annotations.subcellular_location'
        fields[fp] = subcell_texts
        ev_ids = []
        for txt in subcell_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if tissue_texts:
        fp = 'annotations.tissue_specificity'
        fields[fp] = tissue_texts
        ev_ids = []
        for txt in tissue_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if ptm_texts:
        fp = 'annotations.ptm'
        fields[fp] = ptm_texts
        ev_ids = []
        for txt in ptm_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    if polymorphism_texts:
        fp = 'annotations.polymorphism'
        fields[fp] = polymorphism_texts
        ev_ids = []
        for txt in polymorphism_texts:
            ev = {
                'field': fp,
                'value': txt,
                'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                'retrieved_at': retrieved_at,
            }
            ev_id = generate_evidence_id('UniProt', primary or '', fp, txt)
            ev['evidence_id'] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    # organism
    org_name = get_in(uniprot_json, ['organism', 'scientificName'])
    if org_name:
        fp = 'annotations.organism'
        fields[fp] = org_name
        ev = {
            'field': fp,
            'value': org_name,
            'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
            'retrieved_at': retrieved_at,
        }
        ev_id = generate_evidence_id('UniProt', primary or '', fp, org_name)
        ev['evidence_id'] = ev_id
        evidences.append(ev)
        field_evidence[fp] = [ev_id]

    # binding sites (features)
    binding_items: List[Dict[str, Any]] = []
    active_items: List[Dict[str, Any]] = []
    modified_items: List[Dict[str, Any]] = []
    glyco_items: List[Dict[str, Any]] = []
    disulfide_items: List[Dict[str, Any]] = []
    for f in uniprot_json.get('features', []) or []:
        if f.get('type') in ('Binding site', 'Active site', 'Modified residue', 'Glycosylation', 'Disulfide bond'):
            loc = f.get('location', {}) or {}
            start = get_in(loc, ['start', 'value'])
            end = get_in(loc, ['end', 'value'])
            if start is not None:
                item = {
                    'location': {
                        'kind': 'sequence',
                        'sequence': {
                            'sequence_id': f"UniProt:{primary}" if primary else None,
                            'start': start,
                            'end': end if end is not None else start,
                            'indexing': '1-based',
                        },
                    },
                    'description': f.get('description') or '',
                }
                if f.get('type') == 'Binding site':
                    binding_items.append(item)
                elif f.get('type') == 'Active site':
                    active_items.append(item)
                elif f.get('type') == 'Modified residue':
                    modified_items.append(item)
                elif f.get('type') == 'Glycosylation':
                    glyco_items.append(item)
                elif f.get('type') == 'Disulfide bond':
                    disulfide_items.append(item)
    if binding_items or active_items or modified_items or glyco_items or disulfide_items:

        if binding_items:
            fp = 'features_positional.binding_site'
            features[fp] = binding_items
            ev_ids: List[str] = []
            for item in binding_items:
                ev = {
                    'field': fp,
                    'value': item,
                    'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                    'retrieved_at': retrieved_at,
                }
                ev_id = generate_evidence_id('UniProt', primary or '', fp, item)
                ev['evidence_id'] = ev_id
                evidences.append(ev)
                ev_ids.append(ev_id)
            field_evidence[fp] = ev_ids

        if active_items:
            fp = 'features_positional.active_site'
            features[fp] = active_items
            ev_ids = []
            for item in active_items:
                ev = {
                    'field': fp,
                    'value': item,
                    'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                    'retrieved_at': retrieved_at,
                }
                ev_id = generate_evidence_id('UniProt', primary or '', fp, item)
                ev['evidence_id'] = ev_id
                evidences.append(ev)
                ev_ids.append(ev_id)
            field_evidence[fp] = ev_ids

        if modified_items:
            fp = 'features_positional.modified_residue'
            features[fp] = modified_items
            ev_ids = []
            for item in modified_items:
                ev = {
                    'field': fp,
                    'value': item,
                    'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                    'retrieved_at': retrieved_at,
                }
                ev_id = generate_evidence_id('UniProt', primary or '', fp, item)
                ev['evidence_id'] = ev_id
                evidences.append(ev)
                ev_ids.append(ev_id)
            field_evidence[fp] = ev_ids

        if glyco_items:
            fp = 'features_positional.glycosylation'
            features[fp] = glyco_items
            ev_ids = []
            for item in glyco_items:
                ev = {
                    'field': fp,
                    'value': item,
                    'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                    'retrieved_at': retrieved_at,
                }
                ev_id = generate_evidence_id('UniProt', primary or '', fp, item)
                ev['evidence_id'] = ev_id
                evidences.append(ev)
                ev_ids.append(ev_id)
            field_evidence[fp] = ev_ids

        if disulfide_items:
            fp = 'features_positional.disulfide_bond'
            features[fp] = disulfide_items
            ev_ids = []
            for item in disulfide_items:
                ev = {
                    'field': fp,
                    'value': item,
                    'source': {'type': 'database', 'name': 'UniProt', 'record_id': primary or ''},
                    'retrieved_at': retrieved_at,
                }
                ev_id = generate_evidence_id('UniProt', primary or '', fp, item)
                ev['evidence_id'] = ev_id
                evidences.append(ev)
                ev_ids.append(ev_id)
            field_evidence[fp] = ev_ids

    return {'fields': fields, 'features': features, 'evidences': evidences, 'field_evidence': field_evidence}
