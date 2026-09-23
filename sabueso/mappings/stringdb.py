"""STRING → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def map_string_interactions(string_json: List[Dict[str, Any]], query_name: str, retrieved_at: str) -> Dict[str, Any]:
    """Map STRING network JSON into interactions.binding_partners."""
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

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
        sa_ids: List[str] = []
        for p in partners:
            assertion = make_source_assertion(fp, p, "STRING", query_name, retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["source_assertion_id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
