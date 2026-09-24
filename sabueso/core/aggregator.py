"""Minimal aggregator to build Cards from mapping outputs."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from sabueso.resolver import load_selection_rules, resolve_field

from .card import CARD_SCHEMA_VERSION, Card, make_card_id
from .errors import SchemaError
from .quantities import field_node
from .relationship_store import RelationshipStore
from .source_assertion_store import SourceAssertionStore, assertion_value

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
    fields: Dict[str, Any] | None = None,
) -> str | None:
    """Derive a stable card id from the subject of the primary identifier assertion.

    A small molecule is anchored at its standard InChIKey whatever the source, never at a
    source record (uibcdf/sabueso#25). Without one it has no anchor, and no id.
    """
    if entity_type == "small_molecule":
        from sabueso.mappings.molecule_identity import anchor_ref, is_standard_inchikey

        key = (fields or {}).get("identifiers.inchikey")
        return (
            make_card_id(entity_type, anchor_ref(key))
            if is_standard_inchikey(key)
            else None
        )
    candidates: List[str] = []
    for fp in PRIMARY_IDENTIFIER_FIELDS:
        candidates.extend(field_source_assertions.get(fp, []))
    candidates.extend(
        sa_id for sa_ids in field_source_assertions.values() for sa_id in sa_ids
    )
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
    entity_subjects: Iterable[str] | None = None,
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
    # FieldResolver boundary (#6, #21): only assertions about the card's entity may feed
    # its fields. Assertions about other subjects (structures, identity-linked records)
    # may live in the store as support for relationships, never as fields.
    feeding = {
        sa_id: (store.get(sa_id) or {}).get("subject_ref")
        for fp in list(fields) + list(features)
        for sa_id in field_source_assertions.get(fp, [])
    }
    if entity_subjects is not None:
        allowed = set(entity_subjects)
        for fp in list(fields) + list(features):
            for sa_id in field_source_assertions.get(fp, []):
                if feeding[sa_id] not in allowed:
                    raise SchemaError(
                        f"Field {fp} would be fed by {sa_id} about {feeding[sa_id]}, "
                        f"outside the card entity {sorted(allowed)}"
                    )
    else:
        # Guard by default: records about several subjects are merged into one card only
        # after their identity is resolved (resolve_protein_card, build_molecule_cards),
        # which then passes ``entity_subjects``. A false entity merge is worse than an
        # unresolved conflict (devguide/SCIENTIFIC_POTENTIAL.md).
        subjects = {subject for subject in feeding.values() if subject}
        if len(subjects) > 1:
            raise SchemaError(
                f"Fields are fed by assertions about several subjects {sorted(subjects)}. "
                "Resolve their identity and pass entity_subjects."
            )
    relationship_store = RelationshipStore(mapping_result.get("relationships", []))
    for relationship in relationship_store.to_list():
        missing = [
            sa_id
            for sa_id in relationship.get("source_assertion_ids", [])
            if store.get(sa_id) is None
        ]
        if missing:
            raise SchemaError(
                f"Relationship {relationship['id']} cites unknown SourceAssertions: {missing}"
            )

    meta = dict(meta or {})
    meta.setdefault("schema_version", CARD_SCHEMA_VERSION)
    resolved_card_id = card_id or meta.get("card_id")
    if resolved_card_id is None:
        resolved_card_id = _derive_card_id(
            store, field_source_assertions, meta.get("entity_type", ""), fields
        )
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
        cur[parts[-1]] = field_node(path, value, source_assertion_ids)

    # Helper: resolve field value if rules provided
    # Every field is resolved from its assertions, with the packaged default rules when
    # none are given. A field stated by several sources never takes the last one merged
    # while citing them all (uibcdf/sabueso#10).
    rules = selection_rules or load_selection_rules()
    alternatives: List[Dict[str, Any]] = []

    def resolve_value(fp: str, val: Any) -> tuple[Any, List[str], dict | None]:
        sa_ids = field_source_assertions.get(fp, [])
        assertions = [store.get(sa_id) for sa_id in sa_ids if store.get(sa_id)]
        if not assertions:
            return val, sa_ids, None
        if isinstance(val, list) and not any(
            isinstance(a.get("asserted_value"), list) for a in assertions
        ):
            # An itemised field: each assertion states one item (a location, a site, a
            # reaction). Items do not compete; the field is their union, each traced.
            items: Dict[str, Any] = {}
            for a in assertions:
                item = assertion_value(a)
                items.setdefault(json.dumps(item, sort_keys=True, default=str), item)
            return list(items.values()), [a["id"] for a in assertions], None
        result = resolve_field(fp, assertions, rules, mode=mode)
        if result.get("alternatives"):
            alternatives.append({"field": fp, **result["alternatives"]})
        return (
            result.get("selected_value"),
            result.get("source_assertion_ids", []),
            result.get("conflict"),
        )

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

    card = Card(
        meta=meta,
        sections=sections,
        source_assertion_store=store,
        selection_rules=rules,  # the rules actually applied, defaults included
        relationship_store=relationship_store,
    )
    if conflicts:
        card.quality.setdefault("conflicts", []).extend(conflicts)
    if alternatives:
        card.quality.setdefault("alternatives", []).extend(alternatives)

    return card
