# Tutorial: `load_deck_jsonl`

## Goal

Load Deck payloads from JSONL.

## Steps

1. Point to the JSONL file.
2. Call `load_deck_jsonl(path)`.
3. Validate count and payload structure.

## Example

```python
from sabueso.tools.deck import load_deck_jsonl

payloads = load_deck_jsonl("data/decks/ligands.jsonl")
print(len(payloads))
```

## What to check

- Returned value is a list
- Each element is dict-like
- Canonical keys are present

## Notes

- Returns payloads, not a Deck object
- Rebuild Deck in your application layer if required
