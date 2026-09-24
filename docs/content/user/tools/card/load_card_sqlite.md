# Tutorial: `load_card_sqlite`

## Goal

Load one stored Card from SQLite, verified.

## Steps

1. Choose database path and table.
2. Optionally provide `card_id`.
3. Call `load_card_sqlite(...)`.

## Example

```python
from sabueso.tools.card import load_card_sqlite

card = load_card_sqlite("data/cards.sqlite", table="cards", card_id="P52789")
print(card.get("identifiers.uniprot")["value"])
```

## What to check

- The database and table are readable.
- The query returns a Card (not `None`).

## Notes

- If `card_id` is omitted, the latest row is returned.
- The card's quantities seal is verified; a card changed outside Sabueso is refused with
  `StorageError`.
