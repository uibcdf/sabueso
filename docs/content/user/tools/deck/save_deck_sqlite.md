# Tutorial: `save_deck_sqlite`

## Goal

Append all cards in a Deck to SQLite.

## Steps

1. Create or assemble a Deck.
2. Set database path and table.
3. Call `save_deck_sqlite(...)` with optional `id_field`.

## Example

```python
from sabueso.tools.deck import save_deck_sqlite

# deck = ...
save_deck_sqlite(deck, "data/decks.sqlite", table="cards", id_field="identifiers.uniprot")
```

## What to check

- Rows are inserted for all deck cards
- Serialized payload is stored per row
- `card_id` is populated when configured

## Notes

- Recommended for large persistent decks
- Keep consistent table conventions across projects
