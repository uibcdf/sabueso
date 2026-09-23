# Core Concepts

Sabueso uses a small set of core concepts to convert heterogeneous source data
into auditable molecular objects.

## Card

A `Card` represents one molecular entity (protein, peptide, or small molecule). It has
a stable reference, `card.id` (`meta.card_id`, e.g. `sabueso:protein:uniprot:P52789`),
that does not depend on where the card is stored. Each field is stored in a structured
node:

```text
{"value": <selected_value>, "source_assertion_ids": [<source_assertion_id>, ...]}
```

Cards expose core methods such as:

- `get(field_path)`
- `extract(field_paths)`
- `compare(other, fields=None, mode="strict|tolerant")`
- `to_dict()`, `to_json(path)`, `to_sqlite(path, ...)`
- `from_json(path)`, `from_sqlite(path, ...)`

## Deck

A `Deck` is a collection of Cards with batch operations:

- `filter(predicate)`
- `extract(predicate)` for sub-decks
- `compare(other, key_fields, mode="strict|tolerant")`
- `to_jsonl(path)`, `to_sqlite(path, ...)`
- `from_jsonl(path)`, `from_sqlite(path, ...)`

## SourceAssertion

A `SourceAssertion` records what an external source asserts about an entity or
property: the asserted value, the field it refers to, the source and record it comes
from, and when it was retrieved:

```text
{"id": "SA_UniProt_P52789_...",
 "subject_ref": "uniprot:P52789",
 "field_path": "annotations.organism",
 "asserted_value": "Homo sapiens",
 "source": {"type": "database", "name": "UniProt", "record_id": "P52789"},
 "retrieved_at": "2026-02-01"}
```

A SourceAssertion is not scientific *evidence* for a hypothesis (that concept belongs to
Nextia, the Discovery context of the MOLI Platform) and it is not provenance in general. It is an
external knowledge claim that carries its own provenance. Qualifiers the source attaches
to its own statements (for example, UniProt ECO codes) are kept as source metadata.

## SourceAssertionStore

The `SourceAssertionStore` holds every SourceAssertion referenced by
`source_assertion_ids`. Sabueso keeps all assertions, including alternative or
contradictory ones, and only selects canonical values for Card fields. This separates:

- field readability (resolved values in the Card)
- traceability (every source assertion in the store, serialized with the Card)

## Resolver

The Resolver turns the SourceAssertions of each field into resolved molecular
knowledge. Its output contains:

- `selected_value`
- `source_assertion_ids` (the assertions that support the selected value)
- `conflict` (when assertions disagree; the alternatives stay in the store)

Conflicts are always reported when there is a discrepancy.

## Selection Rules

Selection behavior is controlled by versioned rules (`x.y.z`), including:

- priority source order
- per-field strategy (for example, `most_recent` or `priority_sources`)
- whether a field allows multiple selected values

## Pipeline

The operational flow is:

```text
source payloads
  -> mappings
  -> merge
  -> resolver
  -> card/deck
```

This pipeline preserves traceability while producing canonical outputs for downstream tools.

## Field Paths

Sabueso uses canonical dot-separated field paths (for example,
`identifiers.uniprot` or `features_positional.binding_site`).
See {doc}`field_paths`.

## Storage Model

Sabueso supports in-memory work by default and explicit persistence by user choice.
Recommended project layout and storage tradeoffs are documented in {doc}`storage`.

