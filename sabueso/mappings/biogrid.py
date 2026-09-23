"""BioGRID → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


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
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

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
        sa_ids: List[str] = []
        for p in partners:
            assertion = make_source_assertion(fp, p, "BioGRID", query_name, retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["source_assertion_id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
