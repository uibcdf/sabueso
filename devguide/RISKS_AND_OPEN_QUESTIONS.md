# Sabueso — Risks and Open Questions

## Risks
- **Licensing/Terms**: Some sources (DrugBank, eMolecules, ChemSpider) have licensing constraints that may affect redistribution and caching.
- **API Rate Limits**: Public APIs may rate‑limit or change formats.
- **Data Heterogeneity**: Conflicting values across sources require robust conflict handling.
- **Clinical Data Volatility**: Clinical information changes more frequently than core physchem data.

## Architecture Risks (General)
- **SourceAssertion growth**: preserving all values can create very large cards and stores.
- **Mapping fragility**: changes in source APIs can break field mappings.
- **Ambiguity**: input resolution may produce multiple valid entities.
- **Ops drift**: unstable ops contracts can break tools and downstream integrations.
- **Schema churn**: frequent schema changes can break cards, tools, and mappings.
- **Recorded Sabueso version in development environments**: `sabueso.__version__`, and
  therefore the `sabueso_version` of derivation records, comes from the installed
  distribution's metadata. If the imported code is another copy (a worktree on
  `PYTHONPATH`, or a stale `sabueso.egg-info` at the repository root), cards record a
  version that did not write them. Published packages are not affected. Frozen cards are
  therefore built from the published package (#42).
- **Concurrent curation stores** (uibcdf/sabueso#48): a `CurationStore` is rewritten
  whole on every save. The write is atomic (temporary file, then replace), but two people
  saving to the same file at the same time lose the first writer's new records: the last
  writer wins. Until the native store (#27) gives records a transactional home, use one
  store per curator or merge through version control.
- **Stored curation values** (#48): records keep the value in its stored form, so
  re-applying gives the same id. If a field's item shape changes in a new schema version,
  re-application raises instead of silently changing the id. Stores then need a
  migration.
- **Snapshots of rebuilds** (#7): a snapshot id covers everything a card stores,
  `retrieved_at` included. Two builds from unchanged sources on different days are
  therefore two snapshots. That is exact, since what was read on each day is part of the
  record, but it is not "same knowledge, same id". If consumers need that, a second
  digest that leaves out observation times can be added next to the snapshot id. It
  must never replace the snapshot id.
- **Canonical JSON is the snapshot contract** (#7): the id depends on how Python's
  `json` writes numbers and on the stored form of the card. A change to `to_dict()`
  changes the ids of new snapshots, never of stored ones, and it goes with a card
  schema version (#42). Floats use the shortest representation that round-trips, and
  NaN is refused.
- **Retention in the knowledge store** (#27): snapshots and rows are never deleted. A
  store that is saved often grows, although identical rows are stored once. Pruning
  would break pins that consumers may hold, so it needs a retention policy agreed in
  uibcdf/moli#3 before it exists.
- **Queries match references as written** (#27): `KnowledgeStore.relationships` does
  not use the glossary of entities (#52). A molecule stated as `chembl:…` in one card and
  as `pdb.ligand:…` in another is found only under each reference. Resolving through
  the glossary is the next step if cross-source queries become common.
- **Knowledge store format** (#27): the file states format 1. A change to its tables
  needs a new format and a migration, like the card schema (#42, #51).
- **Deck operations that cannot be recorded** (#58): `Deck.filter(predicate)` records
  the operation but not the Python predicate, and marks it `"reproducible": False`. A
  deck derived that way can be cited through its pinned reference, but not rebuilt from
  its parent. Prefer `in_lineage`, `group_by`, `intersect` and `difference` when the
  derivation must be reproducible.
- **One writer at a time**: SQLite serializes writers, which suits a local knowledge
  store. Many concurrent writers would need another backend.
- **ChEMBL ranges are untested against real data** (#37): ChEMBL_37 states none, so
  the mapping is guarded by a constructed record. If a release starts stating ranges,
  check how it sets `standard_relation` for them, and add a real fixture.
- **Uncertainty on section fields** (#37): only bioactivity measurements can carry
  one. A curated scalar field (for example a stated molecular weight ± error) would
  need the same node shape at its field path, and a schema version.
- **Uncertainty in the classification** (#37): an interval that spans a threshold is
  still classified by its central value. If that is misleading for a project,
  classifying the whole interval, as for ranges, is a new rule version, not a change to
  `@3`.
- **Identity audit thresholds** (#55): the near-identity bound (2% of positions,
  equal lengths, no alignment) is a flag for review, not a biological criterion.
  Proteins with indels, or strain variants above 2%, are not flagged. A position-level
  comparison through a MolSysMT alignment would replace it if needed. `same_gene`
  joins isoforms, fragments and alleles, which a reader must tell apart.
- **Strain relations by name** (#55): a strain entry whose lineage stops above the
  species is related through its name ("Trypanosoma cruzi (strain CL Brener)"). A
  taxonomy service (NCBI Taxonomy) would be exact if names prove unreliable.
- **Scheme-1 curation records** (#62): a statement dropped by the old collision cannot
  be recovered from a store. Stores stay mixed, with scheme-1 and scheme-2 records,
  until every entity is applied or saved once.
- **Card comparison scope** (#59): `compare_knowledge` takes protein cards, and
  compares relationships by their objects only, not their qualifiers. Comparing
  measured values per molecule is `compare_ligands`. Comparing two small-molecule
  cards needs its own rules (stereochemistry, salts, tautomers) and is not offered.
- **Profiles do not include predicted structures** (#57): `structural_baseline@1` was
  published before models existed, and profiles never change. If a baseline with
  models is wanted, add `structural_baseline@2`, never an edit of `@1`.
- **Model versions change** (#57): AlphaFold DB replaces models (v2 to v6 so far). A
  card records the version it saw, and a snapshot pins it. The coordinates of an older
  version may no longer be served, which MolSysMT consumers should expect.

## Open Questions
- What are the default **selection rules** per field?
- Should local cache include partial cards or only complete cards?
- How to handle **ambiguous inputs** (e.g., common names)?
- What is the **schema versioning policy** (major/minor compatibility rules)?
- What is the **local cache policy** (raw sources vs cards vs both) given licensing constraints?
- What is the **LLM integration policy** (provider, prompts, and SourceAssertion tracking)?
