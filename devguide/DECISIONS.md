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

## Organism relations from NCBI Taxonomy (2026-09-25)
uibcdf/sabueso#67; card schema 0.3.4.
- `taxonomy=True` (with `taxonomy_client`) adds `annotations.taxonomy`: the organism's
  taxon, its rank and every ancestor with name and rank, from NCBI Taxonomy (Datasets
  API, no key, public domain). UniProt's `annotations.taxon_id` stays the anchor.
- The identity audit uses NCBI ancestors when both cards have them, and its answer is
  final: related (`ncbi_lineage`) or not, whatever the names suggest. Otherwise it falls
  back to UniProt names, and every finding says which one decided (`organisms`).
- `Deck.group_by_rank(rank)` groups cards by the taxon of a rank (genus, family…).
- The resolver's search candidates are still compared by names, because they are not
  enriched; the audit of cards in a deck is exact once they are.

## One measurement, several sources (2026-09-25)
uibcdf/sabueso#66; rule `measurement_identity@1`;
`devguide/archive/measurement_identity.md`.
- Source records are kept. A measurement is a derived group over them, and views count
  measurements.
- Identity in layers: declared provenance (exact); then independent readings of one
  paper (publication, molecule through the glossary, type, relation, value at the
  coarser stated precision); ambiguity is never resolved silently.
- Pairs with the same paper, type and exact value but different molecules are reported
  for review (`molecule_differs`, `stereo_differs`, `molecule_unresolved`). They may be
  curation discrepancies between sources.
- Copies are pointers: a copy whose original is missing leads to it, and is not
  discarded.
- BindingDB is the second bioactivity source. Its monomers are anchored through
  UniChem, never from SMILES.
