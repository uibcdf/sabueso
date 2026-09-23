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

## Versioning (Pending Decision)
- Version strings use **x.y.z** (no leading `v`).
- Third‑party API URLs may include their own version segments (e.g., `/v1/`); do not change those.
- CardOps, DeckOps, and any internal Sabueso formats follow **x.y.z**.
- A formal **schema versioning policy** is required.
- Card and tool versioning must be defined before stable releases.

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
