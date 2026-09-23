"""SCOPe → ProteinCard mappings (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def _extract_domains(scope_json: Dict[str, Any]) -> List[Dict[str, str]]:
    domains: List[Dict[str, str]] = []

    if "data" in scope_json and isinstance(scope_json["data"], list):
        for d in scope_json["data"]:
            did = d.get("sunid") or d.get("id")
            name = d.get("name") or d.get("description")
            if did and name:
                domains.append({"id": str(did), "name": name})
        return domains

    did = scope_json.get("sunid") or scope_json.get("id")
    name = (
        scope_json.get("name")
        or scope_json.get("description")
        or scope_json.get("title")
    )
    if did and name:
        domains.append({"id": str(did), "name": name})

    return domains


def map_scope_domains(scope_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    domains = _extract_domains(scope_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        sa_ids: List[str] = []
        for dom in domains:
            assertion = make_source_assertion(fp, dom, "SCOPe", dom["id"], retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["id"])
        field_source_assertions[fp] = sa_ids

    return {
        "fields": fields,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
    }
