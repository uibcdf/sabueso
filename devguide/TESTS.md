# Sabueso — Test Strategy (Offline vs Online)

## Offline tests (default)
Offline tests must not require network access. They should use fixtures or mock data.
Run them with:

```
pytest -m "not online"
```

## Online tests (manual)
Online tests are explicitly marked and require network access.
Run them with:

```
pytest -m online
```

## Conventions
- Any test that calls a `fetch_*` function or hits a remote endpoint **must** be marked `@pytest.mark.online`.
- Offline tests are the default for CI and local development.
- Some online tests are **dump-backed** (SCOPe/TED) and will download remote files unless
  `SCOPE_DUMP_PATH` / `TED_DUMP_PATH` are set to local files.
- Some online tests may skip on slow/unreachable endpoints (e.g., InterPro timeout).
