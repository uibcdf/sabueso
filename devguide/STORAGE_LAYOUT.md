# Sabueso — Recommended Storage Layout (Project-Level)

This is a **recommendation only**. There are **no default paths** in Sabueso.
Users must choose where to store Cards/Decks in their project.

## Suggested Layout

```
project_root/
  data/
    knowledge.db        # KnowledgeStore: cards and decks with their revisions
    curation.jsonl      # CurationStore: curated statements, kept across rebuilds
    raw/                # optional: raw source payloads (tools.db get_* records)
    exports/            # optional: files to share
      cards.jsonl       # JSONL deck
      cards.db          # SQLite deck
      ligands.jsonl
```

The knowledge store is the default choice for a project: what it saves can be cited
exactly (pinned references) and read back as it was. The files are for exchange and
inspection. A curation store belongs to whoever curates, and it can serve several
projects.

## Deck files (uibcdf/sabueso#26)
A deck is its cards plus its `meta`: the traces that make it interpretable, such as the
decision of an `ambiguity_deck`, or the source outcomes and unanchored records of a
`ligand_deck`. Both are persisted:
- **JSONL:** the first line is a header, `{"sabueso_deck": {"format": 1, "meta": {...}}}`,
  followed by one card per line. Files without a header (written before #26) still
  load, with empty `meta`.
- **SQLite:** the cards of a deck fill one table, and its `meta` is the row of the
  `deck_meta` table keyed by that table name. Several decks can share one database, one
  table each.
- **Saving replaces.** Saving a deck into a table replaces what the table held, so a
  table and its `meta` always describe the same deck. To accumulate cards, build the
  deck in memory (`Deck.extend`) and save it once.
- Table names must be plain identifiers, and `deck_meta` is reserved.
- `load_deck_*` return a `Deck`; `read_deck_*` return `(meta, cards)`;
  `Deck.from_jsonl` and `Deck.from_sqlite` restore both. Likewise `load_card_*` return a
  `Card`.
- **Every loader verifies.** A stored card's quantities are sealed (`quantities`, #32),
  and no public function returns an unverified payload: a card changed outside Sabueso
  is refused with `StorageError`.

## Knowledge store (uibcdf/sabueso#7, #27)
`sabueso.KnowledgeStore(path)` keeps cards with their history, in one SQLite file:
- `store.save(card, note=None)` stores the card's exact state (a snapshot) and returns
  its pinned reference, `<card_id>@sha256:<hex>`. Saving the card's latest state again
  adds nothing.
- `store.load(ref)` returns that exact state, or, for a bare `card_id`, the latest one.
  A pin that is absent or malformed raises `StorageError`; another state is never
  returned in its place.
- `store.history(card_id)` lists the revisions: reference, time, note and schema.
- `store.source_assertion(ref)` and `store.relationship(ref)` return one item of a
  pinned state, `<card_id>@sha256:<hex>#SA_…` or `#REL_…`.
- `store.relationships(object_ref=…, predicate=…, subject_ref=…)` searches across the
  latest states of all cards, or across every state with `all_revisions=True`. An
  example: which proteins a molecule was measured on.
- `store.save_deck(deck, deck_name)` stores a deck revision: its meta and the pinned
  states of its cards, content-addressed. It returns `sabueso:deck:<name>@sha256:…`.
  `store.load_deck(name or ref)` gives the latest revision or the exact pinned one, and
  `store.deck_history(name)` lists the revisions (#58).
- `store.import_card_table(path, table="cards")` imports the rows of a
  `save_card_sqlite` table, oldest first, as history.

Tables:
- `snapshots` holds one row per distinct state: the card's document as JSON, plus its
  seal.
- `revisions` holds the saves of each card, in order.
- `source_assertions` and `relationships` hold one row per distinct content, with
  indexed columns (`sa_id`/`rel_id`, subject, field path, predicate, object, source
  release).
- `snapshot_source_assertions` and `snapshot_relationships` say which rows each state
  holds, and in which order.
- `deck_snapshots` holds one row per distinct deck content, and `deck_revisions` the
  saves of each deck name, in order.
- `store_meta` holds the store's format, currently 1.

Every read rebuilds the snapshot, hashes it and compares the result with its id. Then
`Card.from_dict` checks the schema version and the quantities seal. The store uses no
SQLite JSON functions, so any SQLite that Python ships with works.

## Notes
- JSON/JSONL is recommended for transparency and version control.
- SQLite is recommended for large datasets and fast queries.
- Raw payloads are optional, but recommended for reproducibility.
