"""TED → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def _extract_domains(ted_json: Dict[str, Any]) -> List[Dict[str, str]]:
    domains: List[Dict[str, str]] = []

    if "domains" in ted_json and isinstance(ted_json["domains"], list):
        for d in ted_json["domains"]:
            did = d.get("id") or d.get("accession")
            name = d.get("name") or d.get("label")
            if did and name:
                domains.append({"id": did, "name": name})
        return domains

    did = ted_json.get("id") or ted_json.get("accession")
    name = ted_json.get("name") or ted_json.get("label")
    if did and name:
        domains.append({"id": did, "name": name})

    return domains


def map_ted_domains(ted_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    domains = _extract_domains(ted_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        sa_ids: List[str] = []
        for dom in domains:
            assertion = make_source_assertion(fp, dom, "TED", dom["id"], retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["source_assertion_id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
