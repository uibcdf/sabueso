# Sabueso — Minimal Interfaces (Core)

This document defines the **minimal internal interfaces** for a stable Sabueso core.
These are contracts only (no implementation).

## Card
**Purpose:** Resolved knowledge about a single entity, linked to its SourceAssertions.

**Attributes**
- `meta: dict` (includes `card_id` and `schema_version`)
- `id: str | None` *(property: stable card reference, `meta.card_id`)*
- `sections: dict` (nested content)
- `source_assertion_store: SourceAssertionStore`
- `selection_rules: dict`
- `quality: dict`

**Methods**
- `get(field_path: str) -> Any`
- `set(field_path: str, value: Any, source_assertion_ids: list[str]) -> None`
- `extract(field_paths: list[str]) -> dict`
- `compare(other_card: Card, fields: list[str] | None = None) -> dict`
- `derive_deck(kind: str) -> Deck`
- `list_fields() -> list[str]`
- `to_dict() -> dict` *(includes `source_assertion_store`)*
- `to_deck() -> Deck`

## Deck
**Purpose:** Collection of Cards with consistent operations.

**Attributes**
- `cards: list[Card]`
- `meta: dict` (optional)

**Methods**
- `add(card: Card) -> None`
- `extend(cards: list[Card]) -> None`
- `get_card(index: int) -> Card`
- `filter(predicate: Callable[[Card], bool]) -> Deck`
- `extract(predicate: Callable[[Card], bool]) -> Deck`
- `sort(key: str) -> Deck`
- `map(fn: Callable[[Card], Any]) -> list[Any]`
- `compare(other_deck: Deck, key_fields: list[str]) -> dict`
- `summarize(fields: list[str]) -> list[dict]`
- `to_list() -> list[dict]`

## SourceAssertionStore
**Purpose:** Registry of the SourceAssertions referenced by a card. A SourceAssertion
records what an external source asserts about an entity or property.

**Attributes**
- `store: dict[str, dict]`

**Methods**
- `add(assertion: SourceAssertion) -> str` *(returns the assertion `id`)*
- `get(source_assertion_id: str) -> SourceAssertion | None`
- `find_by_field(field_path: str) -> list[SourceAssertion]`
- `to_list() -> list[SourceAssertion]` *(serialized with the card)*

## Resolver
**Purpose:** Classify inputs and normalize identifiers.

**Methods**
- `resolve(input: Any) -> dict`

**Return Contract (resolve)**
- `entity_type: str` *(protein | peptide | small_molecule)*
- `normalized_inputs: list[dict]`
- `ambiguity: bool`
- `candidates: list[dict]` *(optional)*
