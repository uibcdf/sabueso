"""PhosphoSitePlus → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def map_psp_ptm(psp_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map PTMs to features_positional.modified_residue."""
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    items = psp_json.get("ptm", []) if isinstance(psp_json, dict) else []
    features: List[Dict[str, Any]] = []
    for it in items:
        pos = it.get("position")
        mod = it.get("modification")
        if pos is None:
            continue
        features.append({
            "location": {
                "kind": "sequence",
                "sequence": {"start": int(pos), "end": int(pos), "indexing": "1-based"},
            },
            "description": mod or "",
        })

    if features:
        fp = "features_positional.modified_residue"
        fields[fp] = features
        sa_ids: List[str] = []
        for item in features:
            assertion = make_source_assertion(fp, item, "PhosphoSitePlus", "PTM", retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
