# Sabueso — Recommended Storage Layout (Project-Level)

This is a **recommendation only**. There are **no default paths** in Sabueso.
Users must choose where to store Cards/Decks in their project.

## Suggested Layout

```
project_root/
  data/
    raw/                # raw source payloads (JSON/XML)
    cards/              # resolved cards
      cards.jsonl       # JSONL deck
      cards.db          # SQLite deck
    decks/              # optional per-deck files
      ligands.jsonl
      interactors.jsonl
```

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
- `load_deck_*` return the card payloads; `read_deck_*` return `(meta, payloads)`;
  `Deck.from_jsonl` and `Deck.from_sqlite` restore both.

## Notes
- JSON/JSONL is recommended for transparency and version control.
- SQLite is recommended for large datasets and fast queries.
- Raw payloads are optional, but recommended for reproducibility.
