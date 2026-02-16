# Tutorial: `fetch_ted_entry`

## Goal

Fetch raw payload data from TED.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_ted_entry`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.ted import fetch_ted_entry

data = fetch_ted_entry("Q9Y6K9")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
