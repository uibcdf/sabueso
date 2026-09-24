# Tutorial: `create_compound_card_online`

```{warning}
Deprecated: use `sabueso.resolve("pubchem:<cid>")`, which anchors the compound at its standard InChIKey and links its records across sources. It warns when called, and will be removed before Sabueso 1.0.
```

## Goal

Fetch PubChem data and create a Sabueso Card in one call.

## Steps

1. Choose a valid identifier or input payload.
2. Call `create_compound_card_online`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.pubchem import create_compound_card_online

card = create_compound_card_online("66414", retrieved_at="2026-02-04")
print(card.get("metadata.entity_type"))
```

## What to check

- Function returns a non-empty Card
- Canonical identifiers are populated
- Each mapped value is linked to the SourceAssertions that support it

## Notes

- Mark tests for this flow with @pytest.mark.online
- Keep one stable identifier per source for smoke tests
