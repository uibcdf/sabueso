# Tutorial: `fetch_go_term`

## Goal

Fetch raw payload data from GO.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_go_term`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.go import fetch_go_term

data = fetch_go_term("GO:0008150")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
