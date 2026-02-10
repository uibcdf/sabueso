"""Merge mapping outputs into a single mapping result."""

from __future__ import annotations

from typing import Any, Dict, List


def merge_mapping_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    evidences: List[Dict[str, Any]] = []
    field_evidence: Dict[str, List[str]] = {}

    for res in results:
        for fp, val in res.get("fields", {}).items():
            fields[fp] = val
        for fp, val in res.get("features", {}).items():
            features[fp] = val
        for ev in res.get("evidences", []):
            evidences.append(ev)
        for fp, ev_ids in res.get("field_evidence", {}).items():
            field_evidence.setdefault(fp, []).extend(ev_ids)

    return {
        "fields": fields,
        "features": features,
        "evidences": evidences,
        "field_evidence": field_evidence,
    }
