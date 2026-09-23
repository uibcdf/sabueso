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
- `relationship_store: RelationshipStore`
- `selection_rules: dict`
- `quality: dict`

**Methods**
- `get(field_path: str) -> Any`
- `set(field_path: str, value: Any, source_assertion_ids: list[str]) -> None`
- `extract(field_paths: list[str]) -> dict`
- `compare(other_card: Card, fields: list[str] | None = None) -> dict`
- `derive_deck(kind: str) -> Deck`
- `list_fields() -> list[str]`
- `to_dict() -> dict` *(includes `source_assertion_store` and `relationship_store`)*
- `relationships(predicate=None, object_ref=None) -> list[Relationship]`
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

## RelationshipStore
**Purpose:** Registry of the Relationships carried by a card (subject side). See the
Relationship contract in `devguide/SCHEMA.md`.

**Methods**
- `add(relationship: Relationship) -> str` *(merges support for an existing id; records
  `qualifier_conflicts`)*
- `get(relationship_id: str) -> Relationship | None`
- `find(subject_ref=None, predicate=None, object_ref=None) -> list[Relationship]`
- `to_list() -> list[Relationship]` *(serialized with the card)*

Helpers: `make_relationship(...)` validates the predicate and requires support;
`make_derivation(rule, inputs, parameters)` builds the derivation record for inferred
relationships.

## EntityResolver
**Purpose:** Decide which molecular entity an identifier or query refers to, without
silent choices. Contract: `devguide/pending_proposals/entity_resolver.md` (#6).
Implemented in `sabueso/resolver/entity_resolver.py` for UniProt accessions and protein
name + organism searches (MVP steps 2–3).

**Methods**
- `EntityResolver(uniprot_client=None, policy="prefer_reviewed@1")` *(defaults to
  `OnlineUniProtClient`; `FixtureUniProtClient` serves saved REST responses; `policy=None`
  disables preferences so several matches stay ambiguous)*
- `resolve(query: EntityQuery | str) -> EntityResolution`
- `sequence_identity_link(entry_a, entry_b) -> Relationship | None` *(derived
  `possibly_same_as` for identical sequences within one organism; never across organisms)*

**EntityQuery**
- `identifier` *(e.g. `P60174`, `uniprot:P60174-3`)*
- `name`, `organism` *(taxon id or scientific name; required with `name`)*,
  `include_subtaxa` *(also match strains/subtaxa of the organism)*, `entity_type`

**EntityResolution**
- `status`: `resolved | ambiguous | not_found | unsupported | error`
- `entity_ref`: e.g. `sabueso:protein:uniprot:P60174`
- `qualifiers`: e.g. `{"isoform": "P60174-3"}`
- `candidates`: when ambiguous, `[{entity_ref, basis}]`
- `alternatives`: non-chosen candidates when resolved
- `policy`: named preference policy, when one was applied
- `identity_links`: Relationships (`same_as`, `superseded_by`, `isoform_of`)
- `source_assertions`: the UniProt SourceAssertions supporting those links
- `decision`: rules applied, sources consulted (with outcome or retrieval time), query,
  Sabueso version

## FieldResolver
See `devguide/RESOLVER.md` (`resolve_field`).
