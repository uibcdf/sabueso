"""PhosphoSitePlus → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


def map_psp_ptm(psp_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map PTMs to features_positional.modified_residue."""
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

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
        ev_ids: List[str] = []
        for item in features:
            ev = {
                "field": fp,
                "value": item,
                "source": {"type": "database", "name": "PhosphoSitePlus", "record_id": "PTM"},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("PhosphoSitePlus", "PTM", fp, item)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
