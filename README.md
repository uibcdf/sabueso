# Sabueso

[![MOLI: Knowledge](https://img.shields.io/badge/MOLI-Knowledge-blue.svg)](https://github.com/uibcdf/moli)
[![MOLI governance](https://github.com/uibcdf/sabueso/actions/workflows/moli-governance.yml/badge.svg)](https://github.com/uibcdf/sabueso/actions/workflows/moli-governance.yml)
[![Offline tests](https://github.com/uibcdf/sabueso/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/uibcdf/sabueso/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/uibcdf/sabueso/branch/main/graph/badge.svg)](https://app.codecov.io/gh/uibcdf/sabueso)
[![Python 3.11–3.14](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://github.com/uibcdf/moli/blob/main/devguide/policies/python_policy.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sabueso is the **Knowledge** component of the MOLI platform: a scientific Python library for aggregating and normalizing biomolecular data across multiple public databases.

Given a molecular system (protein, peptide, small molecule, etc.), it produces a structured **Card** of resolved molecular knowledge in which every value is linked to the **SourceAssertions** — what each external source asserts — that support it. A **Deck** is a collection of cards with consistent operations.

## Status

Active early-stage implementation. Sabueso is directly governed by MOLI for shared platform and engineering contracts while retaining ownership of its implementation, scientific behavior, tests, and local API.

Python 3.11, 3.12, 3.13, and 3.14 are currently supported and exercised by the offline CI suite. Python 3.14 is the routine development version under MOLI's direct-component baseline.

The coverage badge measures the Sabueso package with offline pytest on
Linux/Python 3.14 after pushes to `main`. It does not cover online service tests;
the displayed report may briefly lag a new push while CI finishes.

## Current release status

- **Latest release:** [0.13.0](https://github.com/uibcdf/sabueso/releases/tag/0.13.0)
  (2026-10-05), distributed through the `uibcdf` conda channel.
  - One `noarch` package for Linux, macOS Apple Silicon (arm64) and Windows,
    on Python 3.11–3.14. The exact `py_0` file passes all 12 installed lanes,
    each with 613 integration cases and the public attribution workflow. A clean
    public Linux/Python 3.14 installation verifies bytes, origins, API, frozen-card
    reading, those 613 cases, workflow and pip check.
  - Card schema 0.3.12 retains original literal extraction and explicit article
    bibliography. Pinned disease/state/bioactivity/ligand/oligomer explanations
    preserve support; versioned corrections retain explicit legacy rules.
  - Required Ackredit >=0.9.0 attribution now observes ChEMBL, PubChem, BindingDB,
    CCD, UniChem, PDBe-KB, AlphaFold DB and InterPro alongside UniProt, Europe PMC
    and RCSB. Save original runtime JSON with scientific objects; broader coverage
    and bibliography gaps remain explicit.
  - Zenodo [10.5281/zenodo.23162373](https://doi.org/10.5281/zenodo.23162373):
    all 960 source files verified against the qualified tag.
  - Complete [publication receipt](devtools/conda-build/receipts/sabueso_0.13.0_public_2026-10-05.json).
  - 0.12.0 remains archived on Zenodo, identical to its tag:
    [10.5281/zenodo.23134375](https://doi.org/10.5281/zenodo.23134375).
  - 0.11.0 is archived on Zenodo, verified to be identical to its tag:
    [10.5281/zenodo.23099139](https://doi.org/10.5281/zenodo.23099139).
  - Users who exported literature extractions with earlier versions: upgrade.
    `CurationStore` now keeps rule/model extractions out of human-curation export;
    already-exported records need their original acquired state to recover omitted
    provenance (#105; see the release notes).
  - 0.10.0 is archived on Zenodo, verified to be identical to its tag:
    [10.5281/zenodo.23089116](https://doi.org/10.5281/zenodo.23089116).
  - 0.9.0 is archived on Zenodo, verified to be identical to its tag:
    [10.5281/zenodo.23084553](https://doi.org/10.5281/zenodo.23084553).
  - 0.8.1 is archived on Zenodo, verified to be identical to its tag:
    [10.5281/zenodo.23079157](https://doi.org/10.5281/zenodo.23079157).
  - Users of 0.8.0 who read OMA orthologs: upgrade. An ortholog could be named by a
    retired UniProt accession (see the release notes).
  - 0.8.0 is archived on Zenodo, verified to be identical to its tag:
    [10.5281/zenodo.23077926](https://doi.org/10.5281/zenodo.23077926).
  - Users of 0.7.0 who read gnomAD variants: upgrade. Some changes were placed on
    canonical residues the canonical protein never carries (see the release notes).
  - Users of 0.6.0: see the 0.7.0 release notes about cut answers (#88).
  - Users of 0.3.0: see the 0.3.1 release notes about copies of cards (#64).
  - Users of 0.2.0: see the 0.3.0 release notes about curated ids (#62).
- **0.7.0 to 0.3.0** are archived on Zenodo, each verified to be identical to its tag:
  - 0.7.0: [10.5281/zenodo.23048186](https://doi.org/10.5281/zenodo.23048186);
  - 0.6.0: [10.5281/zenodo.23038465](https://doi.org/10.5281/zenodo.23038465);
  - 0.5.0: [10.5281/zenodo.23001265](https://doi.org/10.5281/zenodo.23001265);
  - 0.4.0: [10.5281/zenodo.22969742](https://doi.org/10.5281/zenodo.22969742);
  - 0.3.1: [10.5281/zenodo.22959360](https://doi.org/10.5281/zenodo.22959360);
  - 0.3.0: [10.5281/zenodo.22958049](https://doi.org/10.5281/zenodo.22958049);
  - concept DOI, which covers all versions and resolves to the latest:
    [10.5281/zenodo.22937375](https://doi.org/10.5281/zenodo.22937375).
- **0.2.0** is archived and verified on Zenodo
  ([10.5281/zenodo.22948384](https://doi.org/10.5281/zenodo.22948384)).
- **0.1.1** is archived too
  ([10.5281/zenodo.22937715](https://doi.org/10.5281/zenodo.22937715)).

  Each Zenodo record holds the source snapshot of its tag only. The conda package is
  published separately on the `uibcdf` channel.
- **0.1.0** is archived too ([10.5281/zenodo.22937376](https://doi.org/10.5281/zenodo.22937376)),
  but its package cannot build cards (#35).

To cite Sabueso, see [`CITATION.cff`](CITATION.cff).

## Installation

Sabueso is distributed through the `uibcdf` conda channel, like the other UIBCDF Python
components:

```bash
conda install -c uibcdf -c conda-forge sabueso
```

It runs on Linux, macOS Apple Silicon (arm64) and Windows with Python 3.11–3.14.
macOS support is currently limited to Apple Silicon (arm64). Intel-based macOS
(x86_64) is not part of the supported platform matrix. Support may be
reconsidered if there is demonstrated user demand. `pandas` is optional; install
it (`conda install -c conda-forge pandas`) to turn tables into DataFrames. Avoid 0.1.0:
its package lacks a data file and cannot build cards (#35). Sabueso is not published on
PyPI.

For development, provision the Conda environment with public runtime dependencies,
including Ackredit >=0.9.0. Python 3.14 is the routine development version:

```bash
conda env create -n sabueso-dev -f devtools/conda-envs/development_env.yaml
conda activate sabueso-dev
```

Follow [the development provisioning instructions](devtools/conda-envs/README.md),
then install the local checkout:

```bash
pip install --no-deps --editable .
```

## Development

Start with:

- `AGENTS.md` and `MOLI_GUIDE.md` for governance;
- `devguide/README.md`, the index of the developer guide;
- `devguide/VISION.md` and `devguide/ARCHITECTURE.md` for Sabueso's scientific design;
- `devguide/CHECKPOINT.md` for the current repository baseline, and
  `devguide/ROADMAP.md` for the plan (the foundational plan and the pilot-driven route,
  integrated);
- `schemas/card_schema_0.3.11.yaml` for the current card schema, and
  `schemas/card_schema.yaml` for the conceptual draft it grew from.

Common quality gates:

```bash
ruff format --check .
ruff check .
pytest -m "not online"
```

If `sabueso.__version__` reports an old version when Python runs from the repository
root, delete the stale `sabueso.egg-info/` left by an earlier in-tree build. Python finds
that metadata before the metadata of the editable install.

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
