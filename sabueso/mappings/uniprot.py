"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.evidence_store import generate_evidence_id


def map_protein(uniprot_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """
    Map minimal UniProt fields into canonical card fields.

    Returns a dict with:
      - fields: canonical field_path → value
      - features: canonical feature field_path → list of feature items
    Evidence objects are created upstream (not here).
    """
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    # identifiers
    primary = uniprot_json.get('primaryAccession')
    if primary:
        fp = 'identifiers.secondary_ids.uniprot'
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
    for c in comments:
        if c.get('commentType') == 'FUNCTION':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    func_texts.append(v)
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
    if func_texts:
        fp = 'uniprot_comments.function'
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

    if pathway_texts:
        fp = 'uniprot_comments.pathway'
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
        fp = 'uniprot_comments.subunit'
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
    for f in uniprot_json.get('features', []) or []:
        if f.get('type') in ('Binding site', 'Active site'):
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
                else:
                    active_items.append(item)
    if binding_items or active_items:

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

    return {'fields': fields, 'features': features, 'evidences': evidences, 'field_evidence': field_evidence}
