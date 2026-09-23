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
silent choices. Contract: `devguide/archive/entity_resolver.md` (#6).
Implemented in `sabueso/resolver/entity_resolver.py` for UniProt accessions and protein
name + organism searches (MVP steps 2–3).

**Methods**
- `EntityResolver(uniprot_client=None, policy="prefer_reviewed@1", rcsb_client=None)`
  *(RCSB defaults to `OnlineRCSBClient`; `FixtureRCSBClient` serves saved GraphQL
  entries)* *(UniProt defaults to
  `OnlineUniProtClient`; `FixtureUniProtClient` serves saved REST responses; `policy=None`
  disables preferences so several matches stay ambiguous)*
- `resolve(query: EntityQuery | str) -> EntityResolution`
- `sequence_identity_link(entry_a, entry_b) -> Relationship | None` *(derived
  `possibly_same_as` for identical sequences within one organism; never across organisms)*

**EntityQuery**
- `identifier` *(e.g. `P60174`, `uniprot:P60174-3`, `pdb:1TCD`)*
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
- `related`: for a PDB entry, the protein entities its polymer entities map to
  (`[{entity_ref, predicate: has_structure, polymer_entities}]`)
- `decision`: rules applied, sources consulted (with outcome or retrieval time), query,
  Sabueso version

## ProteinCards from resolved entities
Implemented in `sabueso/tools/card/protein.py` (#6, step 4c); exported at package root.
- `resolve_protein_card(query, resolver=None, structures=(), string=None, string_client=None) -> (Card | None, EntityResolution)`:
  - builds the card of the resolved protein entity; the card is `None` when the query did
    not resolve to a protein;
  - only assertions about the entity (anchor record plus `same_as` records) feed fields,
    enforced through `build_card_from_mapping(..., entity_subjects=...)`;
  - identity links become relationships;
  - `structures=[...]` or `"all"` enriches `has_structure` with RCSB data;
  - `string={...}` (e.g. `{"required_score": 700, "limit": 50}`) adds STRING
    `functionally_associated_with` relationships for the entry's organism;
  - every enrichment outcome (`added`, `not_found`, `error`) is recorded in
    `quality.enrichments`, and a failed enrichment never prevents the card;
  - the resolution trace goes to `quality.entity_resolution`.
- `ambiguity_deck(resolution) -> Deck`: light candidate cards (UniProt accession,
  organism, length) for the candidates of an ambiguous resolution, or for the alternatives
  of a preference. `deck.meta.kind` is `entity_ambiguity` or `entity_alternatives`.
  Nothing is fetched again.

## FieldResolver
See `devguide/RESOLVER.md` (`resolve_field`).