- PubChem BioAssay (#68): copies deposited by ChEMBL or BindingDB are grouped with
  their originals by provenance (assay and molecule), never vote for a group's class,
  and lead to ChEMBL assays a card lacks. A copy whose compound PubChem standardised
  differently is grouped only when the connectivity leaves one candidate, and is
  flagged.

## Migrating cards (2026-09-25)
uibcdf/sabueso#51; rule `card_migration@1`.
- Loading a card of another schema line is refused, and the error points to the
  explicit `sabueso.migrate_card(data)`. Nothing is migrated silently.
- A migration is honest, not complete.
  - Each step records what it converted and the **gaps**: `missing` when a fresh build
    with the same options would state it, `available` when it is a new enrichment one
    can ask for.
  - Additions a version made are listed in `migration.SCHEMA_CHANGES`, and a test
    requires an entry for every schema version.
- The original is never changed: its snapshot id is recorded, and with `store=` the
  original and the migrated card are two revisions of one card.
- `sabueso.refresh_card(card)` builds the card again with the options its
  enrichments record, re-applies curations, and records which gaps it completed and
  which the sources do not state.
- Steps between lines are functions in `migration.STEPS`. None exists: every card
  published so far is in the 0.3 line.

## Free-text claims typed by topic (2026-09-25)
uibcdf/sabueso#43.
- `card.add_literature_claim(topic, text, publication, curator, about=..., locator=...,
  quote=...)` records a claim that fits no structured field, in `literature.claims`,
  as a curated SourceAssertion. The curation store keeps it across rebuilds.
- **Never compared.** Whether two texts agree needs a reader, so the outcome is always
  `not_compared`. `card.claims(topic=None)` and `card.table("claims")` list claims by
  topic, with their provenance.
- **Topics are Sabueso's own provisional vocabulary** (`curation.CLAIM_TOPICS`): a new
  topic is an additive schema change. A vocabulary shared with Praxis or Nextia would
  be agreed in uibcdf/moli.
- **Promotion.** When claims of one topic recur, they should become a structured field
  or predicate, and cards move to it with `migrate_card` (#51). Biological context may
  be the first case (#60).
- **Claims drafted by an agent** stay SourceAssertions, with the agent recorded as
  curator. They are never Evidence (Nextia).

## Names from UniProt, and the names of a deck (2026-09-25)
- UniProt's other names are mapped with their kind:
  - `names.synonyms` holds `{name, kind}`, where `kind` is `alternative_name` or
    `submission_name`;
  - `names.abbreviations` holds `{name, of}`, `of` being the full name shortened;
  - `names.gene_names` holds `{name, kind, gene}`.
- A curated `{name}` that UniProt states corroborates it. `kind` describes the item,
  it does not state it (`curation.DESCRIPTOR_KEYS`).
- **A name is not an identity.** Most protein names name a function: "TIM" abbreviates
  "triosephosphate isomerase", which every organism's enzyme carries. A label such as
  "TcTIM" is the literature's; it enters as a curated synonym with its publication.
  Only accessions and gene loci identify an entry.
- `deck.unique_names(return_cards=False)` lists the distinct names of a deck, as
  `numpy.unique` does. It follows rule `unique_names@1`: spellings equal ignoring case,
  spaces, hyphens and underscores are one name, shown in the spelling most cards use.
  With `return_cards=True` it also returns, per name, the distinct cards that carry
  it. It is a view for reading and review. Nothing is grouped, stored or merged by
  name. Whether two cards with one name are paralogs or redundant entries is the
  identity audit's question.

## Structural inventory: grouping keys and residue maps (2026-09-26)
uibcdf/sabueso#70, found running the inventory live on two orthologs.
- **`group_by`** chooses the keys of a group among `structures.GROUP_KEYS`. The
  default, every state key, keeps the results of `structure_inventory@1` as they were
  cited. `ligands:interest` reads the ligand state coarsely: `no_ligands` and
  `no_ligand_of_interest` are both `none_of_interest`.
- **`residue_maps` and `reference`** place each card's substitutions in the reference
  card's numbering. The maps come from the caller, e.g. a MolSysMT alignment; Sabueso
  aligns nothing. `shared_substitutions` lists a reference position and residue found in
  several proteins, and the key `substitutions` groups mutants by them.
- **Equal numbers are never equivalent positions.** A card without a map keeps its own
  numbering, and its substitutions match no other card's.
- The rule's parameters record the keys, the reference and the mapped cards, so a
  grouping can be told from another.

## Gene loci across databases (2026-09-26)
uibcdf/sabueso#69.
- Two entries of one gene can state it in different databases. In the case found, a
  Swiss-Prot entry states a TriTrypDB locus, and a TrEMBL entry of a strain genome
  states an NCBI GeneID. The audit could not relate them and fell back to sequence.
- **Reported first.** A sequence-based finding says `gene_loci: not_comparable`, with
  each entry's databases, when both state loci in databases that do not overlap.
- **Decided by a source.** NCBI Gene lists the UniProt entries (Swiss-Prot and TrEMBL)
  of a gene's products. With `resolve(..., ncbi_gene=True)`, the resolver's audit asks
  NCBI Gene for the NCBI loci of a `not_comparable` pair, and only then. When the gene
  lists both entries, the gene is shared as a common locus would be (`gene_products`,
  with the gene and the retrieval date), and the request is recorded in the decision's
  sources. A failed or empty answer changes nothing.
- **Not done:**
  - matching locus tags as text (`TcCLB.508647.200` and `tcr:508647.200`), which is
    fragile and not a source statement;
  - KEGG, whose licence restricts use.
- **Resolution only.** `Deck.identity_audit()` works on cards, which do not store gene
  products. Extend it only when a deck needs it.

## Two integrated routes, and a guide that stays true (2026-09-26)
- **Two routes.** Sabueso's plan follows two routes, integrated in
  `devguide/ROADMAP.md`:
  - the foundational plan of the original design (2026-01 → 2026-09-23);
  - the pilot-driven route (since 2026-09-23).

  The pilots decided the order of the work, not its scope. The foundational objectives
  stay objectives, and the roadmap tracks each one's status: done, partial, pending or
  changed (the last citing the decision that changed it).
- **Nothing is dropped.** The original roadmap, source plan, next steps and
  long-term-direction conversation were archived verbatim, with notes pointing to where
  they are tracked. Sources of the original plan that were missing from the registry
  (eMolecules, ChemSpider, ClinicalTrials.gov, PiSITE, CPPsite, IUPAC resources) were
  added as `queued`.
- **Kinds of document.** The devguide has an index (`devguide/README.md`) that classes
  every document as normative, living, design or historical, and states how the guide
  is kept true.
- **AGENTS.md holds the repository's working rules**, which were recorded nowhere
  before:
  - language, knowledge principles, code conventions;
  - schema policy, tests and fixtures, local gates;
  - commits, releases, recording work, pilot confidentiality.

## Findings of the first live run of the knowledge baseline (2026-09-26)
A live run of the first pilot's knowledge baseline on 0.4.0 was audited against the
sources. Issues #72–#75 record what it found.
- **The oligomer the authors define (#72, `structure_state@2`).**
  - The state read the first assembly by id. For 2V5B, a monomerization structure,
    that is the software-predicted dimer, while the authors defined a monomer.
  - The oligomer now comes from author-defined assemblies, else from the software's.
  - `oligomer_basis` says which, and a software prediction the authors' assemblies do
    not include is flagged (`oligomer_disagreement`), never resolved.
- **Author numbering (#73, card schema 0.3.5).**
  - Positions stay in UniProt numbering. `author_numbering` adds, per chain, the author
    residue numbers from RCSB (`auth_to_entity_poly_seq_mapping` through the entity
    alignment), as compact segments.
  - Views give `author_substitutions` (`E104D` next to UniProt `E105D`).
  - It is a source statement; geometry stays with MolSysMT.
- **Partial source answers (#74, `knowledge_state@2`).**
  - RCSB failed that day, server-side, on the per-chain data of some entries. The client
    now fetches such an entry again without those fields and marks it `_partial`.
  - The card keeps the rest. The enrichment is `partial` (warning
    `SABUESO-W-ENRICH-003`), and the knowledge state is `partial`, naming the
    structures that failed or came back incomplete. "known" no longer hides a gap.
- **The recorded shape and fixture growth.** The shape builder pins its input
  structures, so a new fixture does not change a published shape. Chain-keyed qualifiers
  are recorded as `{chain}`.
- **The measurement review lists only unexplained pairs (#75).**
  - Two compounds of one paper can share a value. When each is already grouped with a
    record of the other source stating its own molecule, pairing them crosswise is no
    discrepancy, and the pair is left out.
  - The list has one entry per pair of molecules, with all its records.
  - On the live P52270 data, 7 entries became 3 unexplained ones: one `molecule_differs`
    worth reading, and two declared copies with other stereochemistry.

## A pinned item is read from its verified snapshot (2026-09-27)
uibcdf/sabueso#79; acceptance case 2 of uibcdf/moli#3.
- `KnowledgeStore.source_assertion(pin#SA_…)` and `relationship(pin#REL_…)` used to read
  the item row directly. `load(pin)` re-verified the whole snapshot, but these did not,
  so a row changed outside Sabueso came back under an unchanged pin.
- Both now rebuild and verify the snapshot, as `load` does, and take the item from that
  verified state. `relationships()` verifies every state it cites before returning, in
  the same transaction.
- Verification is never cached across reads. A cache would let a change made after the
  first read pass unnoticed. The cost is about 0.1 s per item read, for a card of about a
  thousand relationships.

## Early dependency-contract preflight (2026-09-27)
uibcdf/sabueso#76, adopting MOLI's distribution policy (uibcdf/moli#21).
- `pyproject.toml` stays the only authority for runtime names, constraints and
  `requires-python`.
- `devtools/dependency_routes.toml` lists where the runtime is installed: the conda
  recipe, the test, development and docs environments, and the exact public builds the
  staged-package test pins. It also lists, with a reason, the routes that do not install
  the runtime.
- `devtools/dependency_preflight.py` compares them, using the standard library only. It
  fails on:
  - a missing dependency;
  - a weaker or unconstrained floor, or a ceiling above the public one;
  - a missing or wider Python constraint;
  - an unlisted route.
  It never rewrites files. CI's quality job runs it first; it is also a local gate.
- Its first run found real drift. The staged-package test pinned SMonitor 0.16.0, below
  the new floor of 0.17.0, and would have failed to solve at the next release. The pin
  is now the public 0.17.0 build.
- The check for siblings installed from source does not apply: no required lane
  installs a sibling from a Git checkout. The inventory says so, and a lane added later
  must be declared there.
- **The staged-package gate pins its builds in two places**: the workflow's
  `create-args` and the verifier's `PUBLIC_DEPENDENCIES`. The verifier still pinned
  SMonitor 0.16.0. The preflight now reads both, and a test requires them to agree.

## Generated and packaged resources in the release artifact (2026-09-27)
uibcdf/sabueso#77, adopting MOLI's distribution policy (uibcdf/moli#26).
- **One claimed public route**, the `noarch` conda package. No wheel is published.
- **What it carries:**
  - package-critical resources: the packaged selection rules and enrichment profiles
    (`sabueso/resolver/*.json`). A missing one made 0.1.0 unable to build cards (#35);
  - version-bearing payloads: `info/index.json`, the `_version.py` versioningit writes
    at build, and the `dist-info` metadata.
- **Inspection before installation.** The staged-package test inspects the exact staged
  file (`verify_staged_install.py archive`): digest, embedded versions and resources.
  The installed gate then exercises the resources (`api_smoke` reads both JSON files).
- A test keeps `REQUIRED_RESOURCES` equal to the shipped package data. Negative fixtures
  cover a stale embedded version, stale metadata, a missing resource, another digest and
  another version.
- Checked against the published 0.4.0 artifact
  (`sabueso-0.4.0-py_0.tar.bz2`, sha256 `ba12e2d2…2e3e`): passes.

## Immutable Conda coordinates and the public poststate (2026-09-27)
uibcdf/sabueso#78, adopting MOLI's distribution policy (uibcdf/moli#25).
- **The route.** The staged route uploads to `staging`, and promotes by adding `main`
  to the same file through the provider's exact-file primitive, which checks the digest
  and source label. The action is never given `overwrite`, so it never uses `--force`.
- **Before a staged upload.** `release_route.py coordinate` refuses a coordinate the
  registry already holds under any label, identical bytes included. The direct route
  keeps its stricter check: no file of that version may exist.
- **After promotion.** `release_route.py poststate` verifies the exact coordinate,
  labels and SHA-256 with a repeatable read-only registry query and bounded retries. It
  records a receipt; an unobserved record fails the gate. The `conda search` check stays
  as the index view.
- **Negative checks.** An occupied coordinate is refused under `staging`, `main`, both
  or no label. Changed bytes at the public coordinate, a missing `main` label and an
  absent record are refused, and an unobserved poststate stays unresolved.
- **Checked on the live registry.** 0.5.0 is free; 0.4.0 is refused as occupied; the
  public poststate of 0.4.0 matches its tested digest.

## UniProt isoforms, deletions and secondary structure (2026-09-27)
uibcdf/sabueso#80, card schema 0.3.6.
- **Deletions are stated, not implied.** A UniProt "Missing" is
  `substitution: {missing: true}` in variants, mutagenesis and alternative sequences.
  An item with no substitution stays what it was: nothing stated. Curation compares a
  deletion as a substitution of its own. Cards of 0.3.5 or earlier that hold such an
  item report a `missing` gap on migration.
- **Isoform links come from the entry.** An alternative sequence names its isoforms
  through the entry's own list (`Sequence=VSP_…`). No isoform is matched by sequence or
  name, and isoform sequences are not built by applying segments: that would be derived
  knowledge, and fetching them is a later step.
- **Secondary structure is positional, with its structures.** It goes to
  `features_positional.secondary_structure`, one item per segment, with the PDB entries
  it was read from. `structure.secondary_structure` stays unwritten, since
  it would drop that basis.
- **A text comment's isoform restriction lives on its SourceAssertion**
  (`source_metadata.molecule`). The published shape of text comments stays a string.
  Structured comments (catalytic activity, subcellular location) keep it in the value,
  as before.
- **Not curatable yet:** alternative sequences and secondary structure, until a
  publication needs to be compared with them.
- **Per-chain secondary structure from RCSB** (added the same day) is a `has_structure`
  qualifier, with the assigning program. A strand shared by two sheets is one segment,
  and sheets are not kept. A chain without any assignment is left out: not stated,
  never coil. `UNASSIGNED_SEC_STRUCT` counts as an assignment, so a chain with only
  unassigned residues is listed, with no helix or strand.

## Knowledge packets, prototype (2026-09-27)
uibcdf/sabueso#71, before the MOLI contract (uibcdf/moli#22) is agreed; the maintainers
chose to prototype first and align after.
- **Two steps.** `knowledge_packet` resolves the cards the query needs. `compose_packet`
  is a pure function of the query and card states: no network, no LLM, no ranking, no
  summary. The same query and states give the same packet.
- **The query decides what is asked.** Aspects map to resolve options through a fixed,
  versioned mapping (`packet_aspects@1`). Keyword arguments are only a resolver and
  source clients. An unknown aspect or constraint is refused.
- **Two ids.** `snapshot_id` hashes the exact packet, retrieval times included, and is
  what `sabueso:packet:<name>@sha256:…` pins. `content_id` leaves out `retrieved_at` and
  `sabueso_version`, and uses each card's content-equivalence id instead of its pin. So
  two assemblies of unchanged knowledge are recognisably the same, which answers the
  finding recorded on #71 (identical knowledge, different snapshot ids).
- **Facts are the views' output, whole,** with their named rules. Quantities are
  `{value, unit}` nodes, read in their own unit. Summaries with references, if size
  demands them, are a later version.
- **Unknowns come from `knowledge_state@2`,** restricted to the areas of the aspects
  asked. Conflicts come from the cards' records, restricted the same way.
- **Stored like decks.** A packet is saved only when every card state it cites is in
  the store, and a read verifies the packet and those states. The new tables do not
  change the store format.
- **Proteins only** in `knowledge_query@1`: a subject and an optional comparator. Decks
  as subjects, and other entity types, wait for real use.

## Biological context of a target, step 1 (2026-09-27)
uibcdf/sabueso#60. Four curated fields, before any connector (VEuPathDB is step 2):
`annotations.stage_expression`, `essentiality`, `accessibility` and `metabolic_role`.
- **Stated text, never categories.** Items hold the words of the publication. A
  phenotype is not classified. "Essential" is kept only as the authors' `call`.
- **Strict items.** Each field has required and optional keys (`CONTEXT_KEYS` in
  `sabueso/core/curation.py`). Anything else is refused, so a misspelt key cannot
  silently become a new kind of statement.
- **Comparison by condition.** Two statements under the same condition are compared:
  method, stage, host and condition for essentiality; compartment, pathway or stage,
  with stage and host, for the others. A different content there `differs`; another
  stage is another statement.
- **The organism is the card's.** No field names an organism. A result on an ortholog
  belongs to the ortholog's card, since identity is never merged.
- **Absence.** An uncurated field is `not_queried` from `Literature` in the knowledge
  state, with the basis `route: curation`, never `not_stated`.
- **Packets** have a `biological_context` aspect: these fields, and UniProt's
  subcellular location, tissue specificity and pathway.
- Free-text claims on these topics stay possible (#43).

## PHI-base, and caching whole releases (2026-09-27)
uibcdf/sabueso#83, the first source of the coverage plan's pathogen gap.
- **Why PHI-base.** Its curated phenotypes of pathogen mutants are keyed by UniProt
  accession, cover eukaryotic pathogens, and are CC BY 4.0 with versioned releases.
- **Releases, not the web API.** PHI-base 5's web API is undocumented. Its releases on
  Zenodo are versioned and checksummed, so the client uses them.
- **Caching only where told.** The first release cache keeps the policy "Sabueso writes
  only where it is told to". By default a release is indexed in memory for the
  process. A cache directory (`cache_dir=`, `$SABUESO_CACHE_DIR`) keeps it on disk,
  each curation session once (the first attempt, one file per gene, took 2.1 GB).
- **One item per phenotype annotation, with the whole genotype.** A double mutant's
  phenotype carries both alleles and is never read as the single gene's. Nothing is
  classified: "Lethal" or "reduced virulence" is PHI-base's statement about a mutant in
  an experiment.
- **"evidence" stays Nextia's word.** PHI-base's `evidence_code` (how the phenotype was
  observed) is kept as `method`.
- **In packets,** the `biological_context` aspect asks PHI-base (`packet_aspects@1`, not
  yet published).

## Clinical layer, step 1 (2026-09-28)
uibcdf/sabueso#81.
- **Trials only through a stated link.** ClinicalTrials.gov names interventions as text.
  Sabueso asks it only for the NCT ids ChEMBL's drug indications cite, and records that
  basis on every `tested_in`. No trial is matched to a molecule by name.
- **Indications keep ChEMBL's terms.** One `investigated_for` per indication, to the
  term's CURIE (`efo:`, `mondo:`, `doid:`…). Two terms with one MeSH heading are not
  merged. The phase is ChEMBL's, per indication.
- **A cited trial the registry lacks** keeps ChEMBL's statement, with `registry:
  not_found`. A cited trial not fetched is listed in `Card.clinical()["not_fetched"]`,
  never treated as absent.
- **Two sources, two assertions.** The ChEMBL indication record supports both
  relationships. The ClinicalTrials.gov study record, with subject `nct:<id>`,
  supports `tested_in`.
- **Migration changes may name the entity types they apply to** (`entity_types`), so a
  protein is not told it lacks indications, nor a molecule pathogen phenotypes.

## DISEASES, gene–disease associations (2026-09-28)
uibcdf/sabueso#82, the first of the human disease-association sources.
- **Channels stay apart.** One `associated_with` per disease, channel and Ensembl
  protein. A curated association and a text-mined co-mention of one disease are two
  statements.
- **Text mining only when asked.** It links names: the human TPI1 is co-mentioned with
  giardiasis because the parasite's enzyme has the same name. The default channels are
  curated knowledge and experiments.
- **Joined through a stated link.** Rows name Ensembl proteins, and a row reaches a card
  only through an Ensembl protein the UniProt entry cross-references, never by gene
  name. The isoform UniProt maps it to is kept.
- **Scores as stated.** Confidence, source score and z-score are DISEASES's, never
  recomputed or ranked.
- **Not applicable is not "not stated".** For a non-human protein the enrichment is
  `not_applicable`, and the knowledge state says `not_queried` with the reason.
- **Versioned by date.** The files are updated in place, so the version is each file's
  publication date, and the cache is keyed by it.
- **Open Targets (same day).** Associations are per Ensembl gene. A row reaches a card
  only when both sources state the gene–protein link: UniProt cross-references the
  gene, and Open Targets lists the entry among its products. Scores (overall and per
  data type) and rank are recorded as stated, with the data version, never recomputed.
  At most 100 associations per gene by default, in Open Targets' order, with the cut
  reported. `associated_with` is identified by source, channel, Ensembl protein and
  gene, so DISEASES's and Open Targets' statements never merge, and a disease under
  two ontologies stays two references.
- **Orphanet (same day).** One `associated_with` per disorder–gene association, to
  `orphanet:ORPHA:<code>`, with Orphanet's association type, status and validating
  publications. Orphanet states each gene's Swiss-Prot accession, so the link is its
  own. The 22 MB file is indexed in memory once per process, and nothing is written:
  its version is only known after downloading, so a disk cache could not be keyed
  before fetching.

## Reactome, and naming Sabueso over HTTP (2026-09-28)
uibcdf/sabueso#83.
- **Pathways as relationships.** `participates_in`, one per Reactome event mapping the
  accession (lowest-level pathways and reactions), with Reactome's ancestors and its
  orthology-inference flag. UniProt's free-text pathway stays a separate statement.
- **One user agent.** DISEASES's downloads and Reactome's Content Service refuse
  Python's default user agent. New clients name Sabueso and its version through one
  helper (`tools/db/_http.py`); older clients move to it when a source starts refusing
  them.

## ClinVar, and placing variants in UniProt numbering (2026-09-29)
uibcdf/sabueso#83; the numbering rule was agreed with the maintainers before building.
- **Found by a stated gene.** Records come from the NCBI Gene id the UniProt entry
  cross-references, never from a gene symbol.
- **Classifications as stated.** The germline classification, its review status and
  the conditions are ClinVar's words. "Conflicting classifications of pathogenicity"
  is ClinVar's own statement, and Sabueso never resolves it.
- **Placing is strict.** ClinVar's `protein_change` lists the change in every
  isoform's numbering, so it never places a variant. A variant gets a UniProt
  position only when two things hold: the record's transcript is one UniProt states
  for its canonical isoform (RefSeq cross-reference, version included), and the
  residue ClinVar names is the UniProt residue at that position. Otherwise the item
  keeps ClinVar's numbering and says why it is not placed. Nothing is placed by
  similarity.
- **Not for diagnosis.** The docs repeat ClinVar's own warning.
- **gnomAD (same day)** follows the same placement rule, through an Ensembl transcript
  UniProt states for its canonical isoform. gnomAD's transcript ids carry no version,
  so the residue check guards against a changed sequence. Only variants with a protein
  change are kept, and the others are counted. Frequencies (`ac`, `an`, `af`) are kept
  as stated, per exomes and genomes. The placement code is shared (`mappings/_hgvs.py`).

## Placing a change stated on another isoform (2026-09-29)
Agreed with the maintainers as a second pass for the variants of #83.
- **Rule `uniprot_isoform_map@1`.** Each step is a UniProt statement:
  - which isoform a transcript encodes (Ensembl and RefSeq cross-references);
  - how that isoform differs from the canonical sequence (its `VSP_` edits).

  Applying the edits gives a map from isoform positions to canonical ones. The
  residue must still match. The item records `placed_via` (rule, isoform, isoform
  position).
- **An isoform's own segment has no canonical position** (`isoform_specific_position`).
  For TPI1 this accounts for 184 of the 189 gnomAD variants the first pass left out:
  they lie in the 37 residues isoform P60174-3 adds at its N-terminus. Placing them by
  alignment would have been wrong.
- **Alignment is not used.** It is kept as a possible last resort, with its own rule,
  for isoforms UniProt does not describe by edits (#85).
- More precise reasons for what is not placed: `unparsed_protein_change` and
  `stop_codon`, besides `residue_mismatch`.

## Declared enrichers (2026-09-29)
uibcdf/sabueso#86, wave 3 of #83.
- **One contract, one runner.** A source's contribution to a card is declared once.
  The runner applies organism coverage, `not_found` and `error` per request, and a
  fixed order. An enricher's `map` returns its record's outcome, so each source's
  records stay exactly as before.
- **Tables are derived, not kept by hand:** the knowledge-state rows
  (`knowledge_areas`) and the migration map of records to options
  (`options_by_source`). A test checks that each enricher has its parameters,
  digesters and registry entry.
- **Behaviour-preserving steps.** Each step is checked by comparing whole cards
  (snapshot ids and records) before and after, not only by the test suite.
- **Bespoke, for stated reasons:** RCSB structures, the ChEMBL/BindingDB/PubChem
  BioAssay group, and NCBI Gene in the resolution.
- **Step 2 (same day).** STRING, PDBe-KB (ligand sites, interfaces), AlphaFold DB,
  NCBI Taxonomy and InterPro became enrichers. They run in declared stages among the
  bespoke enrichments, so the order of records (part of a card's content) does not
  change. Only the RCSB, ChEMBL, BindingDB and PubChem BioAssay blocks remain in
  `resolve_protein_card`.
- **Step 3 (same day): shared services.**
  - Every client reaches the network through `tools/db/_http.py`: Sabueso's user
    agent, and at most two retries with backoff for 429, 502, 503, 504 and refused
    connections. Timeouts are not retried, since a retry would multiply a slow
    source's cost. Other errors reach the client unchanged, so "not found" stays an
    answer.
  - Release sources share `_release`: memory by default, disk only when told, atomic
    writes, checksums.
  - Keys belong to the user and to a service (`SABUESO_<SERVICE>_KEY`). A card does
    not record whether a key was used: an optional key changes the rate, not the
    answer. A missing required key is `not_queried` (`MissingKeyError`). NCBI is the
    first user, with its optional key.
- **Step 4 (same day): packet options are derived.** An aspect asks every declared
  enricher that answers one of its knowledge areas. The rule: a packet never reports
  as "not queried" what its own aspects could have asked. `packet_aspects@1` is
  unpublished (packets are not in 0.5.0), so its two gaps were corrected in place:
  `structures` now asks AlphaFold DB, and `sequence_features` asks InterPro. Functional
  association (STRING) is not an aspect yet.
- **Step 5 (same day): parallel fetching is deferred (#87).** Measured online: the
  declared enrichers are 18.8 s of a 39.5 s card for HsTIM, and 6.3 s of 34.9 s for
  TcTIM. Concurrency would save at most about a quarter of a card's time, at the cost
  of thread safety and gentler use of rate-limited sources. #87 states when to
  re-evaluate. ClinVar, the slowest, now also takes the optional NCBI key.


## A cut never passes for the whole answer (2026-09-29)
- **The gap.** STRING states no total. With its default limit of 50, a card kept
  HsTIM's 50 most confident partners (of 78 at score ≥ 700), and nothing said so.
- **The rule.** Every source whose answer Sabueso limits must report the cut:
  - with the source's total where it states one (ChEMBL, Open Targets, ClinVar,
    gnomAD);
  - otherwise by asking for one record more than the limit. STRING's cut is then
    recorded as `truncated`, and reported as "50 of more than 50".
- **Where it shows.** The public envelope (`get_partners`) carries `truncated` too.
- **Fixtures.** Some are declared cuts of a larger answer (`temp_data/NOTICE.md`), so
  building cards from them reports truncation. That is the fixture stating what it is,
  not a failure.
- **Defaults: everything, up to a ceiling** (same day, #88). Each source is asked for
  everything it states about an entry, up to 5000 items: ChEMBL, STRING, Open Targets,
  ClinVar, gnomAD, ClinicalTrials.gov. The previous defaults were 50 to 1000, and they
  hid knowledge by default. The ceilings are listed on the data-sources page, read from
  the code. UniProt's name search stays at 500 candidates on purpose: more is ambiguity,
  and the resolution records it. Card size and time are watched in #88.
- **Where sources are documented.** The data-sources page, generated from the registry,
  is the one list of sources in use, their access and licence, their ceilings, and the
  sources set aside or blocked, each with its reason.

## Gaps in the knowledge state, found by the 0.6.0 release (2026-09-29)
- **A cut is partial** (`knowledge_state@3`, #88). A source whose answer was cut at a
  limit read as `known`, although its record and a warning said `truncated`. The row
  is now `partial`, and `basis.truncated_for` names the requests that were cut, as
  `unavailable_for` and `incomplete_for` already do for failures. It is a new rule
  version: packets and views built from now on cite `@3`.
- **"Not stated" carries its release** (#89). `RecordNotFoundError` takes the release
  the client consulted (`version=`), and the enricher runner records it in the
  `not_found` record. The row then reads "not stated by Reactome at release 97". PHI-base,
  Reactome, Orphadata and Open Targets pass it. A source that states no release still
  records `not_found` without one.

## SKEMPI 2.0: interface mutations, joined and placed only on stated grounds (2026-09-29)
uibcdf/sabueso#83, wave 2, first of the interface sources. Card schema 0.3.7.
- **Join.** A SKEMPI row names a PDB entry and the chains of each side (`1BRS_A_D`).
  It joins a protein card only when UniProt states that one of those chains is the
  protein (the PDB cross-reference's `Chains`). The protein names SKEMPI writes are
  kept as text and never used to join.
- **Placement** (`rcsb_author_numbering@1`). Mutations are in the entry's author
  numbering. One is placed in UniProt numbering only through the author numbering RCSB
  states for that chain (#73), of a structure the card holds, and only when its residue
  matches. Mutations on the partner stay in author numbering (`partner_chain`).
  Barnase is the test: its author numbering is the mature protein's, 47 positions from
  UniProt's.
- **As stated.** Affinities, kinetics, thermodynamics and temperature are quantities in
  the units SKEMPI states. A bound keeps its relation, "n.b." is `no_binding`, and an
  assumed temperature is flagged.
- **ΔΔG is derived, never stored** (`binding_ddg@1`, in `Card.interface_mutations()`).
  It is computed from the stored affinities and temperature, and is a bound when an
  affinity is one.
- **Version.** The file states only the database version, 2.0, while the site reports
  later corrections. Each enrichment records the file's SHA-256.
- **Packets.** The `oligomer` aspect now also covers interface mutations. That changes
  what a published mapping asks, so it is `packet_aspects@2`. A test pins each
  version's options: aspect options are derived from the enrichers, and a new enricher
  must never change a published version silently.

## iPPI-DB is blocked (2026-09-29)
- Its compound pages state targets (UniProt), activities and InChIKeys, but only as
  HTML. The CSV export holds SMILES only, and the REST API covers structures, cavities
  and hotspots.
- No data licence was found on the site. The registry's earlier "CC BY-SA 3.0" could
  not be confirmed, and may have been the article's licence.
- Reading HTML pages is fragile and, without terms, not redistributable. It waits on the
  maintainers (#84).

## The disease as an entity, anchored at MONDO (2026-09-29)
uibcdf/sabueso#90, step 1. Card schema 0.3.7.
- **Why MONDO.** Six sources name diseases with different ids (DOID, EFO, MONDO,
  ORPHA, MIM, MeSH). MONDO integrates those terminologies and states, term by term,
  which external ids are the same disease (`MONDO:equivalentTo`). In release v2026-09-01
  that is 118,297 equivalences over 36,015 terms, each external id to exactly one term.
- **Identity** (`mondo_equivalence@1`). An external id resolves only through a stated
  equivalence. The resolution records the statement and the release. Other xrefs are
  related terms, kept apart (`identifiers.related_ids`) and never read as identity:
  for example, EFO:0001360 is cited by MONDO's type 2 diabetes term only as the source
  of other xrefs, so it does not resolve.
- **Obsolete terms are not followed.** The replacement MONDO states is named as a
  candidate. A replacement can be a merge or a split, and whoever cites the old term
  decides.
- **Routing.** Disease namespaces go to disease cards. `omim:` and `mesh:` also number
  genes and chemicals: those find no equivalence and are reported as not found, never
  as a disease.
- **Next steps (#90):** relate the diseases on protein and molecule cards through these
  equivalences, then disease → targets.
- **Step 2 (same day): a protein's diseases, grouped.** `disease_identity` asks MONDO
  about every disease id the other sources put on a protein card: associations,
  UniProt's MIM numbers, and ClinVar's condition ids. Each stated equivalence becomes a
  `same_as` relationship to the MONDO term, backed by a MONDO SourceAssertion.
  `Card.diseases()` groups the statements through those relationships, or when they
  name the same id (`disease_grouping@1`). Nothing else groups, not even an identical
  name. For HsTIM, triosephosphate isomerase deficiency is one disease stated by five
  sources. MedGen concept ids and some EFO terms stay apart, with their reason. In the
  glossary (`entities()`), those ids are diseases, anchored at their MONDO term.
- **Step 3 (same day): ClinVar conditions, MedGen, placeholders.** A first run left 272
  ClinVar statements ungrouped for HsTIM. They were 18 MedGen concepts, and most
  statements were not an identity problem:
  - **One condition is one statement.** ClinVar states that a condition's ids (MedGen,
    OMIM, Orphanet, MONDO…) name it together. Treating each id as a statement had
    left TPI deficiency's MedGen id apart from its own MONDO id. A condition now joins
    a disease when any of its ids does, and ids that reach two terms are
    `conflicting_identity`, both listed, neither chosen.
  - **Placeholders are not diseases.** ClinVar's "not provided" (MedGen C3661900) and
    "not specified" (CN169374) are `condition_not_provided`, 153 of the 272.
  - **MedGen as a source, not a scheme rule.** MONDO states equivalences to MedGen
    records by UID, not by concept id. Reading a MedGen concept id as a UMLS CUI would
    rest on a naming convention that no record states. Instead, MedGen states, record
    by record, the UID of each concept id (`medgen_concept@1`), and MONDO's equivalence
    completes the chain. On HsTIM, both alternatives grouped the same 9 concepts,
    without a single disagreement. The stated route was kept.
  - **Result, live HsTIM:** of ClinVar's conditions, only 6 phenotypic traits have no
    stated equivalence. Three conditions are reported as conflicts: ClinVar gives a
    broader Orphanet id next to a subtype's MONDO and OMIM ids. Telling that granularity
    difference apart with MONDO's hierarchy is a possible next rule.
- **Step 4 (same day): from a disease to its targets and its drugs.**
  - `disease_targets` (`disease_targets@1`) takes Open Targets' associated targets
    (asked by the MONDO id, then its EFO equivalents) and Orphanet's genes of the
    disorder (by its Orphanet equivalents). Each member is a Swiss-Prot product the
    source states for the gene, and its basis lists every statement that brought it.
  - `disease_drugs` (`disease_drugs@1`) takes the molecules whose ChEMBL indications
    name the disease by its MONDO id or its EFO and MeSH equivalents, ordered by
    ChEMBL's phase.
  - **A lower default for decks (50).** Enrichments ask for everything up to 5000
    (#88), but a deck member is a whole card, at least one request: five protein cards
    took about 50 s live. The cut is recorded (`excluded`, reason `limit`) and
    reported, and `limit` asks for more.

## What may be done with the knowledge: a first milestone (2026-09-29)
uibcdf/sabueso#29.
- **Terms are the sources' statements, recorded per source** in the registry (`terms`),
  with the URL of the statement and a review date. They are not SourceAssertions: their
  subject is the source, not an entity. Granularity is the source, except where the
  source states that terms vary per record (PubChem BioAssay's depositors, a curated
  statement's publication). Those are `unknown` until they are recorded per record.
- **Three verdicts:** `allowed` with obligations, `restricted` with the reason, and
  `unknown` with the reason. Unknown is never "no restriction".
- **An item remains when one allowed source states it.** Each statement stands on its
  own, so a value two sources state survives the loss of one of them.
- **Derived knowledge** is recomputed from what remains, and carries the obligations
  of the statements it is computed from; the strictest governs (`terms_propagation@1`).
- **The disclaimer lives in the returned report.** It is a report for a person's
  decision, not legal advice.
- **Answering the acceptance question.** For the *T. cruzi* enzyme with ChEMBL,
  BindingDB and PubChem BioAssay, 272 of 527 measured molecules may be used in a
  commercial product (attribution, share-alike); 255 are known only from PubChem
  BioAssay and are `unknown`.
- **Terms profiles** (same day, #94). `terms="commercial"` or `"non_commercial"` builds
  knowledge only from sources whose stated terms are `allowed` for the profile's use
  (`commercial_product`, `academic_publication`).
  - Named by use, not by institution.
  - A project that may end in commercial exploitation is `commercial` from its first
    day: knowledge that informed a decision cannot be un-used later.
  - Unknown terms are excluded too, with their reason. In a commercial project a wrong
    green light is worse than an exclusion.
  - The card keeps the profile (`quality.terms_profile`, `terms_profile@1`), so a
    packet or a Nextia decision knows under which terms its knowledge was gathered.
  - Curations the user applies are the user's, and are not filtered.
  - Today almost every source in use allows commercial use. The profiles differ through
    sources with unknown terms, and `non_commercial` would let us reconsider sources set
    aside for a non-commercial licence, such as DrugBank's clinical content.
- **Terms per record: PubChem BioAssay by depositor** (same day, #94).
  - A PubChem BioAssay result keeps its depositor's terms. The registry names the
    depositors whose terms are known (ChEMBL, BindingDB: their assays in PubChem are
    copies of their records).
  - Each result is judged by its depositor's terms, and the report says so
    (`PubChem BioAssay (deposited by ChEMBL)`, with its basis). Other depositors stay
    `unknown`.
  - Profiles now ask PubChem BioAssay and keep each result whose depositor's terms
    allow the use. The others are counted (`excluded_records`).
  - The depositor comes from each relationship's `assay.depositor`, so cards stored by
    0.6.0 are judged the same way.
  - For TcTIM with ChEMBL, BindingDB and PubChem BioAssay, all 527 measured molecules
    now remain for a commercial product, with attribution and share-alike. The first
    milestone reported 255 of them as `unknown`.
- **Scientific operations: navigate, explain, as of** (same day, #91).
  - `expand(card, predicate)` follows relationships into a deck of the related
    entities' cards (`relationship_expansion@1`). A member is one entity: refs that
    resolve to the same card are merged, and the basis keeps every statement and its
    SourceAssertions. Merging relies on the stated identity that resolution already
    uses, never on similarity.
  - What cannot be followed is excluded with its reason (`no_card_type`,
    `not_resolved`, `limit`). A related entity without a card type is not dropped.
  - Each member is a whole card, so expansion is capped (50 by default). The entities
    with the most statements are followed first, and the cut is reported as a
    truncation.
  - One name, `expand`: the `neighbors` of the roadmap would only have been a second
    spelling. The reserved `Card.expand(kind)` now takes a predicate.
  - `explain` answers from what is recorded: a deck member's basis and the deck's
    operations, and a card's SourceAssertions. It does not re-run anything.
  - `as_of` reads the store's revisions only. Sabueso does not reconstruct a source's
    past: knowledge on a date is what was built and saved by then.
- **Molecules given as a structure** (same day, #93).
  - A `smiles:` or `inchi:` query is matched by PubChem, and the card is the compound
    PubChem names, anchored at the InChIKey PubChem states
    (`pubchem_structure_lookup`). Sabueso never computes a key from a structure: that
    would make identity depend on a toolkit and its version.
  - A structure PubChem does not hold (CID 0) is `not_found`; one it cannot read (HTTP
    400) is `unsupported`, with PubChem's message; several CIDs are `ambiguous`.
  - Stereochemistry, tautomers and salts are as PubChem handles them. A SMILES without
    stereocentres names the compound with undefined stereochemistry, which is a
    different card: vincristine's flat SMILES resolves to CID 3717450, not 5978.
  - The lookup is the resolution's basis (`decision["structure"]`, with the structure
    as given), not a SourceAssertion: the card is about the compound, and the query is
    the user's.
  - A computed key, as a flagged derived identity under a named rule, waits for a
    stated need.
- **A disease named at two granularities** (same day, #90). On HsTIM, three ClinVar
  conditions reached two MONDO terms and were reported as `conflicting_identity`.
  - MONDO's hierarchy tells them apart. `disease_identity` asks MONDO, for the terms one
    statement reaches, whether one is under the other. It records each chain as
    `subclass_of`: each `is_a` step is a MONDO SourceAssertion, and a chain of several
    steps is derived (`mondo_hierarchy@1`). Only terms met together in one statement
    are related. Relating every term a card reaches recorded 1,107 relationships on
    HsTIM, most of them to broad terms such as "hereditary disease"; asking by
    statement records 3.
  - The statement joins the **broader** term, with the narrower one in `narrower`.
    Joining the most specific term looked natural, and it was right for two of the
    three conditions (Klippel-Feil syndrome 3, familial tumoral calcinosis 1). The
    third was ClinVar's "Obesity", named with the Orphanet id of obesity due to MC4R
    deficiency. What holds for a subtype holds for the disease it belongs to; the
    reverse is a claim no source made.
  - Terms of which neither is under the other (two subtypes) stay a conflict.
  - `disease_grouping@1` has not been released, so it keeps its version, with
    `granularity: mondo_hierarchy@1` among its parameters.
- **How each statement entered** (same day, #92, step 1). Every SourceAssertion
  records `acquisition`, a new optional key in card schema 0.3.7.
  - Methods: `database`, `curation`, `rule_extraction` and `model_extraction`, plus
    `validated_by` on an extraction. An extraction must name its tool and version: a
    statement whose extractor cannot be named cannot be reproduced or weighed.
  - How a database obtained its own record is the database's statement, recorded as
    `origin` only when the source states it. Today that is DISEASES's text-mining
    channel (`text_mining`). STRING's links combine channels, text mining among them,
    in one score, so no single link can be marked.
  - Acquisition is recorded, not inferred. SourceAssertions of older cards read as
    `not_recorded` until a refresh; a migration within a line does not rewrite them.
  - It says how a statement entered, never how true it is. Weighing a statement for a
    project remains Evidence, in Nextia.
  - The key is not in MOLI's conceptual SourceAssertion schema. It was proposed
    there (uibcdf/moli#32), and Sabueso's use is additive.
- **Europe PMC: stated accessions only** (same day, #92, step 2).
  - Europe PMC mines abstracts and open-access full texts for accession numbers. A
    search `ACCESSION_ID:<acc> AND ACCESSION_TYPE:uniprot` finds the articles whose text
    states the accession: 354 for HsTIM. The id is written by the authors, so a
    mention is identity by statement. It becomes `mentioned_in` (protein →
    publication). It says the paper names the entry, never what it states about it.
  - Its gene and protein annotations are not used. They ground a name without the
    organism: in a paper on the human TPI deficiency, "triosephosphate isomerase" is
    tagged with a yeast entry (Q9C401). That is identity by name.
  - Acquisition: a source that serves text-mined records is `database`, with
    `origin: text_mining`, as DISEASES's text-mining channel is. `rule_extraction` and
    `model_extraction` are kept for extractions whose tool and version are known,
    because Sabueso or its user ran them. Europe PMC states no version of its tagger,
    only of its service (6.9), which is recorded as the release.
  - Terms: EMBL-EBI places no restrictions of its own and expects attribution. Each
    article keeps its licence, so only ids and bibliographic data are kept, never text.
  - Not asked by a packet aspect yet. A well-studied protein has thousands of
    mentions, and packet size is watched (#88).

## Knowledge packets: the name, and references instead of copies (2026-09-30)
uibcdf/sabueso#88.
- **The name stays `KnowledgePacket`.** Alternatives were weighed: *brief* and
  *dossier* collide with MOLI's scientific communication (ProjectBriefings,
  ProgressBriefs, dossiers); *slice* and *bundle* already name integration slices and
  deployment bundles; *answer* pairs well with `KnowledgeQuery` but reads as a
  conclusion; *excerpt* was the closest fit. A packet is not a deck: a deck holds whole
  cards, a packet the facts a query asks, with unknowns, conflicts and provenance.
- **`knowledge_packet@2`: each statement once.** In a TcTIM/HsTIM packet with every
  aspect, the joint structure inventory copied each protein's structures field for
  field (31 of 31), and grouped disease statements copied the associations and ClinVar
  conditions of the same aspect. Both now name what they refer to. Associations and
  pathways carry their `relationship_id`, and ClinVar statements their condition index.
- **Measured.** The same cards give 2.04 MB instead of 2.25 MB (−9 %): structures
  halve (288 → 151 KB), diseases −11 % (most groups hold a single Open Targets
  statement). The rest is content, not repetition. Reducing it is a decision about
  what a packet is for (a declared level of detail, or a compact encoding), taken
  apart.
- **Formats are not compared.** `@1` packets are still read. A revision of another
  format has `knowledge_changed: None`, and `same_knowledge` answers None: the ids of
  two formats differ even when the knowledge does not.

## Ceilings for BindingDB and PubChem BioAssay, and PubChem by target (2026-09-30)
uibcdf/sabueso#98, #88.
- **The ceiling held everywhere but here.** Every source stops at 5000 records and
  reports the cut, except BindingDB and PubChem BioAssay, which fetched everything. For
  EGFR that meant 32,346 BindingDB records (16,463 UniChem lookups, one at a time) and
  6569 PubChem assays (one request each, some primary screens of tens of MB): a card
  that would not finish. Both now keep 5000 by default, and record and report a cut.
- **Which records are kept is a named rule**, recorded in the enrichment (card schema
  0.3.8, since 0.3.7 is published).
  - `bindingdb_record_order@1`: by monomer id, affinity type and value. It is only
    deterministic; every BindingDB record has a value.
  - `pubchem_row_order@1`: confirmatory rows with a value, then other rows with a value,
    then rows without one; each by AID and SID. A cut keeps measurements before
    screening outcomes.
- **PubChem by target.** `assay/target/accession/<acc>/concise` returns every result of
  a protein in one request, with the same columns as an assay's table. For TcTIM it
  gives exactly the 493 rows of the 13 assays fetched one by one. For EGFR it takes
  about 21 s instead of more than 27 minutes. Rows of another protein in a multi-target
  assay are left out, as before.
- **BindingDB's monomer → CID file is not an identity route.** It is fast (97.7 % of
  EGFR's monomers, 200 InChIKeys per PubChem request), but a PubChem CID is PubChem's
  standardized compound. On a sample, 5 of 52 differed from the InChIKey UniChem states
  for BindingDB's structure: a stereo layer, a tautomer, or another compound. Identity
  stays with UniChem. BindingDB's monthly TSV, which states its own InChIKey per row,
  is the candidate for heavy use (#98).
- **Polite concurrency for one-record-per-request services** (same day, #98, #87).
  UniChem has no batch query and states no rate limit. `_http.gather` asks it with four
  threads at most, and `Pace` starts no more than five requests per second, the pace
  PubChem states for itself. The pace belongs to the online client (`workers`,
  `per_second`), so saved answers in tests run unpaced. For EGFR, 1769 BindingDB
  monomers took 635 s instead of about 40 minutes: UniChem's latency (about 1.4 s),
  not the pace, is the limit. A cache of lookups would remove repeated ones, but it is
  a raw-payload cache, an open question of `CACHE_POLICY.md`, and is proposed apart.
- **RCSB entries in batches** (same day, #98). The Data API answers `entries(entry_ids:
  [...])` with the same fields as one entry, and leaves out an entry it does not hold.
  Sabueso asks 25 per request. An entry an error touched is asked alone, so the
  partial-entry fallback of #74 still applies to it; a batch that fails as a whole is
  asked entry by entry. A client without `fetch_structures` (saved entries, a user's
  client) is asked one entry at a time. Live, 40 EGFR entries gave a card with the same
  content id as one-at-a-time, in 5.6 s instead of 13.1 s.

## What was downloaded: a retrieval archive, mirrors and access modes (2026-09-30)
uibcdf/sabueso#100, uibcdf/moli#33. Direction adopted; not yet built.
- **Why the policy changes.** Sabueso stored no raw payloads. MOLI's reproducibility
  policy asks every external retrieval to keep what it returned when the licence
  allows, and to say so when not. Repeated builds re-fetch the same answers (#98), and a
  project should be able to work offline and on one release.
- **Three layers, not one cache.** A retrieval archive (what was downloaded), local
  source mirrors (whole releases with an update policy), and the knowledge store (what
  was known). Reusing a fresh archived answer replaces a separate lookup cache.
- **Three users.** An independent user sees no change by default: online, nothing
  written. UIBCDF's research use gets mirrors on a lab machine and archives per project.
  MOLI gets shared mirrors and per-project archives feeding its InputManifest and
  KnowledgeSnapshot.
- **Order.** #99 first; then the archive with replay and freshness; then the mirror
  manager (ChEMBL and BindingDB first); then MOLI's platform side.
- **Licences decide retention.** The registry's terms gain `retention` and `mirror`.
  What cannot be kept keeps its hash and is marked `retained: false`.

## Knowledge store format 2 (2026-09-30)
uibcdf/sabueso#99.
- **When a statement was read belongs to the state, not to the row.** A SourceAssertion
  row is its content without `retrieved_at`, which `card_sa` keeps per state (through
  `retrieval_times`: a card holds few distinct times). A card rebuilt with unchanged
  knowledge shares every row with its previous revision. Pinned ids do not change: the
  snapshot id is computed on the whole card, before storage, and every read rebuilds and
  checks it.
- **Integer keys.** Membership rows repeated two long hex keys, in the table and in
  each index (~150 bytes a row). States and rows are now numbered, and membership
  tables are `WITHOUT ROWID`.
- **Compression.** Documents and rows are zlib-compressed; ids are computed on the
  canonical JSON, never on stored bytes. A row read as text is format 1's.
- **Measured** on a live pilot store: 15.4 MB (format 1) to 4.7 MB (format 2); saving
  both cards again with unchanged knowledge adds 0.2 MB instead of about 5 MB.
- **Upgrade in place.** Format 1 rows are copied as written, and old tables dropped. A
  Sabueso that reads only format 1 refuses format 2 with its message.
- **The archive sits at `_http.urlopen`** (same day, #100, phase 1, first step). Every
  client already goes through it, so one hook archives the answers of all 23 sources,
  their headers and 404s included, without touching each client. `gather` runs each
  request in a copy of its caller's context, so concurrent lookups are archived too.
  A record's reference hashes what was asked, the answer's status, headers and
  content hash, and when; the content is stored once per SHA-256. A card lists the
  records its build made. Retrieval times still come from each client's clock, so
  replay waits for the next step: taking them from the answers.
- **Replay and reuse; times from the answers** (same day, #100, phase 1).
  - A client dated its answers with its own clock before asking, so a replay would
    have dated statements at replay time. Clients now open a stamp (`_http.stamp`,
    35 sites changed mechanically) whose value is the time of their first answer
    when an archive is active. A recorded statement and its record agree, and a
    replayed one keeps its original time.
  - `replaying(of=card)` follows the card's build: a request answered twice (UniProt's
    entry is fetched by the resolver and again by the card tool) gets its two answers,
    in order. Without `of`, the latest record answers. Live, TcTIM's build replayed
    without the network in 4.4 s and gave an identical card.
  - A request the archive does not hold raises `NotArchivedError`, a
    `ConnectorError`, so every client path handles it. `sabueso.resolve` turns those
    records into `not_queried` (`not_in_archive`).
  - `reusing(max_age)` is the design's `archive_first`: an answer archived within
    `max_age` is used, anything older is asked and kept.
- **Answers attributed to their source; retention from the licence** (same day, #100).
  - Several sources share a service (RCSB PDB and PDB CCD one GraphQL endpoint;
    PubChem and PubChem BioAssay PUG REST; ClinVar, MedGen and NCBI Gene E-utilities),
    so a URL cannot name the source. The client says it: `stamp(source)`, with the
    name its SourceAssertions carry; a test checks every name has recorded terms.
  - Retention is derived when read, from the licence (`retention_from_licence@1`), so a
    change of policy never rewrites the archive. Per-record terms (a depositor's, a
    publication's) and unrecorded ones are `keep: internal`, `share: unknown`.
  - A statement links to its source's answers in the build (`explain`, basis
    `source_in_build`), without threading record ids through clients and mappings.
  - Replay made visible that UniProt's entry was read twice per protein build. The
    resolver now keeps the entries it read for the card tool; the second request is
    gone.
  - A replay's missing answer is not a failure, and no longer warns as one.

## Local mirrors, BindingDB first (2026-09-30)
uibcdf/sabueso#100 (phase 2), #98.
- **Manager.** `sabueso.mirrors`: install, status, update (`manual`, `notify`, `auto`
  keeping the previous releases), remove; releases side by side under a directory the
  user names; `using()` makes card tools read installed mirrors (`mirror_first`) or
  never the network (`offline`). A card records the access route and release.
- **BindingDB first**: its monthly TSV (about 600 MB) with a published MD5 was indexed
  by UniProt accession in 154 s (3.65 M records, 704 MB). ChEMBL, several GB, next.
- **Parity with the service**, measured: identical for TcTIM and HsTIM; for EGFR the
  service rounds values the release states with more precision (2,876 records), and
  about 0.2 % of records differ between the live service and the monthly release.
  Both are recorded: a card names its access and release.
- **The release's InChIKeys are not an identity anchor.** For 39 of 112 sampled EGFR
  monomers they drop the stereo layer that UniChem's standard key keeps (one names
  another compound). Anchoring on them would merge stereoisomers, so identity stays
  with UniChem; repeated lookups are saved by `archive.reusing(...)`.
- **Offline** refuses every request not answered by a mirror or an archive
  (`OfflineError`), and the source is `not_queried` (`offline`), never absent.

## ChEBI: classes and roles of a molecule (2026-09-30)
uibcdf/sabueso#83 (wave 2, chemistry).
- **Joined on stated grounds only.** UniChem lists a structure's ChEBI ids; ChEBI states
  each entry's standard InChIKey. An entry becomes part of a card like any other record
  keyed by its stated InChIKey (`build_molecule_cards`), so an entry whose key is
  another is never merged.
- **Batched.** ChEBI 2.0's `compounds/` answers up to 200 ids per request (about 12 s),
  and a secondary id with its primary entry.
- **Roles, direct or inherited.** `roles_classification` lists every role ChEBI
  classifies an entry with, including those it inherits through its classes and parent
  roles (vincristine is a "Bronsted base" through "tertiary amino compound"). Both are
  kept, and `direct` marks the entry's own `has role` statements, so a reader never
  takes an inherited role for a curated one.
- **The definition's markup** (`C<sub>46</sub>…`) stays in the assertion, as written;
  the field's value is its plain text (`normalized_value`).
- Names and formula are not taken: ChEMBL and PubChem state them already, and a second
  spelling would add disagreements without knowledge.

## gnomAD's consequence on the canonical transcript (2026-09-30)
uibcdf/sabueso#85, found while evaluating Ensembl for wave 2 of #83.
- **Ask the source that states it.** Asked for a gene, gnomAD states each variant's
  consequence on the one transcript it ranks most severe. Asked for a transcript, it
  states each variant's consequence on that transcript, with its version, in one
  request (EGFR: 5,942 variants, 3 s). Sabueso now asks for the gene and for each
  Ensembl transcript UniProt states for the canonical isoform.
- **The canonical statement comes first.** A protein change gnomAD states on the
  canonical transcript is kept as stated, and the residue check still applies. A
  variant gnomAD states changes no residue there (intron or UTR) is not placed
  (`not_coding_on_canonical`) and records that consequence, even where UniProt's
  isoform map would place it: the same DNA change can shift a residue on one isoform
  and none on the other. For TPI1, a frameshift at isoform 3's Pro40, which the map
  had placed at canonical Pro3, is a 5' UTR duplication on the canonical transcript.
- **What it changed**, over nine genes: the variants on transcripts UniProt does not
  state fell from 810 to 533 (MAPK14 12 → 0, EGFR 161 → 88, BRCA1 83 → 38), and 328
  are now stated as not coding on the canonical transcript.
- **What is left, checked variant by variant** (same day), on 22 human proteins: the
  nine above; glycolytic enzymes (GAPDH, PGK1, ENO1, ALDOA, LDHA, PKM); genes with
  hard isoforms (CDKN2A, MAPT, APP, CD44); BRAF, PRKDC and ATM. That is 52,928
  protein changes. gnomAD's variant query states every transcript a variant has a
  consequence on. For all 1,682 changes left on transcripts UniProt does not state,
  it states no protein change on the canonical transcript:
  - 1,205 are intronic (1,191) or in the 3' UTR (14) there. The transcript query
    covers the coding region with a margin, so it does not return them.
  - For 477, gnomAD states no consequence on the canonical transcript at all. They
    lie outside it: TP53's alternative 3' exons, and CDKN2A's exon 1β of p14ARF,
    another UniProt entry.
  - None is coding on the canonical transcript.

  They are changes on other proteins or on other exons: PKM's alternative exon, and
  MAPT's exons the canonical transcript skips.
- **Ensembl adds no stated map for them.** For the transcripts left, Ensembl states a
  separate TrEMBL entry (e.g. Q504U8, E7EQX7) or no translation any more, so there is
  no stated route to canonical positions. Alignment (#85 step 2) is not built: it
  would place changes of other exons and other proteins on this one.
- **Only transcripts gnomAD annotates are asked.** UniProt may cross-reference Ensembl
  transcripts newer than the dataset's GENCODE release (ENO1: 17, of which gnomAD
  annotates one). gnomAD's gene record lists its transcripts, so a request is sent
  only for those. The others are recorded as `not_in_dataset`, and the gnomAD
  service's rate limit is not spent on them.
- **A transcript UniProt names no isoform for is not the canonical one** in an entry
  that describes isoforms. CD44's ENST00000442151 (a 294-residue protein) was taken
  as canonical; the residue check stopped its 3 changes. Such a cross-reference is now
  canonical only in an entry without isoforms (`_hgvs.transcript_context`).
- `uniprot_isoform_map@1` stays for ClinVar, and for a gnomAD variant the canonical
  answer does not state.

## KLIFS: kinase pockets and conformations (2026-09-30)
uibcdf/sabueso#83 (wave 2, family-specific sources).
- **Joined through the accession KLIFS states.** KLIFS's kinase list states each
  kinase's UniProt accession (1,127 kinases, human and mouse, one request per process).
  A protein with two kinase domains is two KLIFS kinases (JAK1 and JAK1-b), and the card
  holds both.
- **What a card gains.** For a kinase:
  - the classification (group, family, subfamily);
  - per structure, the conformation KLIFS assigns (DFG in, out or out-like; αC helix
    in or out), the orthosteric and allosteric ligands, and the quality;
  - the 85 pocket positions in KLIFS's common numbering (gatekeeper `GK.45`, hinge,
    `xDFG`).

  Type I and type II inhibitors differ by DFG state, and the pocket positions compare
  across kinases.
- **The pocket in UniProt numbering, through statements only.** KLIFS states the
  pocket residues in one structure's author numbering. The structure is chosen by
  `klifs_pocket_reference@1`, among the kinase's structures the card holds with RCSB's
  author numbering. The order is:
  - a pocket equal to the kinase's (no mutation, no gap);
  - then the highest quality score;
  - then the fewest missing residues and atoms;
  - then the best resolution;
  - then the lowest KLIFS id.

  It is placed with `rcsb_author_numbering@1`, and the residue must be UniProt's. No
  sequence is aligned. For EGFR the gatekeeper is T790, the residue of the T790M
  resistance mutation, so the pocket joins the variant annotations by position.
- **One request per kinase for the pocket.** `interactions_match_residues` answers one
  structure at a time. One structure is enough to place the kinase's 85 positions; if
  another structure's numbering disagreed, the residue check is the guard. Without a
  structure on the card, the
  pocket stays in KLIFS numbering (`no_structure_loaded`), and no pocket request is
  sent.
- **Terms.** No formal licence was found. The FAQ states the data is free and open for
  academia and industry, and asks to be cited. The registry records it as no
  restrictions of its own, with that caveat (`RISKS_AND_OPEN_QUESTIONS.md`).
- **In packets since `packet_aspects@3`** (2026-10-01): classification in
  `identity`, conformations in `structures`, pocket in `ligand_sites`.
- **Not taken now:** KLIFS's interaction fingerprints per structure (one request each),
  its ligand bioactivities (ChEMBL's, already on the card) and its drug list.

## GPCRdb: GPCR numbering and structure states (2026-09-30)
uibcdf/sabueso#83 (wave 2, family-specific sources).
- **Joined through the accession GPCRdb states.** One request finds the receptor of a
  UniProt accession (`protein/accession/<acc>`), and two more read its residues and
  structures. A protein that is not a GPCR is `not_found`.
- **What a card gains.** For a receptor:
  - the class and family;
  - the segments (TM1-7, loops, H8);
  - the generic number of each residue, in every scheme GPCRdb states. The same
    position compares across receptors (D3.32 of aminergic receptors, the DRY motif
    at 3.50, the toggle switch W6.48).
  - per structure, the activation state, the ligands with the function GPCRdb states
    (agonist, antagonist, inverse agonist, allosteric), and the signalling protein.

  This is the vocabulary of GPCR drug design: the state a ligand stabilises, and the
  positions shared across a family.
- **Numbering through sequence identity, not similarity.** GPCRdb numbers residues on
  the sequence its entry states. Its numbers are UniProt's when that sequence is the
  card's UniProt sequence, character by character (`gpcrdb_sequence_numbering@1`), and
  each residue must still match. This is an equality check of two stated sequences,
  not an alignment. When they differ, everything stays in GPCRdb's numbering.
- **Apo is not a ligand.** GPCRdb writes a structure without ligand as a ligand named
  "Apo (no ligand)" with the code `apo`. The card records `apo: true` and no ligand, so
  no false chemical component enters the card.
- **In packets since `packet_aspects@3`** (2026-10-01): classification in
  `identity`, states in `structures`, segments and generic numbers in
  `sequence_features`.
- **Not taken now:** GPCRdb's mutation data. They are literature mutagenesis with
  ligand effects, often with empty fields (the first β2AR record states only the
  mutation). They are read when a use asks.

## Membranes: segments through RCSB, OPM's own API deferred (2026-09-30)
uibcdf/sabueso#83 (wave 2, structures).
- **OPM's API** answers per PDB entry:
  - the hydrophobic thickness, tilt and transfer energy;
  - the membrane type and which side is cytoplasmic;
  - per subunit, the transmembrane segments.

  But:
  - its subunits carry the letters of OPM's own model (C and D for 2RH1, whose PDB
    chain is A), so its segments cannot be placed through the PDB chain;
  - proteins are named by UniProt entry name;
  - no data licence was found on its site. The earlier "CC BY 3.0" could not be
    confirmed.

  Deferred.
- **RCSB integrates the segments**, with their origin. `MEMBRANE_SEGMENT` instance
  features come from OPM and PDBTM, in the PDB chain's entity numbering. Sabueso
  already reads instance features (secondary structure, #80), so the segments join
  `has_structure` as `membrane_segments`, per chain and per resource, in UniProt
  numbering through the entity alignment.
- **Each resource keeps its own segments.** For GPR52 (6LI0) OPM and PDBTM agree on TM1
  and differ by a residue or two elsewhere. Neither is chosen.
- **Statements of other entries are unchanged.** The segments enter RCSB's statement
  only when stated, so a soluble protein's statements keep their content.
- **What it serves.** Lipid-facing sites and membrane-accessible ligands are placed
  against the transmembrane span of the very structure that shows them.

## SAbDab: antibody complexes of a protein (2026-09-30)
uibcdf/sabueso#83 (wave 2, structures).
- **SAbDab2's annotations of the PDB.** The classic summary download now answers with
  the SAbDab2 web application. Its API publishes one JSON file (about 15 MB) with every
  antibody instance: heavy and light chains and their antigens, with the PDB entity and
  chain of each. It is read once per process, as SKEMPI's CSV is, with its SHA-256.
- **Joined through the chains UniProt states.** An antibody enters a protein's card
  when one of its antigens is a protein or peptide chain UniProt states is this protein
  in that PDB entry. Antigen names are never used. Haptens, sugars and ions carry the
  chain of the polymer they sit on, so they never make a protein an antigen.
- **Every antigen is kept, and marked.** SAbDab assigns as antigens the chains bound to
  the antibody in the structure. In 9IJR an scFv is listed with GPR52 and β-arrestin 1
  as antigens. The card keeps both, with `this_protein`, and does not claim the
  antibody recognises the receptor.
- **Antibodies are not entities yet.** Their chains, types and V gene subgroups are
  kept on the target's card. Antibody cards, CDRs and Thera-SAbDab's therapeutics wait
  for a use.
- **In packets since `packet_aspects@3`** (2026-10-01), in `structures`.

## Wave 2 of the source coverage plan, closed (2026-09-30)
uibcdf/sabueso#83.
- **In use:** ChEBI (molecules), KLIFS (kinases), GPCRdb (GPCRs), SAbDab (antibody
  complexes), and OPM's and PDBTM's transmembrane segments through RCSB. gnomAD now
  also reads the canonical transcript (#85).
- **Deferred or blocked, with the reason in the registry:**
  - the Chemical Probes Portal: no documented access; accessions only in pages;
  - SureChEMBL: mentions cannot be restricted to the claims;
  - OPM's own API: its own chain letters, and no licence found;
  - ESM Atlas: MGnify ids only.
- **Ensembl, deferred** once its service answered again (same day). For orthology:
  - its Compara answers in 44-52 s per gene;
  - it names orthologs as Ensembl genes, one cross-reference request each away from
    UniProt;
  - its vertebrate Compara has no trypanosomatids.

  OMA names orthologs by UniProt accession, and states TcTIM and human TPI1 as
  orthologs of each other. It is proposed as the orthology source (evaluating: its
  licence is to be confirmed).
- **Each source was surveyed for batch or bulk access and tested live before design**
  (whole files for SAbDab, one list request for KLIFS). Each joins only through an
  identifier its source states: an accession, the PDB chains UniProt states, or an
  InChIKey.

## OMA: orthologs, joined only through an exact match (2026-10-01)
uibcdf/sabueso#83, instead of Ensembl's Compara (deferred, 2026-09-30).
- **Why OMA.** It states pairwise orthologs across about 2,600 genomes, by UniProt
  accession where one exists, in one request per protein. That includes the
  parasite–host pairs the pilots compare. Human TPI1 has T. cruzi's TIM among its
  3,090 orthologs, 1:1.
- **The query joins only through an exact match OMA states.** OMA maps an accession to
  one of its proteins, sometimes of another strain, and says whether the sequence is
  the same (`seq_match`). TcTIM (P52270) is mapped to CL Brener's Q4DV43 with
  `modified`. Taking Q4DV43's orthologs for P52270 would be identity by similarity, so
  the card records `not_found` and names the protein OMA chose.
- **Orthologs named by stated identifiers.**
  - A UniProt accession OMA states is taken as is.
  - A Swiss-Prot entry name is resolved to its accession by UniProt, which states
    that; the name is kept as `canonical_id`.
  - Anything else (RefSeq, GenBank) stays `oma:<OMA id>`.
- **One relationship per OMA protein.** Identical proteins of several strains share one
  UniProt entry (Salmonella LT2 and 14028s, both TPIS_SALTY). `oma_id` is an identity
  qualifier, so each genome's ortholog keeps its species.
- **Options.** `rel_type` is filtered by OMA itself; `taxa` keeps exact taxon ids
  (strains are their own taxa, e.g. 353153 for CL Brener). The ceiling is 5000.
- **Terms.** CC BY 4.0, from OMA's Terms of Use as published in its browser's public
  source. The site's pages answer 403 to non-browser clients. An older FAQ line says
  CC BY-SA 2.5 for the browser, and both are recorded.
- **In packets since `packet_aspects@3`** (2026-10-01): the `orthology` aspect,
  asked by name.

## packet_aspects@3: the wave-2 sources in packets (2026-10-01)
uibcdf/sabueso#83, #88. `@2` was published in 0.7.0 and is not changed; `@3` is a new
version.
- **Where each source fits:**
  - KLIFS and GPCRdb classifications in `identity`, what the protein is;
  - kinase conformations, GPCR states and antibody complexes in `structures`, what
    each structure shows;
  - the kinase pocket in `ligand_sites`;
  - GPCR segments and generic numbers in `sequence_features`, positions on the
    sequence.

  Each enters an aspect's facts only when the card holds it, so a protein without
  them keeps the same facts.
- **`orthology` is an aspect of its own, asked only by name.** OMA gives thousands of
  orthologs per protein (3,090 for human TPI1), and packet size is watched (#88).
  With a comparator, the aspect says whether OMA states one protein an ortholog of the
  other, by the accessions the cards are anchored at, and nothing more. For HsTIM and
  TcTIM (P52270) that is empty, because OMA maps P52270 to another strain's protein.
- **Packets of different mappings are not compared.** `same_knowledge` is `None`, as
  for different formats.
- STRING and Europe PMC stay outside packets.

## Where a variant matters: gnomAD's pext (2026-10-01)
uibcdf/sabueso#102.
- **Sources surveyed.**
  - UniProt states tissue specificity as curated text, sometimes per isoform. PKM M1
    and M2 each have their own comment, and Sabueso already keeps the restriction on
    each SourceAssertion. It is text, not values to join with positions.
  - UniProt cross-references HPA, Bgee and Expression Atlas, which are gene-level.
  - GTEx's transcript medians (v8) give PKM's M2 transcript 217 TPM in skeletal muscle
    and the M1 ones 1-3, against the known biology. Short-read quantification cannot
    tell two mutually exclusive exons of one length apart, and GENCODE v26 lacks most
    transcripts UniProt states. Set aside.
  - gnomAD's pext (GTEx v10, GRCh38) gives, per coding region, the share of the gene's
    expression in each of 49 tissues that includes it. It recovers PKM's biology: the
    M1 exon reaches 0.58 in skeletal muscle and 0.01 in oesophagus. Chosen.
- **Stored as stated, joined by a rule.**
  - The pext regions are gnomAD's statements (`annotations.exon_usage_by_tissue`,
    option `exon_usage`, its own enrichment record, data `pext`).
  - `Card.variant_tissue_usage()` places each population variant's genomic position in
    its region (`pext_at_variant@1`, with the threshold as a parameter).
  - A variant outside every region is `outside_pext_regions`, never "not expressed":
    pext covers coding regions only.
  - Nothing derived is stored.
- **What it shows.**
  - TPI1's isoform-3 segment is expressed in testis only (0.38).
  - PKM's M1 exon is expressed in 23 tissues, and an alternative PKM transcript's
    region in none (86 variants).
- **It exposed a placement error.** Next to an exon the canonical transcript lacks, the
  residues on both sides are identical in the two isoforms (PKM's M1 exon, KRAS's exon
  4A). UniProt's isoform map placed changes there on canonical residues, but the
  canonical protein never carries them. gnomAD's transcript query did not catch them,
  because they are intronic on the canonical transcript, beyond its margin.

  Such changes are now asked of gnomAD variant by variant (25 per request) before the
  map is applied. In PKM and KRAS, 14 and 17 wrong placements are gone.
  `no_consequence_on_canonical` is new: gnomAD states no consequence on the canonical
  transcript at all.
- **Still open (#102):** a view per isoform, which needs each isoform's exons in
  genomic coordinates; and tissues as UBERON terms.

