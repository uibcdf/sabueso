# Tutorial: `save_card_json`

## Goal

Persist one Card as a JSON file.

## Steps

1. Build or load a Card in memory.
2. Choose an output file path.
3. Call `save_card_json(card, path)`.

## Example

```python
import sabueso
from sabueso.tools.card import save_card_json

card = sabueso.create_protein_card_online("P52789", retrieved_at="2026-02-04")
save_card_json(card, "data/cards/p52789.json")
```

## What to check

- Output file exists
- File is valid JSON
- Canonical fields and evidence are preserved

## Notes

- JSON is easy to inspect and version-control
- Prefer SQLite when storing many cards
