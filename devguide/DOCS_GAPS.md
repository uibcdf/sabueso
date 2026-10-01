# Documentation Gaps

What the user guide (`docs/`) lacks. The first list (2026-01) was reviewed on 2026-09-26:
what is now covered is noted, and what remains is below.

## Covered

- Concepts: `user/concepts.md`.
- Resolution: `user/resolving.md`, covering queries, ambiguity, the identity audit,
  options, profiles and offline clients.
- What a protein card knows:
  - `user/structures.md`;
  - `user/sites_and_interfaces.md`;
  - `user/bioactivities.md`, with three sources and measurement identity;
  - `user/literature_and_curation.md`, covering the curation workflow, claims and the
    curation store.
- Decks: `user/decks.md`, covering membership, derivation, audits, names, inventory
  and citing.
- Storage and upgrades: `user/storage.md`, and `user/upgrading.md` (migration, refresh,
  deprecations).
- Field paths, selection rules (kept identical to the packaged rules by a test), data
  sources (generated from the registry), testing.
- Source access: `user/tools/db/sources.md`, which lists every `get_*`. The deprecated
  pages are marked, each pointing to its replacement.
- The API reference covers every module of `core`, `tools` and `mappings`.

## Open gaps

- **The showcase notebook** was run on 0.3.0. It lacks:
  - the identity audit with NCBI Gene;
  - measurements across sources;
  - names;
  - the structural inventory.
  Rebuild it (`tools/build_showcase_notebook.py`) with the next release.
- **Per-source coverage tables** for users: which fields and relationships each source
  fills. They live only in `devguide/DATA_SOURCES_STATUS.md`.
- **Integration contracts** with MolSysSuite (MolSysMT, TopoMT, PharmacophoreMT) and with
  Nextia (citing references). Not written, because not agreed yet (uibcdf/moli#3,
  moli#17).
- **Online tests**: keys and environment variables (BioGRID).
- **Sources of wave 2 and the comparative context** (0.8.0, 0.9.0): KLIFS, GPCRdb,
  SAbDab, OMA and UniRef appear only as `resolve` options and on the data sources page.
  No page shows what they state or how to read it: kinase pockets, GPCR numbering,
  antibody complexes, orthologs, a reference entry against its genome-strain entry
  (`clustered_with`, `Card.sequence_differences`).
- **Small-molecule cards** have no page of their own. Resolution, ligand decks and
  entities cover them in part.
