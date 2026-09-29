# Sabueso — Checkpoint

The state of the repository, so that anyone can resume from it. Keep it current: update
it with each release, and whenever a change makes a line below false. History does not
belong here. Decisions go to `DECISIONS.md`, and the previous log is
`archive/CHECKPOINT_log_to_0.4.0.md`.

*Last updated: 2026-09-29, after release 0.6.0.*

## Release and schema

- **Latest release:** 0.6.0 (2026-09-29).
  - Published on the `uibcdf` conda channel, as a `noarch` package for Python 3.11–3.14.
  - Staged candidate 3e5c3db; sha256 `e155b9b7…5f2d`.
  - The exact staged file passed the installed-package gate on Linux, macOS and
    Windows × 3.11–3.14, and a clean public install on Python 3.14.
  - Zenodo archive: pending.
- **Card schema:** 0.3.6 (`schemas/card_schema_0.3.6.yaml`), published by 0.6.0. Main may
  already write additive changes that the next release will publish.
  - Published versions keep their frozen cards in `temp_data/frozen_cards/`: 0.3.0 to
    0.3.6.
  - The recorded shape of 0.3.6 is `schemas/card_shape_0.3.6.json`.
- **Unreleased on main:**
  - card schema 0.3.7 (`schemas/card_schema_0.3.7.yaml`, shape
    `schemas/card_shape_0.3.7.json`): `annotations.interface_mutations` from SKEMPI 2.0,
    placed through RCSB's author numbering, with ΔΔG derived in
    `Card.interface_mutations()` (`binding_ddg@1`) (#83);
  - `packet_aspects@2`: the `oligomer` aspect also covers interface mutations;
  - disease cards (#90), anchored at MONDO, resolved from DOID, Orphanet, OMIM, MeSH,
    EFO… ids only through the equivalences MONDO states (`mondo_equivalence@1`); and a
    protein's diseases grouped across sources (`medgen`, `disease_identity`,
    `Card.diseases()`, `disease_grouping@1`), a condition named at two granularities
    joining the broader disease through MONDO's hierarchy (`mondo_hierarchy@1`); and a disease's targets and drugs as
    decks (`disease_targets`, `disease_drugs`);
  - what may be done with the knowledge (#29, first milestone): `Card.terms(use)`,
    `Deck.terms(use)`, `Deck.admissible(use)`, from the terms each source states in the
    registry (`terms_propagation@1`); and terms profiles to build under
    (`terms="commercial"` or `"non_commercial"`, `terms_profile@1`, #94);
  - scientific operations (#91): `sabueso.expand`, `Card.expand` and `Deck.expand`
    (relationships into decks, `relationship_expansion@1`); `Card.explain` and
    `Deck.explain`; `KnowledgeStore.as_of`, `revision_as_of` and `changed_since`;
  - molecules given as a structure (`smiles:`, `inchi:`), matched by PubChem
    (`pubchem_structure_lookup`, #93);
  - `knowledge_state@3`: an answer cut at a limit is `partial`, with `truncated_for`
    (#88);
  - a `not_found` record states the release it was checked against (#89).
- **Watched:** card and packet size with the default ceilings (#88).

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
- `sabueso/enrichers/`: declared enrichers and their runner (#86).
- `sabueso/tools/deck/`: deck file storage.
- `sabueso/tools/resolve.py`: `sabueso.resolve`; `sabueso/tools/packet.py`: `sabueso.knowledge_packet`;
  `sabueso/tools/navigate.py`: `sabueso.expand` (#91).
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

- Offline suite: 885 tests passed, 15 online tests deselected (2026-09-29). Run with
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
