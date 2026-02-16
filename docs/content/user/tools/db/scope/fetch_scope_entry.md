# Tutorial: `fetch_scope_entry`

## Goal

Fetch raw payload data from SCOPe.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_scope_entry`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.scope import fetch_scope_entry

data = fetch_scope_entry("d2nzta1")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
