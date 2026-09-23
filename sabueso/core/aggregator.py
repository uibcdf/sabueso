"""Minimal aggregator to build Cards from mapping outputs."""

from __future__ import annotations

from typing import Any, Dict, List

from .card import Card
from .source_assertion_store import SourceAssertionStore
from sabueso.resolver import resolve_field


def build_card_from_mapping(
    mapping_result: Dict[str, Any],
    meta: Dict[str, Any] | None = None,
    selection_rules: Dict[str, Any] | None = None,
    mode: str = "strict",
) -> Card:
    """Build a Card from mapping outputs (fields/features/source_assertions).

    If selection_rules are provided, each field is resolved via the resolver from its
    SourceAssertions; alternative or conflicting assertions stay in the store and in
    ``quality.conflicts``.
    """

    fields = mapping_result.get("fields", {})
    features = mapping_result.get("features", {})
    source_assertions = mapping_result.get("source_assertions", [])
    field_source_assertions = mapping_result.get("field_source_assertions", {})

    store = SourceAssertionStore(source_assertions)

    sections: Dict[str, Any] = {}

    def set_section(path: str, value: Any, source_assertion_ids: List[str]) -> None:
        cur = sections
        parts = path.split(".")
        for key in parts[:-1]:
            if key not in cur or not isinstance(cur[key], dict):
                cur[key] = {}
            cur = cur[key]
        cur[parts[-1]] = {"value": value, "source_assertion_ids": source_assertion_ids}

    # Helper: resolve field value if rules provided
    def resolve_value(fp: str, val: Any) -> tuple[Any, List[str], dict | None]:
        if not selection_rules:
            return val, field_source_assertions.get(fp, []), None
        sa_ids = field_source_assertions.get(fp, [])
        assertions = [store.get(sa_id) for sa_id in sa_ids if store.get(sa_id)]
        result = resolve_field(fp, assertions, selection_rules, mode=mode)
        return result.get("selected_value"), result.get("source_assertion_ids", []), result.get("conflict")

    conflicts: List[Dict[str, Any]] = []

    # regular fields
    for fp, val in fields.items():
        resolved_val, sa_ids, conflict = resolve_value(fp, val)
        set_section(fp, resolved_val, sa_ids)
        if conflict:
            conflicts.append({"field": fp, **conflict})

    # features (positional)
    for fp, val in features.items():
        resolved_val, sa_ids, conflict = resolve_value(fp, val)
        set_section(fp, resolved_val, sa_ids)
        if conflict:
            conflicts.append({"field": fp, **conflict})

    card = Card(meta=meta or {}, sections=sections, source_assertion_store=store, selection_rules=selection_rules or {})
    if conflicts:
        card.quality.setdefault("conflicts", []).extend(conflicts)

    return card
