# Tutorial: `save_deck_sqlite`

## Goal

Store a Deck in a SQLite table, with its `meta` in the `deck_meta` table.

## Steps

1. Create or assemble a Deck.
2. Set database path and table.
3. Call `save_deck_sqlite(...)` with optional `id_field`.

## Example

```python
from sabueso.tools.deck import save_deck_sqlite

# deck = ...
save_deck_sqlite(
    deck, "data/decks.sqlite", table="cards", id_field="identifiers.uniprot"
)
```

## What to check

- The table holds one row per deck card; saving again replaces them
- Serialized payload is stored per row
- `card_id` is populated when configured
- The deck `meta` is in `deck_meta`, keyed by the table name

## Notes

- Recommended for large persistent decks
- One table holds one deck. To accumulate cards, extend the deck in memory and save it once
- Table names must be plain identifiers; `deck_meta` is reserved
- `Deck.from_sqlite(path, table=...)` restores the cards and the `meta`
