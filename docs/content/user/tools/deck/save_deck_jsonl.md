# Tutorial: `save_deck_jsonl`

## Goal

Persist a Deck as JSONL: a header line with the deck `meta`, then one card payload per line.

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
- Line count equals deck size plus one (the header)

## Notes

- Good for streaming and simple data exchange
- `Deck.from_jsonl(path)` restores the cards and the `meta`
- Prefer SQLite for relational queries
