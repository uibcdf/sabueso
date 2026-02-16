# Tutorial: `fetch_interpro_entry`

## Goal

Fetch raw payload data from InterPro.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_interpro_entry`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.interpro import fetch_interpro_entry

data = fetch_interpro_entry("IPR000001")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
