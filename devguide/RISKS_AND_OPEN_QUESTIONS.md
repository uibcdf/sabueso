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
- **Knowledge store format** (#27): the file states its format, 2 since #99, and
  upgrades format 1 in place. A change to its tables needs a new format and an upgrade,
  like the card schema (#42, #51).
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
- **The rank vocabulary is Sabueso's copy of NCBI's.** `group_by_rank` refuses a rank
  outside `NCBI_RANKS` (`_private/argdigest/argument/rank.py`), so that a typo is not
  answered with an empty grouping. A rank NCBI adds later (as "realm" and "cellular
  root" were) is refused until it is added there.
- **The documentation is not built in CI.** A broken page or a malformed docstring is
  caught only by the local docs gate (`TESTS.md`). The user guide had drifted far behind
  the API by 0.4.0: stale selection rules, a wrong release badge, no page for
  `resolve`. A docs job in CI, building with `-W`, would prevent it.
- **A support library can change a behaviour in a minor release.**
  - SMonitor 0.17.0 (2026-09-26) began skipping its own frames in `stacklevel`
    (uibcdf/smonitor#23). Sabueso's frame count then double-skipped, and warnings
    pointed into pytest.
  - Main requires SMonitor >= 0.17.0 and counts accordingly.
  - Published Sabueso 0.4.0 declares `smonitor>=0.16.0`, so a fresh install gets 0.17.0
    and attributes its warnings to the wrong line. This is cosmetic: messages, records
    and results are unchanged. The next release fixes it.
  - Lower bounds alone do not protect a published release from such changes. Upper
    bounds, or a release test against the newest support libraries, would.
- **RCSB answers can change from day to day.** On 2026-09-26, RCSB failed server-side
  on the per-chain data of some entries (1KLG, 2V5B, 1KLU), intermittently. Entries
  are now kept as `partial` (#74). Two runs a day apart can still differ in what they
  hold, and a refreshed fixture can be partial. Fixtures are refreshed only from
  complete answers.
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
- **A deletion is read from an empty field** (#80). UniProt's JSON writes "Missing" as an
  empty `alternativeSequence`, and nothing else says so. If UniProt changes that
  convention, a deletion could again read as an unspecified change, or a change as a
  deletion. It was checked against the text format on 2026-09-27, and
  `test_isoforms_offline.py` holds it on frozen entries. Recheck when fixtures are
  refreshed.
- **Secondary structure out of context.** UniProt reads each segment from one PDB entry,
  and mixes entries along one sequence. A consumer that paints it on another structure,
  another state or an isoform shows what those structures do not state. The item keeps
  `structures`, and each structure now carries its own per-chain assignment (RCSB,
  since 0.3.6). Assignments by different programs (PROMOTIF, DSSP, authors) can
  disagree at segment ends; `assigned_by` says which one a chain has.
- **Packet size** (#71). A packet holds the views' output whole. Measured live on
  2026-09-27 for the HsTIM/TcTIM pair: about 0.8 MB of JSON with ChEMBL bioactivities,
  and about 1.2 MB with ChEMBL, BindingDB and PubChem BioAssay (0.8 MB of it TcTIM's
  bioactivities). A protein with thousands of measurements will be much larger. If that
  is felt (MOLI Agent's context, storage), facts may become summaries with references
  to the full views, in a new packet version.
- **What the content-equivalence id leaves out** (#71). It drops `retrieved_at` and
  `sabueso_version` only. A new field that records when or by what something was built
  would make unchanged knowledge look changed, until it is added to `NOT_KNOWLEDGE`
  (`sabueso/core/packets.py`). On 2026-09-27, cards built live held no other time value
  than `retrieved_at` (dates such as a PDB deposit are knowledge, and stay). Recheck
  when a field is added.
- **The packet contract may change** when uibcdf/moli#22 is agreed. Stored packets
  state their format (`knowledge_packet@2` since #88; `@1` is still read), so a change
  is a new version, and revisions of different formats are never compared.
- **Whole-release sources** (#83). PHI-base's first load parses a 134 MB JSON: about
  30 s and 750 MB of memory once per process without a cache directory. A larger
  release, or several release-based sources, would need streaming parsing or a
  prebuilt index. The cache directory is the mitigation today.
- **Terms not stated** (#84). VEuPathDB and TDR Targets state no reuse terms that were
  found. Until they answer, their data is read live only, never committed as fixtures or
  redistributed.
- **Sources that refuse unnamed clients** (#82). DISEASES's download server and
  Reactome's Content Service answer 403 to Python's default user agent. Since #86 every
  client names Sabueso through one helper (`tools/db/_http.py`), and a test keeps it so.
- **Large default answers** (#88). By default every source is asked for everything, up
  to 5000 items. For heavily studied human genes this means thousands of
  SourceAssertions per card: Open Targets holds 5198 associations for TP53, and ClinVar
  16094 records for BRCA1, about a minute to fetch 5000 of them. Card size, store size
  and packet size may grow past what views and MOLI consumers expect. #88 lists what to
  watch and the options.
- **Heavily studied targets** (#98). Measured live for EGFR on 2026-09-30: ChEMBL
  holds 58,847 activities (~7 s per 1000-row page, server side), BindingDB 32,346
  records of 16,463 monomers (each needing a UniChem lookup), PubChem 6569 assays, RCSB
  393 entries (~175 KB of card each). BindingDB and PubChem BioAssay ignore the 5000
  ceiling. A card with every source would exceed 100 MB and take hours. #98 lists the
  batched queries the sources offer, and the order of work.
- **Store growth across rebuilds** (#99, addressed on main). Format 2 keeps
  `retrieved_at` out of a SourceAssertion's row, numbers states and rows with integers,
  and compresses: a card saved again with unchanged knowledge adds about 0.1 MB instead
  of a whole copy. What still grows with each revision is one membership row per
  statement; the retrieval archive (#100) will add responses, which licences and
  freshness decide.
- **Transcript versions** (#85). gnomAD states the version of the canonical transcript
  it annotates (gnomad_r4 uses GENCODE 39), and UniProt cross-references its own. They
  can differ when either updates, and then the same id may encode another protein.
  The residue check guards each placement, and the item records gnomAD's version; the
  versions are not compared yet.
- **Variants on transcripts UniProt does not state** (#85, closed; follow-up #102). After asking gnomAD for the
  canonical transcript, 1,682 of 52,928 protein changes over 22 human proteins remain
  unplaced for this reason (`transcript_not_canonical`). Checked one by one, none is
  coding on the canonical transcript: they are intronic or in its 3' UTR, or outside
  it. The card still says only that the transcript is not canonical. gnomAD's variant
  query would state which (25 variants per request, within its rate limit), and
  isoform expression by tissue would say where each change matters (#102).
- **KLIFS's terms are a statement, not a licence** (2026-09-30). Its FAQ says all data
  is free and open for academia and industry, and asks for a citation; no licence text
  was found. The registry records it as no restrictions of its own, with that caveat.
  If KLIFS publishes a licence, the terms record is reviewed.
- **One structure places a kinase's pocket.** KLIFS states pocket residues one
  structure per request. If the chosen structure's author numbering disagrees with
  another's at a pocket position, the card shows only the chosen one, and the residue
  check is the guard.
- **GPCRdb's own copy of a sequence** (2026-09-30). GPCRdb numbers residues on the
  sequence its entry states. When UniProt revises the sequence and GPCRdb has not yet,
  the numbers stay in GPCRdb's numbering (`sequence_differs`) until both agree: correct,
  but a card loses its placed residues until then.
- **Annotations RCSB integrates carry their own origin** (2026-09-30). Membrane
  segments (OPM, PDBTM) and secondary structure (PROMOTIF, DSSP) reach cards in RCSB's
  statement, with the resource that assigned them. The statement's terms are RCSB's
  (CC0); the assigning resource's own terms, where it states any, are not recorded
  separately. No licence was found for OPM on its site.
- **OMA answers HTTP 502 to about one request in three** (measured 2026-10-01, however
  spaced). Its client tries a request up to 4 times beyond the general retries (on
  main since 0.8.1); a failure is still recorded as `error`, never as absence.
- **Live sources fail now and then** (#97). In one day of eight full pilot builds,
  BindingDB failed three times (a 200 whose body was not JSON), and ChEMBL (HTTP 500),
  OMA, PHI-base and Reactome once or more. Unreadable answers and HTTP 500 are now
  retried and recorded (`quality.retries`); a failure that persists is still an
  `error`. Repeated builds can also reuse what succeeded (the retrieval archive, #100).
- **gnomAD's rate limit.** The service answers HTTP 429 after bursts (about ten
  requests a minute sustained). Sabueso retries with backoff. A build that asks many
  genes in a row may still see errors, recorded as `error`, never as absence.

## Open Questions
- **Which isoforms, and which variants, are tissue-specific?** (#102; a need the
  maintainers recorded on 2026-09-30. **Variants: answered on 2026-10-01** by gnomAD's
  pext and `Card.variant_tissue_usage()`, `pext_at_variant@1`. Isoforms: answered the
  same day by `Card.isoform_tissue_usage()`, `isoform_exon_usage@1`, with UniProt's
  statements restricted to each isoform. Still open: tissues as UBERON terms, and
  isoforms whose transcripts gnomAD does not annotate.) A card states a protein's isoforms and places
  each population variant on the canonical isoform, or says why not
  (`isoform_specific_position`, `not_coding_on_canonical`, `transcript_not_canonical`).
  It does not say where each isoform is expressed. So it cannot tell a change that
  matters only in one tissue from one that matters everywhere, for example PKM1 against
  PKM2, or MAPT's neuronal exons. Resolving it needs a stated source of isoform
  expression by tissue (gnomAD's `pext`, GTEx transcript expression), with its release.
  It also needs a named rule that places a variant within the transcripts each tissue
  expresses. The source and the rule are open.
- What is the **LLM integration policy** (provider, prompts, and SourceAssertion tracking)?
  An LLM output would be stored as a SourceAssertion whose source is the model, the
  prompt and the documents it read, never as Evidence. Nothing is decided beyond that.
- Should Sabueso keep a **raw-payload cache** for heavy enrichments, and how would
  licences constrain it (`CACHE_POLICY.md`)?
- Which **reference form** will MOLI agree for cited knowledge (uibcdf/moli#3, #53)?
- How does **derived knowledge promoted by a project** live in Sabueso, if at all
  (uibcdf/moli#17)?

Answered since the first list (2026-01):
- default selection rules: `SELECTION_RULES_EXAMPLES.md` (#10);
- ambiguous inputs: they are reported, never chosen (`DATA_FLOW.md`, #55);
- the schema versioning policy: `SCHEMA.md` (#42), and migration (#51);
- the local store: `CACHE_POLICY.md`, `STORAGE_LAYOUT.md` (#7, #27). Cards are stored
  whole, so the question of partial cards does not arise.
