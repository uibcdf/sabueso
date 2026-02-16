# Tutorial: `create_string_card_online`

## Goal

Fetch STRING data and create a Sabueso Card in one call.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_string_card_online`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.stringdb import create_string_card_online

card = create_string_card_online("P52789", retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Function returns a non-empty Card
- Canonical identifiers are populated
- Evidence is attached to mapped values

## Notes

- Mark tests for this flow with @pytest.mark.online
- Keep one stable identifier per source for smoke tests
