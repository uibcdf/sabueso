# Tutorial: `fetch_uniprot_json`

```{warning}
Deprecated: use `sabueso.tools.db.uniprot.get_entry(accession)["record"]`, which adds a timeout, catalogued errors and the retrieval date and release ({doc}`../sources`). It warns when called, and will be removed before Sabueso 1.0.
```

## Goal

Fetch raw payload data from UniProt.

## Steps

1. Choose a valid identifier or input payload.
2. Call `fetch_uniprot_json`.
3. Validate canonical output fields.

## Example

```python
from sabueso.tools.db.uniprot import fetch_uniprot_json

data = fetch_uniprot_json("P52789")
print(type(data))
```

## What to check

- Returned object is dictionary-like
- Expected top-level keys are present
- Identifier resolves in the remote source

## Notes

- Use this for debugging mappings
- For end-user workflows prefer create_*_online helpers
