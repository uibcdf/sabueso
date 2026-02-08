"""BioGRID → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


def _extract_partner_pairs(biogrid_json: Dict[str, Any]) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []
    if not isinstance(biogrid_json, dict):
        return pairs

    for _, rec in biogrid_json.items():
        if not isinstance(rec, dict):
            continue
        a = rec.get("OFFICIAL_SYMBOL_A") or rec.get("official_symbol_a")
        b = rec.get("OFFICIAL_SYMBOL_B") or rec.get("official_symbol_b")
        if a and b:
            pairs.append({"a": a, "b": b})
    return pairs


def map_biogrid_interactions(biogrid_json: Dict[str, Any], query_name: str, retrieved_at: str) -> Dict[str, Any]:
    """Map BioGRID interactions into interactions.binding_partners."""
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    partners: List[str] = []
    for pair in _extract_partner_pairs(biogrid_json):
        a, b = pair["a"], pair["b"]
        if a == query_name and b not in partners:
            partners.append(b)
        elif b == query_name and a not in partners:
            partners.append(a)

    if partners:
        fp = "interactions.binding_partners"
        fields[fp] = partners
        ev_ids: List[str] = []
        for p in partners:
            ev = {
                "field": fp,
                "value": p,
                "source": {"type": "database", "name": "BioGRID", "record_id": query_name},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("BioGRID", query_name, fp, p)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
