# Core Concepts

Sabueso uses a small set of core concepts to convert heterogeneous source data
into auditable molecular objects.

## Card

A `Card` represents one molecular entity (protein, peptide, or small molecule).
Each field is stored in a structured node:

```text
{"value": <selected_value>, "evidence_ids": [<evidence_id>, ...]}
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

## EvidenceStore

The `EvidenceStore` holds raw evidences referenced by `evidence_ids`.
Sabueso keeps all available evidence values and only selects canonical values for
Card fields. This separates:

- field readability (selected values in Card)
- provenance completeness (all values in evidence store)

## Resolver

The Resolver selects canonical values per field from evidence sets.
Its output contains:

- `selected_value`
- `evidence_ids`
- `conflict` (when multiple distinct values exist)

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

