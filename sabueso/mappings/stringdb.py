"""STRING → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


def map_string_interactions(string_json: List[Dict[str, Any]], query_name: str, retrieved_at: str) -> Dict[str, Any]:
    """Map STRING network JSON into interactions.binding_partners."""
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    partners: List[str] = []
    for row in string_json or []:
        a = row.get("preferredName_A") or row.get("stringId_A")
        b = row.get("preferredName_B") or row.get("stringId_B")
        if not a or not b:
            continue
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
                "source": {"type": "database", "name": "STRING", "record_id": query_name},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("STRING", query_name, fp, p)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
