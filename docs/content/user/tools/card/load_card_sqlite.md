# Tutorial: `load_card_sqlite`

## Goal

Load one serialized Card payload from SQLite.

## Steps

1. Choose database path and table.
2. Optionally provide `card_id`.
3. Call `load_card_sqlite(...)`.

## Example

```python
from sabueso.tools.card import load_card_sqlite

payload = load_card_sqlite("data/cards.sqlite", table="cards", card_id="P52789")
print(payload["identifiers"]["uniprot"])
```

## What to check

- Database and table are readable
- Query returns payload (not None)
- Payload follows canonical structure

## Notes

- If `card_id` is omitted, latest row is returned
- Use deterministic IDs to avoid ambiguity
