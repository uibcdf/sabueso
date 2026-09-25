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
- **Strain relations by name** (#55, #67): cards enriched with NCBI Taxonomy are
  related exactly. Resolver candidates and cards without that enrichment are still
  related through UniProt names, and each finding says so (`organisms: names`). If
  that proves unreliable, enrich candidates with NCBI Taxonomy in the resolver.
- **NCBI Taxonomy has no data release** (#67): the Datasets API states its software
  version, not a taxonomy release, so `annotations.taxonomy` records no source version.
  Taxonomy changes (merged or renamed taxa) show up as a different snapshot, not as a
  new release.
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
- **Engagement vocabulary** (#61): the mechanisms (`covalent`, `non_covalent`,
  `allosteric`, `interface_disruption`, `unspecified`) are Sabueso's, not an ontology.
  If Praxis or Nextia need a shared vocabulary, raise it in uibcdf/moli, and map these
  terms onto it with a new schema version.
- **Numbering of engaged residues** (#61): papers often number residues from a
  construct or a structure, not from UniProt. The residue-code check catches most
  slips, but it cannot catch a shift that lands on the same amino acid. Curators
  should give the code whenever the paper does.
- **UniChem lags behind BindingDB** (#66): recent monomers (5 of the HsTIM records,
  from a 2024 paper) are not in UniChem yet, so they cannot be anchored and are
  reported as `molecule_unresolved`. They are not grouped, even when ChEMBL states the
  same values.
- **One UniChem request per monomer** (#66): fine for tens of records, too slow for
  targets with thousands (kinases). Use UniChem's source-to-source mapping files, or
  batch lookups, before enriching such targets by default.
- **BindingDB records state no origin through REST** (#66): the provenance layer cannot
  tell a ChEMBL import from BindingDB's own curation. The bulk download states it. It
  also decides the licence (CC BY-SA 3.0 for imports), so the REST records are treated
  as CC BY-SA 3.0.
- **Censored values are not reviewed** (#66): pairs with `>` or `<` values and
  different molecules are frequent within one paper and are not listed. A real
  discrepancy among censored values goes unnoticed.
- **PubChem standardisation** (#68): a copy's CID can lose the depositor's
  stereochemistry or salt form. Within a named assay, grouping by connectivity is
  accepted only when it leaves one candidate, and it is flagged; seven TcTIM copies find
  no molecule of their assay at all, and stay unresolved.
- **Pointers can be large** (#68): a copy can name an assay with thousands of
  activities, all fetched from ChEMBL. That is fine for curated assays; screening
  assays deposited through ChEMBL may need a limit.
- **Refresh options are rebuilt from enrichment records** (#51): options that leave no
  enrichment record (a resolver preference policy, the name query a card came from)
  are not reproduced. A refresh resolves the card's anchor directly, so the entity
  cannot change, but its options may. `refresh_card(**options)` can override them.
- **Gaps of qualifier-level additions** (#51): `SCHEMA_CHANGES` names relationship
  qualifiers by their relationship, so an added qualifier (for example `isoform`) is
  reported only when the relationship itself is absent. The exception is a qualifier
  that every relationship fetched with its schema has (`has_structure.construct`,
  marked `qualifier` in `SCHEMA_CHANGES`). Its absence from every relationship of the
  predicate is a gap. A card whose older structures were never re-fetched is still
  counted as holding it once any structure has it.
- **Structural state is only as good as RCSB's annotations.** `structure_state@1` calls a
  structure `mutant` when RCSB states an engineered mutation, and `differs` when the
  sequences differ without one. A mutation the depositor did not annotate, in a region
  the entity alignment does not cover, is invisible. The `subject_of_investigation`
  flag decides `ligand_of_interest`. It is missing for some older entries (`unstated`)
  and can mark a buffer component. The inventory groups by these states; it must never
  be read as a recommendation.
- **One request per PDB entry.** `structures="all"` fetches entries one by one. A
  protein with hundreds of entries (kinases, proteases) will be slow and may meet rate
  limits. RCSB GraphQL accepts `entries(entry_ids: [...])`; batch when that is felt.
- **Claims can hide structure** (#43): free text is easy to add and cannot be
  compared, so claims could pile up where a structured field should exist. Review the
  topics periodically, and promote a recurring topic to a field.
- **Names are not identities.** UniProt's synonyms, abbreviations and gene names are
  recorded per entry as that source states them. Short names are ambiguous across
  proteins ("TIM" names both a triosephosphate isomerase and unrelated protein
  families), and gene symbols repeat across organisms. No rule may join two entities,
  or anchor a resolution, by a shared stated name. Resolution by name stays with the
  source's search and the identity audit. Curated synonyms anchor only through a
  curation store, and a name curated for two entries is ambiguous. If a view of shared
  names across a deck is ever added, it must report the coincidences, never merge them.

## Open Questions
- What are the default **selection rules** per field?
- Should local cache include partial cards or only complete cards?
- How to handle **ambiguous inputs** (e.g., common names)?
- What is the **schema versioning policy** (major/minor compatibility rules)?
- What is the **local cache policy** (raw sources vs cards vs both) given licensing constraints?
- What is the **LLM integration policy** (provider, prompts, and SourceAssertion tracking)?
