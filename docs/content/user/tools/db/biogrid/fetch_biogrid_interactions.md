# Tutorial: `fetch_biogrid_interactions`

## Goal

Fetch raw payload data from BioGRID.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_biogrid_interactions`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.biogrid import fetch_biogrid_interactions

data = fetch_biogrid_interactions("P52789")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
