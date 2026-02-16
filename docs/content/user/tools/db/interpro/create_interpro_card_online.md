# Tutorial: `create_interpro_card_online`

## Goal

Fetch InterPro data and create a Sabueso Card in one call.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_interpro_card_online`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.interpro import create_interpro_card_online

card = create_interpro_card_online("IPR000001", retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Function returns a non-empty Card
- Canonical identifiers are populated
- Evidence is attached to mapped values

## Notes

- Mark tests for this flow with @pytest.mark.online
- Keep one stable identifier per source for smoke tests
