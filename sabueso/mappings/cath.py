"""CATH → ProteinCard mappings (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


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
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    domains = _extract_domains(cath_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        sa_ids: List[str] = []
        for dom in domains:
            assertion = make_source_assertion(fp, dom, "CATH", dom["id"], retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["id"])
        field_source_assertions[fp] = sa_ids

    return {
        "fields": fields,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
    }
