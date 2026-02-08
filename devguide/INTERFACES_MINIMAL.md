# Sabueso — Minimal Interfaces (Core)

This document defines the **minimal internal interfaces** for a stable Sabueso core.
These are contracts only (no implementation).

## Card
**Purpose:** Single entity representation with evidence links.

**Attributes**
- `meta: dict`
- `sections: dict` (nested content)
- `evidence_store: EvidenceStore`
- `selection_rules: dict`
- `quality: dict`

**Methods**
- `get(field_path: str) -> Any`
- `set(field_path: str, value: Any, evidence_ids: list[str]) -> None`
- `extract(field_paths: list[str]) -> dict`
- `compare(other_card: Card, fields: list[str] | None = None) -> dict`
- `derive_deck(kind: str) -> Deck`
- `list_fields() -> list[str]`
- `to_dict() -> dict`
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

## EvidenceStore
**Purpose:** Registry of evidence objects referenced by cards.

**Attributes**
- `store: dict[str, dict]`

**Methods**
- `add(evidence: dict) -> str` *(returns evidence_id)*
- `get(evidence_id: str) -> dict | None`
- `find_by_field(field_path: str) -> list[dict]`

## Resolver
**Purpose:** Classify inputs and normalize identifiers.

**Methods**
- `resolve(input: Any) -> dict`

**Return Contract (resolve)**
- `entity_type: str` *(protein | peptide | small_molecule)*
- `normalized_inputs: list[dict]`
- `ambiguity: bool`
- `candidates: list[dict]` *(optional)*
