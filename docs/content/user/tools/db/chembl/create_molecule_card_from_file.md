# Tutorial: `create_molecule_card_from_file`

## Goal

Create a Card from a local source JSON file.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_molecule_card_from_file`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.chembl import create_molecule_card_from_file

card = create_molecule_card_from_file("path/to/chembl_sample.json", retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Input path exists and contains valid JSON
- Returned Card preserves canonical structure
- Evidence tracks source provenance

## Notes

- Recommended for offline tests
- Keep fixtures small and versioned
