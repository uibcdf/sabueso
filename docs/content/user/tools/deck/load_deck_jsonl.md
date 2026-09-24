# Tutorial: `load_deck_jsonl`

## Goal

Load a stored Deck from JSONL, with its meta, every card verified.

## Steps

1. Point to the JSONL file.
2. Call `load_deck_jsonl(path)`.
3. Use the returned Deck.

## Example

```python
from sabueso.tools.deck import load_deck_jsonl

deck = load_deck_jsonl("data/decks/ligands.jsonl")
print(len(deck.cards), deck.meta.get("kind"))
```

## What to check

- The returned value is a `Deck`.

## Notes

- `read_deck_jsonl(path)` returns `(meta, cards)`; `Deck.from_jsonl(path)` is equivalent
  to `load_deck_jsonl(path)`.
- Every card's quantities seal is verified; a card changed outside Sabueso is refused
  with `StorageError`.
