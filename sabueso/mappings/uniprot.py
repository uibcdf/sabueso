"""UniProt → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import get_in


def map_protein(uniprot_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map minimal UniProt fields into canonical card fields.

    Returns a dict with:
      - fields: canonical field_path → value
      - features: canonical feature field_path → list of feature items
    Evidence objects are created upstream (not here).
    """
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}

    # identifiers
    primary = uniprot_json.get('primaryAccession')
    if primary:
        fields['identifiers.secondary_ids.uniprot'] = primary

    # canonical name
    name = get_in(uniprot_json, ['proteinDescription', 'recommendedName', 'fullName', 'value'])
    if name:
        fields['names.canonical_name'] = name

    # function (commentType == FUNCTION)
    comments = uniprot_json.get('comments', []) or []
    func_texts: List[str] = []
    for c in comments:
        if c.get('commentType') == 'FUNCTION':
            for t in c.get('texts', []) or []:
                v = t.get('value')
                if v:
                    func_texts.append(v)
    if func_texts:
        fields['uniprot_comments.function'] = func_texts

    # binding sites (features)
    feat_items = []
    for f in uniprot_json.get('features', []) or []:
        if f.get('type') == 'Binding site':
            loc = f.get('location', {}) or {}
            start = get_in(loc, ['start', 'value'])
            end = get_in(loc, ['end', 'value'])
            if start is not None:
                feat_items.append({
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
                })
    if feat_items:
        features['features_positional.binding_site'] = feat_items

    return {'fields': fields, 'features': features}
