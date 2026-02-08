"""Minimal aggregator to build Cards from mapping outputs."""

from __future__ import annotations

from typing import Any, Dict, List

from .card import Card
from .evidence_store import EvidenceStore


def build_card_from_mapping(mapping_result: Dict[str, Any], meta: Dict[str, Any] | None = None) -> Card:
    """Build a Card from mapping outputs (fields/features/evidences)."""
    fields = mapping_result.get("fields", {})
    features = mapping_result.get("features", {})
    evidences = mapping_result.get("evidences", [])
    field_evidence = mapping_result.get("field_evidence", {})

    store = EvidenceStore()
    for ev in evidences:
        store.add(ev)

    sections: Dict[str, Any] = {}

    def set_section(path: str, value: Any, evidence_ids: List[str]) -> None:
        cur = sections
        parts = path.split(".")
        for key in parts[:-1]:
            if key not in cur or not isinstance(cur[key], dict):
                cur[key] = {}
            cur = cur[key]
        cur[parts[-1]] = {"value": value, "evidence_ids": evidence_ids}

    # regular fields
    for fp, val in fields.items():
        set_section(fp, val, field_evidence.get(fp, []))

    # features (positional)
    for fp, val in features.items():
        set_section(fp, val, field_evidence.get(fp, []))

    return Card(meta=meta or {}, sections=sections, evidence_store=store)
