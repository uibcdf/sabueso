# Tutorial: `create_structure_card_from_json`

## Goal

Create a Card from an in-memory source payload.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_structure_card_from_json`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.pdb import create_structure_card_from_json

payload = {}  # Replace with real PDB payload
card = create_structure_card_from_json(payload, retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Payload is dictionary-like
- Returned Card has canonical paths
- Evidence metadata is available

## Notes

- Useful for integration tests and reproducible pipelines
- Keep payload shape aligned with current source format
