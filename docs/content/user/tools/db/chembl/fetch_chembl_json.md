# Tutorial: `fetch_chembl_json`

## Goal

Fetch raw payload data from ChEMBL.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_chembl_json`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.chembl import fetch_chembl_json

data = fetch_chembl_json("CHEMBL90555")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
