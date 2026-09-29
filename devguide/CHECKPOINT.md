# Sabueso — Checkpoint

The state of the repository, so that anyone can resume from it. Keep it current: update
it with each release, and whenever a change makes a line below false. History does not
belong here. Decisions go to `DECISIONS.md`, and the previous log is
`archive/CHECKPOINT_log_to_0.4.0.md`.

*Last updated: 2026-09-27, after release 0.5.0.*

## Release and schema

- **Latest release:** 0.5.0 (2026-09-27).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Staged candidate 2ea2693; sha256 `69fd95b1…5ecb`.
  - Verified by a clean public install on Python 3.14.
  - Archived on Zenodo (10.5281/zenodo.23001265), identical to tag 0.5.0.
- **Card schema:** 0.3.5 (`schemas/card_schema_0.3.5.yaml`), published by 0.5.0. Main may
  already write additive changes that the next release will publish.
  - Published versions keep their frozen cards in `temp_data/frozen_cards/`: 0.3.0 to
    0.3.5.
  - The recorded shape of 0.3.5 is `schemas/card_shape_0.3.5.json`.
- **Unreleased on main:**
  - card schema 0.3.6 (`schemas/card_schema_0.3.6.yaml`, shape
    `schemas/card_shape_0.3.6.json`). It adds UniProt isoforms, alternative sequences
    and secondary structure, per-chain secondary structure from RCSB, and states
    deletions as `substitution.missing` (#80);
  - an integrity fix for users of 0.5.0 and earlier: a deletion stated by UniProt read
    as an unspecified variant, and a free-text comment restricted to an isoform read
    as a statement about the entry (#80);
  - the biological context of a target, curated from publications (#60, step 1):
    `annotations.stage_expression`, `essentiality`, `accessibility` and
    `metabolic_role`;
  - PHI-base, a new source (#83): phenotypes of pathogen mutants
    (`annotations.pathogen_phenotypes`), from versioned releases, cached only where
    told;
  - the clinical layer of molecules (#81): ChEMBL indications (`investigated_for`)
    and the ClinicalTrials.gov trials they cite (`tested_in`), `Card.clinical()`;
  - gene–disease associations for human proteins (#82): DISEASES, per channel; Open
    Targets, with its scores as stated; and Orphanet's rare disorders;
  - Reactome pathways and reactions (#83, `participates_in`);
  - ClinVar variants of human genes (#83, `annotations.clinical_variants`), placed in
    UniProt numbering only through a canonical transcript and a matching residue, and
    gnomAD population frequencies (`annotations.population_variants`) placed the same
    way;
  - a prototype of knowledge packets (#71): `KnowledgeQuery`, `knowledge_packet`,
    `compose_packet`, and stored, pinned packets with a content-equivalence id. Its
    shared contract waits on uibcdf/moli#22.

## Package layout

- `sabueso/core/`: the domain.
  - Card and Deck.
  - The SourceAssertion and relationship stores.
  - Views and derivation rules: structures, bioactivities and measurements, oligomer,
    ligand sites, ligands, literature, knowledge state, card diff, identity audit, names.
  - Curation and the curation store.
  - Snapshots and the knowledge store; knowledge packets; migration.
  - Quantities; tables.
- `sabueso/resolver/`: the EntityResolver and the FieldResolver, selection rules,
  enrichment profiles, and the UniProt and RCSB clients.
- `sabueso/mappings/`: one mapping per source.
- `sabueso/tools/db/`: source access, one module per source in use (see
  `sources/registry.yaml`).
- `sabueso/tools/card/`: the protein and small-molecule card tools, and file storage.
- `sabueso/tools/deck/`: deck file storage.
- `sabueso/tools/resolve.py`: `sabueso.resolve`; `sabueso/tools/packet.py`: `sabueso.knowledge_packet`.
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

- Offline suite: 836 tests passed, 15 online tests deselected (2026-09-27). Run with
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
