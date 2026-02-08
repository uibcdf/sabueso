"""CATH → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


def _extract_domains(cath_json: Dict[str, Any]) -> List[Dict[str, str]]:
    domains: List[Dict[str, str]] = []

    if "data" in cath_json and isinstance(cath_json["data"], list):
        for d in cath_json["data"]:
            did = d.get("domain_id") or d.get("id")
            name = d.get("name") or d.get("description")
            if did and name:
                domains.append({"id": did, "name": name})
        return domains

    if "data" in cath_json and isinstance(cath_json["data"], dict):
        d = cath_json["data"]
        did = d.get("domain_id") or d.get("id")
        name = d.get("cath_id") or d.get("superfamily_id")
        if did and name:
            domains.append({"id": did, "name": name})
        return domains

    # single-domain shape
    did = cath_json.get("domain_id") or cath_json.get("id")
    name = cath_json.get("name") or cath_json.get("description")
    if did and name:
        domains.append({"id": did, "name": name})

    return domains


def map_cath_domains(cath_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    domains = _extract_domains(cath_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        ev_ids: List[str] = []
        for dom in domains:
            ev = {
                "field": fp,
                "value": dom,
                "source": {"type": "database", "name": "CATH", "record_id": dom["id"]},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("CATH", dom["id"], fp, dom)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
