# Tutorial: `fetch_pubchem_json`

## Goal

Fetch raw payload data from PubChem.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_pubchem_json`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.pubchem import fetch_pubchem_json

data = fetch_pubchem_json("66414")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
