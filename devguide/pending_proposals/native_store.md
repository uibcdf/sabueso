---
summary: A native read/write store for Sabueso (normalized SQLite), with JSON/JSONL kept as the exchange format.
issue: uibcdf/sabueso#27
status: open
opened: 2026-09-23
closed:
verification: measured
area: [persistence, relationships, identity, scale]
blocked_by: []
supersedes: []
---

# Native read/write store

## What

Sabueso works in memory: `Card` and `Deck` are Python objects, and JSON, JSONL and SQLite are used to store them and get them back. Each card is stored as one JSON document, and a SQLite row holds that same document as a blob.

This proposal is a native **read/write store**: SQLite with a normalized schema, where cards, SourceAssertions, Relationships and decks are rows. JSON/JSONL remain the **exchange format**: diffable, versionable in git, readable by eye, and easy to share with other MOLI components.

It is not a file-format change. It decides where relationships live, which is the question of uibcdf/sabueso#19, and it gives versions and snapshots (uibcdf/sabueso#7) a natural place.

## How / evidence

State on 2026-09-23:

- **Card size.** A TcTIM ProteinCard grows from about 37 KB to about 1.0 MB of compact JSON when its 493 ChEMBL bioactivities are added. That is about 2 KB per measurement (`devguide/CARD_SIZE_RISKS.md`). The whole document is rewritten on every save.
- **Inverse navigation.** Relationships live with their subject card, so "which proteins was this molecule measured on?" needs every protein card loaded and scanned. It was deferred in uibcdf/sabueso#23 (`devguide/archive/chembl_bioactivities.md`).
- **Duplication.** A SourceAssertion or relationship cited by two cards is stored twice, and a card in two decks is stored twice.
- **Deduplication inside a card.** The assay record shared by many activities is already stated once per assay (#23), but only inside that card.
- **Persistence layout.**
  - Card SQLite appends a row per save and loads the latest row per `card_id`. There is no way to address a revision (#7).
  - Deck SQLite now holds one deck per table, with its meta in `deck_meta` (#26).
- **SQLite JSON functions.** The local Python builds link SQLite 3.50–3.53, and `json_extract` works. SQLite includes the JSON functions by default since 3.38.

## Why

The traces Sabueso keeps (every SourceAssertion, every measurement with its assay and document, every derivation) are its value, and they are what makes cards large.

- A single-document card forces a choice between dropping traces and paying the full cost on every read and write.
- A normalized store keeps every trace and reads only what a question needs.
- It also turns the graph operations of `devguide/SCIENTIFIC_POTENTIAL.md` into queries: neighbours, joins between decks, inverse navigation.

## Alternatives

1. **Normalized SQLite (proposed).**
   - Partial, transactional reads and writes; indexed queries; deduplication.
   - Qualifiers and verbatim source records stay JSON columns, which `json_extract` can query.
   - It is in the Python standard library, and the file opens in any SQLite tool.
2. **HDF5.** Rejected for Sabueso.
   - It is built for large homogeneous numeric arrays (trajectories, coordinates, matrices), with chunking and compression. Sabueso's data is nested, heterogeneous and mostly text.
   - JSON strings stored in datasets add a dependency and nothing else. Dicts mapped to groups and attributes produce many tiny objects that are slow and hard to evolve.
   - It has no indices or queries. Deleting or rewriting in place fragments the file, and space is not reclaimed without repacking.
   - It allows one writer and has no transactions, so a crash mid-write can corrupt the file.
   - It is the natural format on the modelling side (MolSysSuite), consistent with the boundary in `devguide/DECISIONS.md` ("Computable properties are recorded, not computed").
3. **Parquet / DuckDB.** Excellent for column-oriented analysis, but designed for data written once and not modified. It could be a derived, read-only analytical layer if volumes reach millions of measurements, but not the working store.
4. **A document database or graph database.** It adds a server or a heavy dependency for problems SQLite already covers at the expected scale. Reconsider only if graph traversals become the dominant workload.
5. **Keep single-document cards.** Simplest. It does not address size, inverse navigation, duplication or versions.

## Proposed schema (sketch, to be refined)

```
cards(card_id PK, entity_type, schema_version, sections JSON, quality JSON, updated_at)
source_assertions(sa_id PK, subject_ref, field_path, source, record_id, version,
                  retrieved_at, asserted_value JSON, normalized_value JSON, source_metadata JSON)
card_assertions(card_id, sa_id)
relationships(rel_id PK, subject_ref, predicate, object_ref, qualifiers JSON, derivation JSON)
relationship_support(rel_id, sa_id)
decks(deck_id PK, kind, meta JSON)
deck_cards(deck_id, card_id, position)
-- indices: (subject_ref, predicate), (object_ref, predicate), (subject_ref, field_path)
```

- SourceAssertion ids (`SA_…`) and relationship ids (`REL_…`) are already deterministic. That makes them natural primary keys and makes deduplication free.
- `Card`, `Deck` and their views keep working in memory. The store loads a card with the SourceAssertions and relationships it references, or only a slice of them.

## Risks and future problems

- **Versions and snapshots.** How a pinned card version (#7) maps to rows: content hashing or timestamped revisions. This is a local Sabueso decision; uibcdf/moli#3 reviews only the public reference form and consumer-facing guarantees before other components adopt them.
- **Where resolved fields live.** Keeping `sections` as JSON is simpler. Making them rows allows querying resolved values across cards. Decide once real queries exist.
- **Migration.** Existing JSON/JSONL files must import losslessly, and export must round-trip. Tests should compare `Card.to_dict()` before and after.
- **SQLite versions.** Some platforms build Python against an older system SQLite. JSON functions must be checked in CI on Python 3.11–3.14, or the store must avoid them in required paths.
- **Concurrency.** SQLite has one writer at a time. That is fine for a local knowledge store, but not for many concurrent writers.
- **Shared contract.** If Nextia or the MOLI Agent read the store directly, its schema becomes a cross-component contract to raise in `uibcdf/moli`. Until then, it is Sabueso's implementation detail behind `Card`/`Deck`.

## Acceptance criteria

To be agreed before implementation. At least:

- lossless round trip between the store and JSON/JSONL for protein cards, molecule cards and decks;
- inverse navigation (object → subjects) through an indexed query, tested on the TIM fixtures;
- a SourceAssertion or relationship shared by two cards stored once;
- the chosen answers to the risks above recorded in `devguide/DECISIONS.md` and `devguide/STORAGE_LAYOUT.md`.

## Resolution

Pending.
