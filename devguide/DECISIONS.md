# Sabueso — Decision Log

## Language & Ecosystem
- Language: **Python**.
- Scientific OSS standards:
  - tests with **pytest**
  - documentation with **Sphinx**
  - package distribution via **conda**
  - development in a **conda micro‑environment**

## Core Data Model
- Output is a **card** with nested sections and strict field ordering.
- Card types: **ProteinCard**, **PeptideCard**, **SmallMoleculeCard**.
 - **Deck** is a first‑class object for collections of cards.
- Identifiers use direct paths: `identifiers.<db>` (no `secondary_ids`).

## SourceAssertions and Provenance (Critical)
- **Uniform SourceAssertion model** for all fields, no exceptions.
- A SourceAssertion records what an external source asserts about an entity or property.
- Cards store **resolved values** only.
- All raw values from all sources are stored as SourceAssertions in `source_assertion_store`,
  which is serialized with the card.
- Each field points to one or more `source_assertion_ids`.
- `selection_rules` is explicit and versioned.
- `quality.conflicts` records unresolved disagreements.

## All‑Values Policy
- **All values from all sources must be preserved**, never discarded.

## Clinical Layer
- Clinical data is included as a **separate layer**:
  - pharmacology
  - ADMET
  - clinical trials
  - pharmacovigilance
  - indications
  - contraindications
  - interactions

## ProteinCard Enhancements
- Protein cards include a **disease** section with disease associations and their SourceAssertions.
- Protein cards include **ligands** with a `role` attribute (e.g., inhibitor, activator, substrate).
- Protein cards provide an operation to **extract a Deck of inhibitor cards**.

## Positional Location Model
- Positional features support both **sequence‑based** and **structure‑based** locations.
- This is required for interoperability with TopoMT and visualization tools.

## Ambiguity Handling
- Ambiguous inputs should return a **Deck** rather than a single Card.
- Ambiguity must be explicit in the output (metadata or quality section).

## Tools API (Public)
- Tools are organized into:
  - `tools.db.*` (per‑database modules)
  - `tools.card.*` (operate on Card)
  - `tools.deck.*` (operate on Deck)
- Tools are intentionally **ad‑hoc** and **heterogeneous** (no common protocol).

## Versioning
- Version strings use **x.y.z** (no leading `v`). Third-party API URLs may include their own
  version segments (e.g., `/v1/`); do not change those.
- Release, card schema, file formats, rules and profiles are separate namespaces (MOLI
  release version policy):
  - card schema `x.y.z`;
  - deck file and curation store: integer `format`;
  - derived rules and enrichment profiles: `name@N`, immutable once published;
  - selection rules: `x.y.z`.
- Views (`Card.structures()` and the others) are Python API, not schema. They change
  with releases, and deprecations are warned about.

## Card schema versioning (2026-09-24)
uibcdf/sabueso#42; the rules are in `devguide/SCHEMA.md` ("Versioning policy").
- Before 1.0, `z` grows with additive optional fields and `y` with anything else. From
  1.0 on, semver.
- A schema version is fixed once a release publishes it. Until then, additive changes
  accumulate in the next version.
