"""InterPro → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.source_assertion_store import make_source_assertion


def _extract_domains(interpro_json: Dict[str, Any]) -> List[Dict[str, str]]:
    domains: List[Dict[str, str]] = []

    if "domains" in interpro_json and isinstance(interpro_json["domains"], list):
        for d in interpro_json["domains"]:
            did = d.get("id") or d.get("accession")
            name = d.get("name") or d.get("label")
            if did and name:
                domains.append({"id": did, "name": name})
        return domains

    # InterPro entry API shape (metadata)
    metadata = interpro_json.get("metadata") if isinstance(interpro_json.get("metadata"), dict) else None
    accession = None
    name = None
    if metadata:
        accession = metadata.get("accession")
        name_obj = metadata.get("name")
        if isinstance(name_obj, dict):
            name = name_obj.get("name") or name_obj.get("short")
        elif isinstance(name_obj, str):
            name = name_obj
    if accession and name:
        domains.append({"id": accession, "name": name})

    return domains


def map_interpro_domains(interpro_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map InterPro domains into canonical annotations.domains."""
    fields: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}

    domains = _extract_domains(interpro_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        sa_ids: List[str] = []
        for dom in domains:
            assertion = make_source_assertion(fp, dom, "InterPro", dom["id"], retrieved_at)
            source_assertions.append(assertion)
            sa_ids.append(assertion["id"])
        field_source_assertions[fp] = sa_ids

    return {"fields": fields, "source_assertions": source_assertions, "field_source_assertions": field_source_assertions}
