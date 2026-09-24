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
Decided by the Sabueso owner (uibcdf/sabueso#25, `devguide/pending_proposals/molecule_identity.md`):
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

