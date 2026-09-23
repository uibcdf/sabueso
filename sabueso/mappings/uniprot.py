"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in
from sabueso.core.source_assertion_store import make_source_assertion


def map_protein(uniprot_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map UniProt payload data into canonical Sabueso structures.

    Returns a dictionary with canonical mappings, including:
    - ``fields``: ``field_path -> value``
    - ``features``: ``feature_field_path -> list[feature]``
    - ``source_assertions`` and ``field_source_assertions`` links for provenance
    """
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    # identifiers
    primary = uniprot_json.get('primaryAccession')
    if primary:
        fp = 'identifiers.uniprot'
        fields[fp] = primary
        assertion = make_source_assertion(fp, primary, 'UniProt', primary, retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

    # canonical name
    name = get_in(uniprot_json, ['proteinDescription', 'recommendedName', 'fullName', 'value'])
    if name:
        fp = 'names.canonical_name'
        fields[fp] = name
        assertion = make_source_assertion(fp, name, 'UniProt', primary or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

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
        sa_ids: List[str] = []
        for txt in func_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if catalytic_texts:
        fp = 'annotations.catalytic_activity'
        fields[fp] = catalytic_texts
        sa_ids = []
        for txt in catalytic_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if pathway_texts:
        fp = 'annotations.pathway'
        fields[fp] = pathway_texts
        sa_ids = []
        for txt in pathway_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if subunit_texts:
        fp = 'annotations.subunit'
        fields[fp] = subunit_texts
        sa_ids = []
        for txt in subunit_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if subcell_texts:
        fp = 'annotations.subcellular_location'
        fields[fp] = subcell_texts
        sa_ids = []
        for txt in subcell_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if tissue_texts:
        fp = 'annotations.tissue_specificity'
        fields[fp] = tissue_texts
        sa_ids = []
        for txt in tissue_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if ptm_texts:
        fp = 'annotations.ptm'
        fields[fp] = ptm_texts
        sa_ids = []
        for txt in ptm_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    if polymorphism_texts:
        fp = 'annotations.polymorphism'
        fields[fp] = polymorphism_texts
        sa_ids = []
        for txt in polymorphism_texts:
            assertion = make_source_assertion(fp, txt, 'UniProt', primary or '', retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion['id'])
        field_source_assertions[fp] = sa_ids

    # organism
    org_name = get_in(uniprot_json, ['organism', 'scientificName'])
    if org_name:
        fp = 'annotations.organism'
        fields[fp] = org_name
        assertion = make_source_assertion(fp, org_name, 'UniProt', primary or '', retrieved_at)
        source_assertions.append(assertion)
        field_source_assertions[fp] = [assertion['id']]

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
            sa_ids: List[str] = []
            for item in binding_items:
                assertion = make_source_assertion(fp, item, 'UniProt', primary or '', retrieved_at)
                source_assertions.append(assertion)
                sa_ids.append(assertion['id'])
            field_source_assertions[fp] = sa_ids

        if active_items:
            fp = 'features_positional.active_site'
            features[fp] = active_items
            sa_ids = []
            for item in active_items:
                assertion = make_source_assertion(fp, item, 'UniProt', primary or '', retrieved_at)
                source_assertions.append(assertion)
                sa_ids.append(assertion['id'])
            field_source_assertions[fp] = sa_ids

        if modified_items:
            fp = 'features_positional.modified_residue'
            features[fp] = modified_items
            sa_ids = []
            for item in modified_items:
                assertion = make_source_assertion(fp, item, 'UniProt', primary or '', retrieved_at)
                source_assertions.append(assertion)
                sa_ids.append(assertion['id'])
            field_source_assertions[fp] = sa_ids

        if glyco_items:
            fp = 'features_positional.glycosylation'
            features[fp] = glyco_items
            sa_ids = []
            for item in glyco_items:
                assertion = make_source_assertion(fp, item, 'UniProt', primary or '', retrieved_at)
                source_assertions.append(assertion)
                sa_ids.append(assertion['id'])
            field_source_assertions[fp] = sa_ids

        if disulfide_items:
            fp = 'features_positional.disulfide_bond'
            features[fp] = disulfide_items
            sa_ids = []
            for item in disulfide_items:
                assertion = make_source_assertion(fp, item, 'UniProt', primary or '', retrieved_at)
                source_assertions.append(assertion)
                sa_ids.append(assertion['id'])
            field_source_assertions[fp] = sa_ids

    return {'fields': fields, 'features': features, 'source_assertions': source_assertions, 'field_source_assertions': field_source_assertions}
