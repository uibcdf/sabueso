"""SCOPe → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


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
    name = scope_json.get("name") or scope_json.get("description") or scope_json.get("title")
    if did and name:
        domains.append({"id": str(did), "name": name})

    return domains


def map_scope_domains(scope_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    domains = _extract_domains(scope_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        ev_ids: List[str] = []
        for dom in domains:
            ev = {
                "field": fp,
                "value": dom,
                "source": {"type": "database", "name": "SCOPe", "record_id": dom["id"]},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("SCOPe", dom["id"], fp, dom)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
