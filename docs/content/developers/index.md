# Developers

This section summarizes how to work on Sabueso code and documentation.

## Development Environment

Install in editable mode without dependencies:

```bash
pip install --no-deps --editable .
```

Run offline tests:

```bash
pytest -m "not online"
```

Run online tests:

```bash
pytest -m online
```

## Repository Areas

- `sabueso/core`: Card, Deck, EvidenceStore, aggregation helpers.
- `sabueso/tools`: user-facing storage and database helpers.
- `sabueso/mappings`: source-to-canonical transformations.
- `sabueso/resolver`: field-level selection rules and resolver runtime.
- `sabueso/ops`: operation semantics layer (currently minimal placeholders).
- `docs`: Sphinx + MyST documentation.
- `devguide`: project checkpoint, decisions, roadmap, risks.

## Documentation System

- Sphinx with `pydata_sphinx_theme`.
- Content written in MyST Markdown.
- API pages built from docstrings with `autodoc` in `docs/api/`.

Build docs locally:

```bash
sphinx-build -b html docs docs/_build/html
```

## Engineering Conventions

- Public docs in English.
- Evidence and resolver behavior must remain explicit and traceable.
- Online vs offline tests are intentionally separated.
- Version format follows `x.y.z` (no `v` prefix).

## Next Developers Priorities

1. Replace remaining placeholders in `sabueso/ops` and `sabueso/resolver/base.py`.
2. Expand field mappings and improve conflict-resolution coverage.
3. Continue improving docstring quality so API reference remains high signal.
4. Keep `devguide/` synchronized as the canonical checkpoint for team onboarding.
