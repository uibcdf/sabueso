"""Minimal aggregator to build Cards from mapping outputs."""

from __future__ import annotations

from typing import Any, Dict, List

from .card import CARD_SCHEMA_VERSION, Card, make_card_id
from .source_assertion_store import SourceAssertionStore
from sabueso.resolver import resolve_field

# Identifier fields whose subject identifies the card, in order of preference.
PRIMARY_IDENTIFIER_FIELDS = (
    "identifiers.uniprot",
    "identifiers.chembl",
    "identifiers.pubchem",
    "identifiers.pdb",
)


def _derive_card_id(
    store: SourceAssertionStore,
    field_source_assertions: Dict[str, List[str]],
    entity_type: str,
) -> str | None:
    """Derive a stable card id from the subject of the primary identifier assertion."""
    candidates: List[str] = []
    for fp in PRIMARY_IDENTIFIER_FIELDS:
        candidates.extend(field_source_assertions.get(fp, []))
    candidates.extend(sa_id for sa_ids in field_source_assertions.values() for sa_id in sa_ids)
    for sa_id in candidates:
        assertion = store.get(sa_id)
        if assertion and assertion.get("subject_ref"):
            return make_card_id(entity_type, assertion["subject_ref"])
    return None


def build_card_from_mapping(
    mapping_result: Dict[str, Any],
    meta: Dict[str, Any] | None = None,
    selection_rules: Dict[str, Any] | None = None,
    mode: str = "strict",
    card_id: str | None = None,
) -> Card:
    """Build a Card from mapping outputs (fields/features/source_assertions).

    If selection_rules are provided, each field is resolved via the resolver from its
    SourceAssertions; alternative or conflicting assertions stay in the store and in
    ``quality.conflicts``.

    The card receives a stable ``meta.card_id``: the given ``card_id``, or one derived
    from the subject of its primary identifier assertion (e.g.
    ``sabueso:protein:uniprot:P52789``).
    """

    fields = mapping_result.get("fields", {})
    features = mapping_result.get("features", {})
    source_assertions = mapping_result.get("source_assertions", [])
    field_source_assertions = mapping_result.get("field_source_assertions", {})

    store = SourceAssertionStore(source_assertions)

    meta = dict(meta or {})
    meta.setdefault("schema_version", CARD_SCHEMA_VERSION)
    resolved_card_id = card_id or meta.get("card_id")
    if resolved_card_id is None:
        resolved_card_id = _derive_card_id(store, field_source_assertions, meta.get("entity_type", ""))
    if resolved_card_id is not None:
        meta["card_id"] = resolved_card_id

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

    card = Card(meta=meta, sections=sections, source_assertion_store=store, selection_rules=selection_rules or {})
    if conflicts:
        card.quality.setdefault("conflicts", []).extend(conflicts)

    return card
