# Tutorial: `create_ted_card_online`

## Goal

Fetch TED data and create a Sabueso Card in one call.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_ted_card_online`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.ted import create_ted_card_online

card = create_ted_card_online("Q9Y6K9", retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Function returns a non-empty Card
- Canonical identifiers are populated
- Evidence is attached to mapped values

## Notes

- Mark tests for this flow with @pytest.mark.online
- Keep one stable identifier per source for smoke tests
