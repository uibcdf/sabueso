"""GO Consortium → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def _extract_terms(go_json: Dict[str, Any]) -> List[Dict[str, str]]:
    terms: List[Dict[str, str]] = []

    if "terms" in go_json and isinstance(go_json["terms"], list):
        for t in go_json["terms"]:
            term_id = t.get("id") or t.get("go_id")
            name = t.get("name") or t.get("label")
            if term_id and name:
                terms.append({"id": term_id, "name": name})
        return terms

    # single-term GO API shape
    term_id = go_json.get("id") or go_json.get("go_id") or go_json.get("goid")
    name = go_json.get("label") or go_json.get("name")
    if term_id and name:
        terms.append({"id": term_id, "name": name})

    return terms


def map_go_terms(go_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map GO terms into canonical annotations.go_terms."""
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    terms = _extract_terms(go_json)
    if terms:
        fp = "annotations.go_terms"
        fields[fp] = terms
        sa_ids: List[str] = []
        for term in terms:
            assertion = make_source_assertion(fp, term, "GO", term["id"], retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
