# Sabueso — Checkpoint

The state of the repository, so that anyone can resume from it. Keep it current: update
it with each release, and whenever a change makes a line below false. History does not
belong here. Decisions go to `DECISIONS.md`, and the previous log is
`archive/CHECKPOINT_log_to_0.4.0.md`.

*Last updated: 2026-09-26, after release 0.4.0.*

## Release and schema

- **Latest release:** 0.4.0 (2026-09-25).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Archived on Zenodo, DOI 10.5281/zenodo.22969742.
- **Card schema:** main writes 0.3.5 (`schemas/card_schema_0.3.5.yaml`), unpublished:
  0.3.4 plus `author_numbering` (#73). Release 0.4.0 writes 0.3.4.
  - Published versions keep their frozen cards in `temp_data/frozen_cards/`: 0.3.0 to
    0.3.4.
  - The recorded shape of the current schema is `schemas/card_shape_0.3.5.json`.
- **Unreleased on main:**
  - inventory grouping keys and residue maps (#70);
  - NCBI Gene for identity across gene databases (#69);
  - `claims(topic)` and `group_by_rank(rank)` refuse misspelt values;
  - the selection rules published in the user guide match the packaged ones (0.2.0);
  - the oligomer from author-defined assemblies (`structure_state@2`, #72); author
    numbering (#73); partial RCSB entries kept and a `partial` knowledge state
    (`knowledge_state@2`, #74).

## Package layout

- `sabueso/core/`: the domain.
  - Card and Deck.
  - The SourceAssertion and relationship stores.
  - Views and derivation rules: structures, bioactivities and measurements, oligomer,
    ligand sites, ligands, literature, knowledge state, card diff, identity audit, names.
  - Curation and the curation store.
  - Snapshots and the knowledge store; migration.
  - Quantities; tables.
- `sabueso/resolver/`: the EntityResolver and the FieldResolver, selection rules,
  enrichment profiles, and the UniProt and RCSB clients.
- `sabueso/mappings/`: one mapping per source.
- `sabueso/tools/db/`: source access, one module per source in use (see
  `sources/registry.yaml`).
- `sabueso/tools/card/`: the protein and small-molecule card tools, and file storage.
- `sabueso/tools/deck/`: deck file storage.
- `sabueso/tools/resolve.py`: `sabueso.resolve`.
- `sabueso/_private/`: argument digesters (ArgDigest, one per argument name) and
  diagnostics (SMonitor).
- `sabueso/ops/`, `sabueso/utils/`: thin, kept for layout.
- `schemas/`: card schemas by version, recorded shapes, and the conceptual draft
  (`card_schema.yaml`).
- `tools/`:
  - `card_shape.py` (recorded shape), `validate_schema.py`, `validate_card.py`,
    `validate_deck.py`;
  - `source_registry.py` (registry check and its page);
  - `build_showcase_notebook.py`.
- `devtools/`: conda recipe, release plan and route, verification scripts, the MOLI
  governance check.
- `temp_data/`: frozen public responses used as fixtures, with licences in
  `temp_data/NOTICE.md`; frozen cards.
- `docs/`: Sphinx user guide, API reference, showcase notebook.

## Quality baseline

- Offline suite: 720 tests passed, 15 online tests deselected (2026-09-26). Run with
  `python -m pytest -m "not online" --receptor=llm`.
- Ruff format and check are clean. The MOLI governance check passes. The recorded card
  shape matches, and the source registry matches its page.
- CI (`.github/workflows/ci.yml`): Linux and Windows × Python 3.11–3.14, macOS 3.13.

## Open work

- Plan and status of every objective: `ROADMAP.md`. It integrates the foundational plan
  and the pilot-driven route.
- Open issues:
  - #53, the reference form (waits on uibcdf/moli#3);
  - #60, biological context (deferred);
  - #30, ligand proximity (deferred);
  - #29, usage terms of knowledge;
  - #22, BioGRID (needs a key);
  - #20 and #19, re-evaluations of structure and relationship storage;
  - #36, an ArgDigest experiment.
- Risks: `RISKS_AND_OPEN_QUESTIONS.md`.