- Readers:
  - read their own line, and newer versions of it with a warning, keeping unknown keys;
  - refuse other lines until an explicit migration exists (#51);
  - refuse cards without a version.
- Guards:
  - a frozen card per published schema must stay readable;
  - the recorded card shape must match what the code writes;
  - a published version's shape cannot be rewritten.

## Cache/Store Policy (Pending Decision)
- Decide whether local cache stores **raw source data**, **cards only**, or **both**.
- This must respect licensing constraints.

## Core Ops (Pending Decision)
- Define a minimal, consistent set of **CardOps** and **DeckOps** (compare, filter, sort, expand, etc.).

## Resolver (In Progress)
- Resolver contract defined in `devguide/RESOLVER.md` (0.2.0; selection-rules format 0.1.0).
- Field-level resolver implemented in `sabueso/resolver/field_resolver.py` with tests.
- Field examples documented in `devguide/SELECTION_RULES_EXAMPLES.md`.
- Selection rules are published in docs (`docs/selection_rules.rst`) and machine-readable (`docs/selection_rules.json`).

## Online‑First
- Sabueso is **online‑first**.
- Local card caching is optional and does not replace live queries.

## Terminology: SourceAssertion ≠ Evidence ≠ Provenance (2026-09-23)
- The former Sabueso "evidence" object is renamed **SourceAssertion**: what an external
  source asserts about an entity or property. `EvidenceStore` → `SourceAssertionStore`,
  `evidence_store` → `source_assertion_store`, `evidence_ids` → `source_assertion_ids`,
  mapping outputs `evidences`/`field_evidence` → `source_assertions`/`field_source_assertions`,
  ID prefix `E_` → `SA_`.
- **Evidence** is reserved for Nextia (project-contextual support, contradiction or
  information about a Question/Hypothesis). **Provenance** is cross-cutting.
- Rationale: avoid a permanent ambiguity for humans and MOLI Agent, and follow MOLI Platform
  Architecture 1.0 (`uibcdf/moli`): "External knowledge does not automatically become
  project Evidence".
- Source-native qualifiers (UniProt ECO codes, PubMed IDs, assay descriptors) stay in
  `source_metadata` under their native names; Sabueso defines no generic `evidence` field.
- No deprecated aliases: Sabueso had no release or external consumer when renamed.
- Formal card schema bumped to `0.2.0`; Resolver contract bumped to `0.2.0`.

## SourceAssertion contract aligned with MOLI (2026-09-23)
- SourceAssertion fields follow MOLI Platform Architecture 1.0
  (`schemas/sabueso_source_assertion_conceptual_schema.md`): `id`, `subject_ref`,
  `field_path`, `asserted_value`, optional `normalized_value`, `source`
  (`type` ∈ database|literature|patent|curated|other), `retrieved_at`,
  `source_metadata`, optional `provenance_ref`.
- `subject_ref` is `<namespace>:<record_id>` of the source record (e.g. `uniprot:P52789`);
  linking it to a Sabueso entity is the job of the future EntityResolver.
- The resolver works on `normalized_value` when present, else on `asserted_value`.
- Cards carry a stable `meta.card_id` (`sabueso:<entity_type>:<subject_ref>`, provisional
  syntax) and `meta.schema_version`; SQLite persistence keys cards by `card_id`.
- Sabueso is the Knowledge component of the MOLI Platform's Scientific Context, not a
  MolSysSuite member (MolSysSuite admission withdrawn, `uibcdf/molsyssuite#40`).

## Entity identity, relationships and structures (2026-09-23)
Agreed contract in `devguide/archive/entity_resolver.md` (uibcdf/sabueso#6):
- **Protein identity:** anchored on a UniProt record. Use the reviewed canonical entry
  when one exists; otherwise apply an explicit, recorded preference. Anchor changes are
  recorded as `superseded_by`, never rewritten silently. Consumers treat references as
  opaque.
- **Ambiguity:** resolved only by a named, versioned preference policy
  (`prefer_reviewed@1`). The non-preferred candidates are kept on the Card as
  `alternatives` and never feed fields. Preferences never cross organisms, and identical
  sequences in different organisms are never identity.
- **Relationships:** first-class, with deterministic ids. They are backed by
  SourceAssertions, or by a derivation record when inferred. They are stored with the
  subject Card; re-evaluation in uibcdf/sabueso#19.
- **Structures:** no StructureCard. The ProteinCard exposes a `structures` view over
  `has_structure` relationships, which carry mandatory raw qualifiers (chains, range,
  coverage, other entities present) and a derived classification with visible thresholds.
  Structure facts keep `pdb:<id>` as subject. Re-evaluation in uibcdf/sabueso#20.
- **General rule:** possible future problems of a design decision are recorded in
  `devguide/`, and decisions that need later re-evaluation get an issue with explicit
  triggers.


## Small-molecule identity (2026-09-23)
Decided by the Sabueso owner (uibcdf/sabueso#25, `devguide/archive/molecule_identity.md`):
- **Anchor:** a small molecule is anchored at its standard InChIKey. Its card id is
  `sabueso:small_molecule:inchikey:<key>`.
- **Links:** source records (`chembl:`, `pdb.ligand:`, and the DrugBank, PubChem, ChEBI
  and BindingDB records listed by UniChem) are linked to `inchikey:<key>` with `same_as`,
  supported by the source that states the key.
- **Standard keys only:** records without a standard InChIKey are reported as
  unanchored, never guessed.
- **Variants are not merged:** charge, salt, stereochemistry and tautomer variants have
  different anchors. A future connectivity-level link must be a derived
  `possibly_same_as`.
- Rejected alternatives: a preferred source record (no chemistry source is universal),
  and the UniChem compound id (internal to one service).

## Computable properties are recorded, not computed (2026-09-23)
Proposed in uibcdf/sabueso#25 and accepted by the Sabueso owner. It is the boundary for
uibcdf/sabueso#10.
- **What Sabueso does:** it records the physicochemical properties that sources state
  (logP, TPSA, rotatable bonds, molecular weight, ...). Each value is a SourceAssertion,
  traceable to the source that computed it and to its method. Different methods give
  different values, and they are qualified by method (#10), never reconciled by
  recomputation.
- **What Sabueso does not do:** it does not compute those properties itself. Running a
  descriptor, a fingerprint or a similarity over a structure is modelling. Modelling
  belongs to MolSysSuite, not to the Knowledge component of the MOLI Scientific Context.
  A value computed by Sabueso would have no source to cite.
- **In practice:**
  - no module of the `sabueso` package imports a chemistry toolkit (RDKit, Open Babel,
    OpenEye, Mordred, ...). Toolkits may be used in tests or tooling, never to feed a
    card. `tests/core/test_boundaries_offline.py` enforces this;
  - a computed property, if ever needed on a card, arrives as a MolSysSuite result with
    its own derivation record. It never appears as a SourceAssertion;
  - similarity and fingerprints are the same case, and the more tempting one: "molecules
    similar to this inhibitor" looks like knowledge, but it is a calculation.
- **Scope:** if this boundary starts to bind other MOLI components, it becomes a shared
  contract to raise in `uibcdf/moli`.

## Guard by default against entity merges (2026-09-23)
Closes uibcdf/sabueso#21 (`devguide/archive/legacy_entity_paths.md`).
- `build_card_from_mapping` refuses fields fed by assertions about several subjects,
  unless the caller passes `entity_subjects` after resolving their identity.
- There is no unguarded merge path: a false entity merge is worse than an unresolved
  conflict.
- Small molecules have one identity scheme: every card is anchored at the standard
  InChIKey, whatever the source of its records (ChEMBL, PubChem, PDB CCD).

## Resolution compares like with like (2026-09-23)
Closes uibcdf/sabueso#10 (`devguide/archive/physchem_normalization.md`).
- Every field is resolved from its SourceAssertions, with the packaged rules when none are
  given. A multi-source field never takes the last value merged while citing every source.
- Values are compared only when they measure the same thing: within one method
  (`compare_within`), within one source for representations only a toolkit can
  canonicalise (SMILES), and within the precision each source states
  (`numeric_agreement: "stated_precision"`). The rest are `alternatives`, visible and never
  conflicts; real disagreements stay `conflicts`.
- Items of a list field are a union, not competing values.
- A small molecule's properties describe the structure its card is anchored at (ChEMBL
  `full_mwt`, not the parent's `mw_freebase`).

## Quantities travel with their units, sealed (2026-09-24)
uibcdf/sabueso#32 (`devguide/archive/quantities.md`); the format is PyUnitWizard's
`QuantityRecord` (released in 0.27.0; design in uibcdf/pyunitwizard#83).
- Sabueso answers quantity questions with quantities, and stores every quantity as
  `{value, unit}` in PyUnitWizard's canonical spelling.
- Stored cards seal their quantities (one QuantityRecordBundle, columns by path and
  unit); loaders verify, and there is no default unit.
- Bioactivity concentrations are normalized to nanomolar with explicit conversions; the
  source's value and unit are kept verbatim. pChEMBL is kept as ChEMBL states it.
- Sabueso never sets PyUnitWizard's session policy; stored numbers do not depend on it.
- Every place a card stores quantities, and its unit, is declared in
  `quantities.NEGOTIATED_UNITS`. The writer refuses anything else, and the reader
  declares those units' dimensionalities itself. It never takes its expectations from
  the card it verifies.
- Plausibility is checked, never corrected: `pchembl_consistency@1` and
  `unit_scale_discrepancy@1` flag measurements, and resolver conflicts mark exact 10³ or
  10⁶ ratios. Closes uibcdf/sabueso#32.

## Curated literature assertions (2026-09-24)
uibcdf/sabueso#41, part 2. Free-text claims are deferred to uibcdf/sabueso#43.
- A person or an agent reads a paper and records what it states. Sabueso does not read
  papers: it checks the shape against the field, stores the claim as a literature
  SourceAssertion, and compares it mechanically.
- Only existing knowledge fields and relationship predicates take curated assertions.
  Identity, sequence, metadata, identity links, `has_structure` and `described_in`
  never do.
- Curated bioactivities (uibcdf/sabueso#44):
  - the molecule carries its full identity: its InChIKey and every record linked to it,
    resolved by Sabueso rather than typed by the curator;
  - a curated measurement is compared only with ChEMBL measurements of the same
    publication, the same molecule and the same type, at the precision it was stated
    with;
  - the curator states whether it was measured on this protein or on an ortholog.
- A curated assertion never takes priority automatically ("Literature" is in no priority
  list), and it is never discarded. Its outcome is always recorded (`quality.curation`).
  A difference is reported in `quality.conflicts` and warned about
  (`SABUESO-W-CURATION-001`).
- On list fields, "differs" means the same item, identified by position and
  substitution, site or disease accession, stated differently. Whether two texts
  contradict each other needs a reader, so Sabueso flags the difference and never
  judges it. Free-text lists are `not_compared`.
- Quantities are compared at the precision they were stated with, converted to the
  field's unit ("0.9 kDa" states hundreds of daltons).
- How a curated assertion bears on a project's hypotheses is Nextia Evidence
  (SourceAssertion ≠ Evidence).
- Curations survive rebuilds through a `CurationStore` (uibcdf/sabueso#48):
  - a JSONL file of what was curated, never a card;
  - applied when a card is built, with the same content-derived SourceAssertion ids;
  - outcomes are recomputed, and changes are reported;
  - retractions are kept and never applied.

## Enrichment profiles (2026-09-24)
uibcdf/sabueso#45.
- A profile names a set of card-tool options, and its version is part of the name
  (`structural_baseline@1`). A published profile never changes: a change is a new
  version.
- Explicit options override a profile. The profile, the options it gave and those
  overridden are recorded in `quality.entity_resolution.decision.profile`, so a card
  says how it was built.
- Profiles hold Sabueso's own options only. A study's methodology, meaning why this
  baseline, belongs to Praxis.

## Three public layers (2026-09-24)
uibcdf/sabueso#49, `devguide/SOURCE_ACCESS.md`.
- The layers are source access (raw records in a provenance envelope), mappings
  (SourceAssertions) and cards (resolved knowledge). Each is public.
- Each source has one module with one set of clients, shared by card building and
  direct queries.
- Sabueso retrieves knowledge records, never coordinate files; loading structures
  belongs to MolSysMT.

## Glossary of entities (2026-09-24)
uibcdf/sabueso#52 (Diego's proposal).
- A card lists each molecular entity it mentions once (`entities`). Relationships keep
  their source's record, which is their provenance, and the glossary resolves it to an
  entity.
- Identity is stated, never guessed: records merge only on a source's statement.
- What a curator states is the molecule as given and its InChIKey. The records UniChem
  links are identity knowledge in the glossary, so curated ids do not change when UniChem
  learns a new record.

## Tables and optional dependencies (2026-09-24)
uibcdf/sabueso#46.
- `Card.table(view, **options)` gives flat rows. Quantities stay quantities. Lists
  become `"; "`-joined text.
- `sabueso.to_dataframe(rows, units=None)` gives numbers only in a unit the caller
  names: the unit goes into the column name and `df.attrs["units"]`. A column holding
  several kinds (nanomolar and percent) is refused rather than half converted.
- pandas is optional, and DepDigest checks it at call time (`sabueso/_depdigest.py`,
  `LibraryNotFoundError`). DepDigest therefore now applies to Sabueso, the condition
  recorded in #31.


## Card snapshots and the knowledge store (2026-09-25)
uibcdf/sabueso#7 and #27. The design is recorded in
`devguide/archive/card_versioning_snapshots.md` and `devguide/archive/native_store.md`.
- **A snapshot is content-addressed.** `Card.snapshot_id()` is the SHA-256 of the stored
  card (`Card.to_dict()`) in canonical JSON, with the quantities seal left out and
  SourceAssertions and relationships in canonical order. The same state always has the
  same id, whoever computes it and wherever the card is kept, so a JSON copy can be
  checked against a pin without a store.
- **A revision is what a human reads.** A store records the order in which a card's
  snapshots were saved, when, and with a note. Both at once: the revision for people, the
  hash for identity and integrity.
- **References (provisional, uibcdf/moli#3):** `<card_id>` for the latest state,
  `<card_id>@sha256:<hex>` for one exact state, and `…#SA_…` or `…#REL_…` for an item in
  that state. An item reference must be pinned. A pinned read returns that exact state
  or fails; it never returns another one.
- **The knowledge store is normalized SQLite** (`sabueso.KnowledgeStore`). A card's
  document, meaning its sections, quality, rules, entities and meta, stays one JSON
  column. SourceAssertions and relationships become rows keyed by their content, and are
  shared by every snapshot that holds them. Relationships are indexed by object,
  subject and predicate. Decks are stored by name as their meta and the pinned states of
  their cards.
- **Rows are keyed by content, not by id.** A SourceAssertion id names what was stated,
  so the same statement from another source release is a different row. Two cards share
  a row only when they state exactly the same thing. Different subjects never do.
- **JSON/JSONL stay the exchange formats.** `save_card_sqlite` and `save_deck_sqlite`
  stay as they are. `KnowledgeStore.import_card_table` turns their rows into history.
- **The store's tables are Sabueso's implementation.** Other components rely on the
  reference forms, not on the tables.

## Ranges and stated uncertainty (2026-09-25)
uibcdf/sabueso#37; card schema 0.3.2; rule `bioactivity_class@3`.
- **A range keeps both ends,** verbatim and normalized: `upper_value` and
  `normalized_upper`. It is classified by its band when both ends share one, and is
  `inconclusive` across a threshold. A range is never read as its lower end, and takes
  no pChEMBL check and no scale comparison.
- **ChEMBL_37 states no range.** `standard_upper_value` is null in all 24,527,044
  activities (checked through the API on 2026-09-25). The ChEMBL path is kept for
  fidelity, guarded by a constructed record. Ranges read in papers are the case that
  occurs.
- **Uncertainty is Sabueso's representation,** since PyUnitWizard defines none.
  `normalized_uncertainty` is `{kind, half_width | lower, upper, level?, n?}`, with
  quantity nodes in the measurement's normalized unit. The kinds are `sd`, `sem`,
  `unspecified` (a bare "±") and `ci`. As written, it is part of the curated statement
  and of its id. No database Sabueso maps states an uncertainty.
- **Uncertainty changes neither the class nor agreement.** The class is read from the
  central value. A curated value agrees with ChEMBL's reading of the same paper when
  the numbers agree at their stated precision: agreement is about transcription, not
  about the spread of the measurement. A point and a range never agree.

## Organism identity, gene loci and orthology groups (2026-09-25)
uibcdf/sabueso#54; additive, card schema 0.3.2.
- A protein card states its organism's NCBI taxon (`annotations.taxon_id`) and its
  lineage (`annotations.lineage`, from the root down, the organism excluded), as
  UniProt states them. UniProt's taxon is strain-level when the entry is, so no
  separate strain field is needed.
- `identifiers.gene_loci` lists gene loci in organism databases: VEuPathDB components
  (TriTrypDB, GiardiaDB, HostDB…) and NCBI Gene. A reviewed entry can gather the loci
  of several strain genomes (TcTIM lists 11). Loci are the identity anchors that tell
  paralogs apart (#55); sequence similarity never is.
- OrthoDB and eggNOG groups are `classified_in` relationships, like the other
  classifications. A missing group is "not stated", never "not an ortholog": UniProt
  gives HsTIM an OrthoDB group and TcTIM none.
- `Deck.in_lineage(taxon)` keeps cards whose organism is or descends from the taxon.
  Cards whose lineage is not stated are listed apart, not dropped silently.
  `Deck.group_by(field_path)` groups by a resolved value.

## Identity hygiene (2026-09-25)
uibcdf/sabueso#55 and #62.
- **Identity never comes from sequence similarity.** Paralogs can be closer in
  sequence than redundant entries of one protein: two Trichomonas vaginalis
  paralogs differ in 4 of 252 positions, while human P60174 and Q53HE2 differ in 1
  of 249.
- **Rule `protein_identity_audit@1`** (`sabueso/core/identity_audit.py`) compares two
  entries of related organisms. Related means the same taxon, one in the other's
  lineage, or a strain name extending the species name. The steps:
  - a shared gene locus with an agreeing sequence gives `possibly_same_as`, and with
    another sequence gives `same_gene` (isoforms, fragments, alleles);
  - distinct loci of one genome give `distinct_genes`;
  - otherwise, an identical or near-identical sequence gives `possibly_same_as`.
    Near-identical means the same length and at most 2% of positions differing,
    compared position by position. Different lengths are not compared: aligning
    belongs to MolSysMT.
- **Nothing merges.** `possibly_same_as` is a flag for review. The resolver records
  the findings among search candidates (`decision["identity_audit"]`), and
  `Deck.identity_audit()` among a deck's protein cards.
- **Named anchors are curated.** A curator states a name for an entry
  (`names.synonyms`, with a publication). `resolve(EntityQuery(name=...),
  curations=store)` answers from that anchor before any search (rule
  `curated_name`). A name that designates two entries is ambiguous, and a name
  anchored in another organism does not answer the query.
- **Curated ids include the subject** (id scheme 2, #62). Stores written earlier are
  re-identified record by record when applied or saved, and the old id is kept.

## Knowledge states (2026-09-25)
uibcdf/sabueso#56; rule `knowledge_state@1`.
- `card.knowledge_state()` and `card.table("knowledge_state")` give one row per area
  and source: `known`, `conflicting`, `not_stated`, `not_queried` or `unavailable`,
  with the source release, a count and the basis.
- `not_stated` means the source was consulted and states nothing. For UniProt this
  covers every field and relationship its mapping can give (`STATED_FIELDS`,
  `STATED_PREDICATES`). For enrichments it means the request answered with nothing.
  The basis keeps the reason: "no ChEMBL cross-reference in the UniProt entry" means
  ChEMBL was not asked, not that ChEMBL has no data.
- `not_queried` means the enrichment was not requested; `unavailable` means a request
  failed and nothing was stated.
- These are facts about sources, never Evidence: what an absence means for a project
  is Nextia's.

## Versioned decks and traceable membership (2026-09-25)
uibcdf/sabueso#58.
- **A deck revision is content-addressed**, like a card snapshot: its meta plus the
  pinned references of its cards (`Deck.snapshot_id()`). Decks are referenced as
  `sabueso:deck:<name>`, meaning the latest revision, or `sabueso:deck:<name>@sha256:…`,
  meaning that exact revision or failure. Deck names use letters, digits and `_ . -`.
- **Membership is part of the content.** `meta["membership"]` maps each card to its
  basis, and `meta["excluded"]` records candidates left out with their reason.
  `ambiguity_deck` and `ligand_deck` fill the membership. `Deck.add(card, basis=...)`
  and `Deck.exclude(candidate, reason, by=...)` let a curator do the same.
- **Derived decks record their operations** (`meta["operations"]`), and keep the
  membership of the cards they hold. `filter(predicate)` is marked not reproducible.

## Comparing two cards (2026-09-25)
uibcdf/sabueso#59; rule `card_knowledge_diff@1`.
- `card.compare_knowledge(other, residue_map=None)` says, area by area, what both
  protein cards state, what only one states, and what they state differently.
  - Fields: list items are compared by their identity (`curation.ITEM_IDENTITY`), and
    lists of plain values as values.
  - Relationships: the objects both cards point at, and those only one does.
  - Knowledge states: the ones that differ.
- **Positions need a mapping.** The same number in two entries is not the same residue.
  Positional features are `not_compared` without a residue mapping, and an item with
  an unmapped position is `not_comparable`. The mapping comes from an alignment
  (MolSysMT) and is recorded as the basis.
- **Free text is `not_compared`,** as for curated claims (#43).
- The comparison is a derived view, never a SourceAssertion.

## Predicted structures (2026-09-25)
uibcdf/sabueso#57.
- AlphaFold DB models are `has_predicted_structure` relationships
  (`alphafold:<entry id>`), a predicate of their own. `Card.structures()` and every view
  of experimental structures therefore cannot count them, by construction.
- A model carries what a reader needs to judge it: version, tool, mean pLDDT and its
  bands, the range covered, and whether the modelled sequence is the entry's current
  one. A model of an older sequence version is flagged, not dropped.
- `predicted_structures=True` is an opt-in enrichment. Its outcome is a knowledge
  state like any other: known, not stated (no model), not queried, or unavailable.
- Sabueso records models; it never downloads coordinates (MolSysMT).

## Curated ligand engagement (2026-09-25)
uibcdf/sabueso#61.
- `card.add_literature_engagement(molecule, residues, mechanism, publication, curator,
  covalent_residue=None, method=None, ...)` records the residues a paper says a compound
  acts on, and how. The result is an `engages` relationship, anchored by the molecule's
  InChIKey.
  - Residues are UniProt positions of the entry. A residue code given with a position
    must match the entry's sequence, which catches numbering slips.
  - A covalent engagement names its modified residue.
- Compared with the structural ligand sites of the same molecule (PDBe-KB): shared
  residues corroborate. Different residues are `not_comparable`, never a conflict,
  because a site can differ between states or constructs. Without an observed site the
  engagement is `new`.
- `Card.ligand_sites()` shows curated engagements next to observed contacts, each with
  its source. The curation store keeps them across rebuilds.

## Source registry (2026-09-25)
- `devguide/sources/registry.yaml` records every online resource Sabueso uses, has
  set aside, or has yet to review. Statuses: in_use, evaluating, queued, deferred,
  rejected, retired, out_of_scope. Each decision states its reason, and `deferred`
  states when to revisit.
- It is validated in CI: every `tools.db` module is an in_use entry, and a decision
  without its basis fails. The user page `data_sources.md` is generated from it.
- Proposals arrive through GitHub Discussions ("Data sources", with a form); the
  registry, not the thread, records decisions (`devguide/sources/README.md`).
- It was seeded from Diego's inventory of open resources for drug design (54 queued),
  plus the sources already in use and those set aside earlier (#21, #22, #29, #60).
- To be shared with MOLI once it has proven itself in Sabueso.
