# Tutorial: `create_protein_card`

## Goal

Create a Card using the module helper workflow.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_protein_card`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.uniprot import create_protein_card

card = create_protein_card("P52789", retrieved_at="2026-02-04")
print(card.get("identifiers"))
```

## What to check

- Helper resolves input into a valid Card
- Canonical identifiers are present
- Key mapped sections are populated

## Notes

- Prefer explicit online/offline helpers when available
