"""InterPro → ProteinCard mappings (minimal)."""

from __future__ import annotations
from typing import Any, Dict, List

from sabueso.core.evidence_store import generate_evidence_id


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
    accession = interpro_json.get("accession")
    name = None
    if "metadata" in interpro_json and isinstance(interpro_json["metadata"], dict):
        name = interpro_json["metadata"].get("name")
    if accession and name:
        domains.append({"id": accession, "name": name})

    return domains


def map_interpro_domains(interpro_json: Dict[str, Any], retrieved_at: str) -> Dict[str, Any]:
    """Map InterPro domains into canonical annotations.domains."""
    fields: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    domains = _extract_domains(interpro_json)
    if domains:
        fp = "annotations.domains"
        fields[fp] = domains
        ev_ids: List[str] = []
        for dom in domains:
            ev = {
                "field": fp,
                "value": dom,
                "source": {"type": "database", "name": "InterPro", "record_id": dom["id"]},
                "retrieved_at": retrieved_at,
            }
            ev_id = generate_evidence_id("InterPro", dom["id"], fp, dom)
            ev["evidence_id"] = ev_id
            evidences.append(ev)
            ev_ids.append(ev_id)
        field_evidence[fp] = ev_ids

    return {"fields": fields, "evidences": evidences, "field_evidence": field_evidence}
