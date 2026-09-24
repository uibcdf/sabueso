# Tutorial: `save_card_sqlite`

## Goal

Append one Card to a SQLite database table.

## Steps

1. Build or load a Card.
2. Set database path and table name.
3. Call `save_card_sqlite(...)` with optional `id_field`.

## Example

```python
import sabueso
from sabueso.tools.card import save_card_sqlite

card, _ = sabueso.resolve("P52789")
save_card_sqlite(
    card, "data/cards.sqlite", table="cards", id_field="identifiers.uniprot"
)
```

## What to check

- SQLite file and table exist
- Row is inserted
- `card_id` is populated when `id_field` resolves

## Notes

- Better than many JSON files for query-oriented workflows
- Keep a stable id_field convention in your project
