# Tutorial: `fetch_pdb_json`

```{warning}
Deprecated: use `sabueso.tools.db.rcsb.get_entry(pdb_id)`, the RCSB entry data Sabueso maps, in a provenance envelope ({doc}`../sources`). It warns when called, and will be removed before Sabueso 1.0.
```

## Goal

Fetch raw payload data from PDB.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_pdb_json`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.pdb import fetch_pdb_json

data = fetch_pdb_json("2NZT")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
