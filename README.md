# Sabueso

[![MOLI: Knowledge](https://img.shields.io/badge/MOLI-Knowledge-blue.svg)](https://github.com/uibcdf/moli)
[![MOLI governance](https://github.com/uibcdf/sabueso/actions/workflows/moli-governance.yml/badge.svg)](https://github.com/uibcdf/sabueso/actions/workflows/moli-governance.yml)
[![Python 3.11–3.14](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_policy.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sabueso is the **Knowledge** component of the MOLI platform: a scientific Python library for aggregating and normalizing biomolecular data across multiple public databases.

Given a molecular system (protein, peptide, small molecule, etc.), it produces a structured **Card** of resolved molecular knowledge in which every value is linked to the **SourceAssertions** — what each external source asserts — that support it. A **Deck** is a collection of cards with consistent operations.

## Status

Active early-stage implementation. Sabueso is directly governed by MOLI for shared platform and engineering contracts while retaining ownership of its implementation, scientific behavior, tests, and local API.

Python 3.11, 3.12, 3.13, and 3.14 are currently supported and exercised by the offline CI suite. Python 3.14 is explicitly admitted under MOLI's active Python transition.

## Installation

Sabueso is distributed through the `uibcdf` conda channel, like the other UIBCDF Python
components. It has not had a public release yet; the first one will be 0.1.0.

For development, dependencies come from conda and pip is used only for the local editable
install:

```bash
conda env create -n sabueso-dev -f devtools/conda-envs/development_env.yaml
conda activate sabueso-dev
pip install --no-deps --editable .
```

## Development

Start with:

- `AGENTS.md` and `MOLI_GUIDE.md` for governance;
- `devguide/VISION.md` and `devguide/ARCHITECTURE.md` for Sabueso's scientific design;
- `devguide/CHECKPOINT.md` for the current repository baseline;
- `schemas/card_schema.yaml` for the current conceptual schema.

Common quality gates:

```bash
ruff format --check .
ruff check .
pytest
```

## Repository layout

```text
sabueso/
  core/
  resolver/
  tools/
    db/
    card/
    deck/
  ops/
  mappings/
  utils/
docs/
tests/
```

## Documentation

Sphinx documentation lives in `docs/` and uses the **pydata_sphinx_theme**.

## Governance

Sabueso follows MOLI's shared engineering and platform governance. Local bugs and proposals belong to this repository; shared contracts involving other MOLI components belong to `uibcdf/moli`.

See `MOLI_GUIDE.md` for the concise governance contract.
