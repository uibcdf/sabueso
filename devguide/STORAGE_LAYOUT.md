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
- `store.save_packet(packet, packet_name)` stores a knowledge packet revision
  (`sabueso:packet:<name>@sha256:…`) once every card state it cites is in the store.
  `store.load_packet(name or ref)` verifies the packet and those states;
  `store.packet_history(name)` lists the revisions with their format, their
  content-equivalence ids and whether the knowledge changed (#71); revisions of
  different formats are not compared (#88).
- `store.import_card_table(path, table="cards")` imports the rows of a
  `save_card_sqlite` table, oldest first, as history.

Tables (format 2, #99):
- `snapshots` holds one row per distinct state: the card's document, plus its seal,
  zlib-compressed. `snapshot_numbers` gives each state an integer.
- `revisions` holds the saves of each card, in order.
- `sa_rows` and `rel_rows` hold one row per distinct content, compressed, with indexed
  columns (`sa_id`/`rel_id`, subject, field path, predicate, object, source release). A
  SourceAssertion's row leaves out `retrieved_at`: the same statement read again is the
  same row.
- `card_sa` and `card_rel` say which rows each state holds, in which order, by integer.
  `card_sa` also names when each statement was read (`retrieval_times`).
- `deck_snapshots` holds one row per distinct deck content, and `deck_revisions` the
  saves of each deck name, in order.
- `packet_snapshots` holds one row per distinct knowledge packet (its document, its
  snapshot id and its content-equivalence id), and `packet_revisions` the saves of each
  packet name, in order (#71).
- `store_meta` holds the store's format, currently 2. A format-1 store is upgraded in
  place when it is opened: its rows are copied as written (text, `retrieved_at` inside),
  and its old row tables are dropped. A Sabueso that reads only format 1 refuses a
  format-2 store.

Measured on a live pilot store (two proteins, six card states): 15.4 MB in format 1,
4.7 MB in format 2; saving both cards again with unchanged knowledge adds 0.2 MB, where
format 1 stored them whole again (about 5 MB).

Every read rebuilds the snapshot, hashes it and compares the result with its id. That
includes the reads of a single pinned item (`source_assertion`, `relationship`) and the
states `relationships()` cites. A row changed outside Sabueso fails the read, instead of
being returned under an unchanged pin (#79). For a card of about a thousand
relationships, a verified item read takes about 0.1 s. Then
`Card.from_dict` checks the schema version and the quantities seal. The store uses no
SQLite JSON functions, so any SQLite that Python ships with works.

## Notes
- JSON/JSONL is recommended for transparency and version control.
- SQLite is recommended for large datasets and fast queries.
- Raw payloads are optional, but recommended for reproducibility.
