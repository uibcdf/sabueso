# Documentation Gaps

What the user guide (`docs/`) lacks. The first list (2026-01) was reviewed on 2026-09-26:
what is now covered is noted, and what remains is below.

## Covered since the first list

- Card and deck concepts, views, knowledge states, comparison: `user/concepts.md`.
- Field paths: `user/field_paths.md` (from `devguide/FIELD_PATHS.md`).
- Published selection rules: `user/selection_rules.md` and `selection_rules.json`.
- Storage (files and the knowledge store): `user/storage.md`.
- Data sources and their status: `user/data_sources.md`, generated from the registry.
- Testing: `user/testing.md`.
- A worked flow on real systems: the showcase notebook.

## Open gaps

- **The tools reference lags the API.**
  - `user/tools/` still centres on the deprecated `create_*_card_*` and `fetch_*_json`
    pages.
  - It has no page for `sabueso.resolve` and its options, for the `get_*` source-access
    functions, or for the newer sources: AlphaFold DB, BindingDB, PubChem BioAssay,
    UniChem, InterPro, the PDB CCD, NCBI Taxonomy, NCBI Gene.
  - It should be rebuilt around `resolve`, views and source access, with the deprecated
    pages marked.
- **Deck operations.** No user page for membership, lineage, `group_by_rank`, identity
  audit, the structural inventory or `unique_names`; only short entries in
  `concepts.md`.
- **Curation.** The curation workflow (curated assertions, bioactivities, engagements,
  claims, the curation store, retractions) has one page, under UniProt literature. It
  deserves its own.
- **Migration and refresh** of stored cards, for users upgrading.
- **Resolver logic.** Worked examples of ambiguity, identity findings and curated
  names.
- **Per-source coverage tables** for users: which fields and relationships each source
  fills. Today they live only in `devguide/DATA_SOURCES_STATUS.md`.
- **Integration contracts** with MolSysSuite (MolSysMT, TopoMT, PharmacophoreMT) and with
  Nextia (citing references). Not written, because not agreed yet (uibcdf/moli#3,
  moli#17).
- **Online tests**: keys and environment variables (BioGRID).
