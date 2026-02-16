# Testing

Sabueso test strategy separates offline and online execution.

## Offline (default)

Offline tests do not require network access and should be the default in local
and CI workflows.

```bash
pytest -m "not online"
```

## Online (manual)

Online tests hit external endpoints and are explicitly marked.

```bash
pytest -m online
```

## Notes

- Some online tests are dump-backed (for example SCOPe/TED behavior).
- Some online tests may skip if endpoint access is unavailable or slow.
- BioGRID online execution requires `BIOGRID_ACCESS_KEY`.

## Schema Validation Tests

- Field-path vs schema alignment:

```bash
pytest tests/core/test_schema_alignment.py
```

- Card schema validation:

```bash
pytest tests/core/test_card_schema_validation_offline.py
```

- Deck schema validation:

```bash
pytest tests/core/test_deck_schema_validation_offline.py
```
