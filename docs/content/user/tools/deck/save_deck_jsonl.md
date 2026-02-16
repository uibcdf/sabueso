# Tutorial: `save_deck_jsonl`

## Goal

Persist a Deck as JSONL (one card payload per line).

## Steps

1. Create or assemble a Deck.
2. Choose an output `.jsonl` path.
3. Call `save_deck_jsonl(deck, path)`.

## Example

```python
from sabueso.tools.deck import save_deck_jsonl

# deck = ...
save_deck_jsonl(deck, "data/decks/ligands.jsonl")
```

## What to check

- Output file exists
- Each line is valid JSON
- Line count equals deck size

## Notes

- Good for streaming and simple data exchange
- Prefer SQLite for relational queries
