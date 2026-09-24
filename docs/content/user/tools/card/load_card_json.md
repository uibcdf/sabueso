# Tutorial: `load_card_json`

## Goal

Load one stored Card from JSON, verified.

## Steps

1. Provide the card JSON path.
2. Call `load_card_json(path)`.
3. Read fields and quantities from the returned Card.

## Example

```python
from sabueso.tools.card import load_card_json

card = load_card_json("data/cards/p52789.json")
print(card.get("identifiers.uniprot")["value"])
print(card.quantity("sequence.molecular_weight"))  # a quantity, with its unit
```

## What to check

- The path resolves correctly.
- The returned object is a `Card`.

## Notes

- The card's quantities seal is verified on the way in. A card changed outside Sabueso
  (a hand-edited value or unit, a removed seal) is refused with `StorageError`; there is
  no default unit.
- `Card.from_json(path)` does the same.
