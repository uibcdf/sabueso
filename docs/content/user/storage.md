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

## Cache Policy

Current policy is Raw + Cards.

- Raw payloads support reproducibility and re-resolution.
- Cards support fast reuse in workflows.
- There are **no hard-coded default paths**.

## Recommended Project Layout

See:

- `devguide/STORAGE_LAYOUT.md`
- `devguide/CACHE_POLICY.md`

## Tradeoffs

- JSON/JSONL: easiest to inspect and diff.
- SQLite: best for larger collections and query performance.
- Knowledge store: the place to keep cards you will cite, with their history.
