# Developers

This section summarizes how to work on Sabueso code and documentation.

## Development Environment

Dependencies come from the `uibcdf` and `conda-forge` conda channels, as they do for
users. pip is used only to install Sabueso itself, in editable mode:

```bash
conda env create -n sabueso-dev -f devtools/conda-envs/development_env.yaml
conda activate sabueso-dev
pip install --no-deps --editable .
```

The environments live in `devtools/conda-envs/`:

- `development_env.yaml`: development;
- `test_env.yaml`: what CI tests run on;
- `docs_env.yaml`: documentation;
- `build_env.yaml`: building the conda package.

Run offline tests (agents use `--receptor=llm`; CI uses `--receptor=ci`):

```bash
pytest -m "not online"
```

Run online tests:

```bash
pytest -m online
```

## Conda package

The recipe is in `devtools/conda-build/`; see its `README.md`.

## Repository Areas

- `sabueso/core`: Card, Deck, SourceAssertionStore, aggregation helpers.
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
- SourceAssertions and resolver behavior must remain explicit and traceable.
- Online vs offline tests are intentionally separated.
- Version format follows `x.y.z` (no `v` prefix).

## Plans and state

- `devguide/README.md` indexes the developer guide.
- `devguide/CHECKPOINT.md` records the current state of the repository.
- `devguide/ROADMAP.md` records the plan: the foundational plan and the pilot-driven
  route, integrated, with the status of every objective.
- `AGENTS.md` holds the repository's working rules: principles, conventions, local
  gates, schema policy, commits and releases.
