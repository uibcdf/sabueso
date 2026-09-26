# Storage

Sabueso is designed for in-memory work first, with explicit persistence when the
user decides to save artifacts in a project directory.

## Supported Formats

- **Card**:
  - JSON
  - SQLite
- **Deck**:
  - JSONL (one Card per line)
  - SQLite

## API Methods

Card persistence:

- `card.to_json(path)`
- `card.to_sqlite(path, table='cards', id_field=None)`
- `Card.from_json(path)`
- `Card.from_sqlite(path, table='cards', card_id=None)`

Deck persistence:

- `deck.to_jsonl(path)`
- `deck.to_sqlite(path, table='cards', id_field=None)`
- `Deck.from_jsonl(path)`
- `Deck.from_sqlite(path, table='cards')`

## Knowledge Store: Versioned Cards

To keep cards over time and cite the exact state you used, save them in a knowledge
store. It is one SQLite file:

```python
import sabueso

store = sabueso.KnowledgeStore("project/knowledge.db")
ref = store.save(card, note="baseline for the docking run")
# 'sabueso:protein:uniprot:P52270@sha256:3b1f…' pins this exact state

store.load(ref)  # exactly that state, or StorageError
store.load(card.id)  # the latest state saved for the card
store.history(card.id)  # every revision: reference, time, note

# Which stored proteins was this molecule measured on?
store.relationships(object_ref="chembl:CHEMBL1288605", predicate="has_bioactivity")
```

- A snapshot id is the content address of the card. `card.snapshot_id()` and
  `card.pinned_ref()` compute it without a store, so a JSON copy of a card can be
  checked against a reference.
- A pinned reference never resolves to another state of the card. If that state is not
  in the store, you get a `StorageError`.
- An assertion or relationship is cited within a pinned state:
  `store.source_assertion(f"{ref}#SA_…")`.
- Decks are versioned too. `store.save_deck(deck, "ligands")` returns
  `sabueso:deck:ligands@sha256:…`. `store.load_deck("ligands")` gives the latest
  revision, and `store.load_deck(ref)` the exact one, each card in the state it was
  saved in. `store.deck_history("ligands")` lists the revisions.
- To bring in cards saved earlier with `card.to_sqlite`, use
  `store.import_card_table(path)`. Each row becomes a revision.

The reference forms are provisional until they are agreed across MOLI (uibcdf/moli#3).

## Old Cards

Cards written by older versions are read, or migrated with what they lack reported; see
{doc}`upgrading`.

## What Sabueso stores

- **Cards and decks**, in the knowledge store or in files, where you choose. There are
  no default paths.
- **Curated statements**, in a curation store ({doc}`literature_and_curation`).
- **Not the raw source records.** Each SourceAssertion keeps what was taken from a
  record: the source, its release, the record id, the retrieval date and the asserted
  value. To keep raw records yourself, use the `get_*` functions
  ({doc}`tools/db/sources`), and check each source's terms before redistributing them.

## Recommended Project Layout

```text
project_root/
  data/
    knowledge.db        # KnowledgeStore: cards and decks with their revisions
    curation.jsonl      # CurationStore: curated statements, kept across rebuilds
    raw/                # optional: raw source records you keep yourself
    exports/            # optional: JSON/JSONL/SQLite files to share
```

The developer guide explains the reasons (`devguide/STORAGE_LAYOUT.md`,
`devguide/CACHE_POLICY.md`).

## Tradeoffs

- JSON/JSONL: easiest to inspect and diff.
- SQLite: best for larger collections and query performance.
- Knowledge store: the place to keep cards you will cite, with their history.
