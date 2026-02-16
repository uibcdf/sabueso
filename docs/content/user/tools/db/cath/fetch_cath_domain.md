# Tutorial: `fetch_cath_domain`

## Goal

Fetch raw payload data from CATH.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_cath_domain`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.cath import fetch_cath_domain

data = fetch_cath_domain("2nztA00")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
