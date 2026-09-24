# Tutorial: `load_deck_sqlite`

## Goal

Load a stored Deck from a SQLite table, with its meta, every card verified.

## Steps

1. Choose database path and table.
2. Call `load_deck_sqlite(path, table=...)`.
3. Inspect payload count and identifiers.

## Example

```python
from sabueso.tools.deck import load_deck_sqlite

deck = load_deck_sqlite("data/decks.sqlite", table="cards")
print(len(deck.cards))
```

## What to check

- Table exists and is readable
- The returned value is a `Deck`, with its `meta`

## Notes

- Apply SQL filtering externally when you need subsets
- `read_deck_sqlite(path, table=...)` returns `(meta, cards)`; `Deck.from_sqlite(path, table=...)` is equivalent
- Every card's quantities seal is verified; a card changed outside Sabueso is refused with `StorageError`
