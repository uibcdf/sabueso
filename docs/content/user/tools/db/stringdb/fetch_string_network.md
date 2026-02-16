# Tutorial: `fetch_string_network`

## Goal

Fetch raw payload data from STRING.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_string_network`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.stringdb import fetch_string_network

data = fetch_string_network("P52789")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
