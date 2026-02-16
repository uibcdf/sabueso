# Tutorial: `load_card_json`

## Goal

Load one serialized Card payload from JSON.

## Steps

1. Provide the card JSON path.
2. Call `load_card_json(path)`.
3. Inspect key fields in the returned payload.

## Example

```python
from sabueso.tools.card import load_card_json

payload = load_card_json("data/cards/p52789.json")
print(payload["identifiers"]["uniprot"])
```

## What to check

- Path resolves correctly
- Returned object is dict-like
- Required canonical sections are present

## Notes

- This returns payload data, not a Card object
- Wrap into Card in your application layer if needed
