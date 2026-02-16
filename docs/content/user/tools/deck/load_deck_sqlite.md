# Tutorial: `load_deck_sqlite`

## Goal

Load all deck payloads from a SQLite table.

## Steps

1. Choose database path and table.
2. Call `load_deck_sqlite(path, table=...)`.
3. Inspect payload count and identifiers.

## Example

```python
from sabueso.tools.deck import load_deck_sqlite

payloads = load_deck_sqlite("data/decks.sqlite", table="cards")
print(len(payloads))
```

## What to check

- Table exists and is readable
- Returned value is a list of payload dicts
- Canonical paths are preserved in each payload

## Notes

- Apply SQL filtering externally when you need subsets
- Convert payload list into Deck/Card objects in your workflow
