"""Minimal aggregator to build Cards from mapping outputs."""

from __future__ import annotations

from typing import Any, Dict, List

from .card import Card
from .evidence_store import EvidenceStore
from sabueso.resolver import resolve_field


def build_card_from_mapping(
    mapping_result: Dict[str, Any],
    meta: Dict[str, Any] | None = None,
    selection_rules: Dict[str, Any] | None = None,
    mode: str = "strict",
) -> Card:
    """Build a Card from mapping outputs (fields/features/evidences).

    If selection_rules are provided, fields are resolved via the resolver.
    """

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

    # Helper: resolve field value if rules provided
    def resolve_value(fp: str, val: Any) -> tuple[Any, List[str], dict | None]:
        if not selection_rules:
            return val, field_evidence.get(fp, []), None
        ev_ids = field_evidence.get(fp, [])
        evs = [store.get(eid) for eid in ev_ids if store.get(eid)]
        result = resolve_field(fp, evs, selection_rules, mode=mode)
        return result.get("selected_value"), result.get("evidence_ids", []), result.get("conflict")

    conflicts: List[Dict[str, Any]] = []

    # regular fields
    for fp, val in fields.items():
        resolved_val, ev_ids, conflict = resolve_value(fp, val)
        set_section(fp, resolved_val, ev_ids)
        if conflict:
            conflicts.append({"field": fp, **conflict})

    # features (positional)
    for fp, val in features.items():
        resolved_val, ev_ids, conflict = resolve_value(fp, val)
        set_section(fp, resolved_val, ev_ids)
        if conflict:
            conflicts.append({"field": fp, **conflict})

    card = Card(meta=meta or {}, sections=sections, evidence_store=store, selection_rules=selection_rules or {})
    if conflicts:
        card.quality.setdefault("conflicts", []).extend(conflicts)

    return card
