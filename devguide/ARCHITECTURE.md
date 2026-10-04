# Sabueso — Architecture

What Sabueso is built of, after release 0.12.0 and the current development slices.
`DATA_FLOW.md` follows one resolution
through these parts; `PUBLIC_API.md` lists the public surface.

## Layers

Traceability is a required Sabueso product property, including failed or empty
source access. Knowledge support, observed execution and bibliography retain their
separate meanings. Runtime records must state their coverage and gaps; a returned
card or a citation list alone cannot establish complete pipeline provenance.
Published acquisition covers built-in UniProt, Europe PMC and RCSB entry, search,
mentions, annotations and structural clients. Unreleased development adds ChEMBL
logical operations and detached literal literature extraction (#108/#92, moli#36).
See `SOURCE_ACCESS.md` and the [implementation review](pending_proposals/design_implementation_review.md).
MOLI owns ProjectRecord composition and the future Recorda boundary; local records
do not implement project routing, EventLedger persistence or strict commit policy.

1. **Source access** (`sabueso.tools.db.<source>`, `SOURCE_ACCESS.md`).
   - Each source has:
     - a client with an online and a fixture implementation, sharing one protocol;
     - public `get_*` functions that return raw records in a provenance envelope.
   - Failures are `ConnectorError`; absences are `RecordNotFoundError`.
   - Sources in use are listed in `sources/registry.yaml`.
2. **Mappings** (`sabueso.mappings.<source>`). They translate a source record into:
   - field values;
   - relationships;
   - one SourceAssertion per value the source asserts.
   Mappings live apart from source access, so that a transformation is written once.
   **Enrichers** (`sabueso.enrichers`, #86) declare each source's contribution to a
   card once: its option, areas, organism coverage and three steps (requests, fetch,
   map). One runner handles coverage, failures and order, and the knowledge-state rows,
   migration map and packet options are derived from the declarations. Clients share
   the network, release-cache and key services of `tools/db/` (`SOURCE_ARCHITECTURE.md`).
3. **Aggregation and selection** (`core.aggregator`, `core.merge`,
   `resolver.field_resolver`).
   - Mapping outputs are merged into one card.
   - Each field is resolved from its SourceAssertions by the selection rules
     (`resolver/selection_rules.json`, `RESOLVER.md`).
   - Alternatives and conflicts are kept, never discarded.
4. **Entity resolution** (`resolver.entity_resolver`, `tools.resolve`).
   - `sabueso.resolve(query)` routes a query by namespace, to a protein card or a
     small-molecule or MONDO-anchored disease card.
   - The EntityResolver decides which entity a query or record refers to. It reports
     ambiguity instead of choosing, and audits identities
     (`protein_identity_audit@1`).
   - The decision is recorded on the card.
5. **The card** (`core.card`).
   - Nested sections of fields: each is `{value, source_assertion_ids}`, and a quantity
     is `{value, unit}`.
   - A `source_assertion_store` and a `relationship_store`.
   - `quality`: conflicts, alternatives, enrichments, resolution, curation, migration.
   - A `meta.card_id` that does not depend on storage, and a `schema_version`.
6. **Views and derived knowledge** (`core.structures`, `core.bioactivities`,
   `core.oligomer`, `core.ligand_sites`, `core.literature`, `core.knowledge_state`,
   `core.card_diff`, `core.identity_audit`, `core.measurements`, `core.names`…).
   - Card and deck methods read the stored knowledge and return views.
   - Everything a view derives (a class, a group, a state, a finding) carries the named,
     versioned rule that produced it, and is never stored as a SourceAssertion.
   - `core.structure_explanation` explains an inventory item and every member of its
     group through pinned relationships and SourceAssertions (`Deck.explain`, #91).
   - Unreleased `Card.explain_disease` and `Card.explain_knowledge_state` trace
     stored disease identity and state classification at exact pins. Scientific
     support, coverage inference and request reports retain separate bases; missing
     support remains explicit. Readers never fetch, mutate cards or add credit.
   - Unreleased `Card.explain_measurement` and `Card.explain_bioactivity` collect
     actual grouping and class-voter decisions at the card pin. Precision and
     threshold quantities retain units; copies, ambiguity and discordance remain
     explicit. Whole-card candidate/glossary inputs are context with exact support;
     stored identity metadata has locators, not invented assertion membership.
     These readers preserve the scientific rules/schema.
   - Unreleased `Card.explain_ligand_site` and `Card.explain_ligand` explain
     annotated overlaps and the protein/molecule deck crossing. Exact multi-card
     support, actual identity/class/name choices, annotated fields/conflicts,
     structure instances and native deck snapshot/membership metadata remain
     explicit. Duplicate deck members are not selected silently. Other derived
     views remain #91 work; the ligand record/group counter correction is #118.
7. **Decks** (`core.deck`). Collections of cards that record:
   - why each card is in (membership);
   - which candidates were left out;
   - the operations that derived the deck.
   Deck views compare, group, audit and inventory across cards.
8. **Curation** (`core.curation`, `core.curation_store`). What a publication states is
   recorded as a curated SourceAssertion:
   - field assertions, relationships, bioactivities, engagements and typed claims;
   - compared with the sources, never given priority;
   - kept across rebuilds by a `CurationStore`.
   Unreleased `tools.literature.extract_literature_mentions` runs a named literal
   rule on identified supplied text. Its statements, relationships and original
   attribution remain detached. Explicit card intake preserves original support;
   `ExtractionStore` retains exact original results independently of cards and
   human curation. Refresh preserves support and explicitly reuses supplied original
   receipts; a payload-only refresh reports missing runtime sidecars. Extractions
   never become human curation through `CurationStore` (#92).
9. **Storage and references** (`core.snapshot`, `core.knowledge_store`,
   `core.migration`, `tools.card.storage`, `tools.deck.storage`).
   - Content-addressed snapshots and pinned references, for cards, their items and
     decks.
   - The `KnowledgeStore`, a normalized SQLite store with revisions.
   - JSON, JSONL and SQLite files.
   - Honest migration and refresh of cards written by older schemas.
10. **Cross-cutting.**
    - Physical quantities through PyUnitWizard: never a bare number with its unit in a
      name.
    - Argument contracts through ArgDigest: one digester per argument name
      (`ARGUMENT_CONTRACTS.md`).
    - Diagnostics through SMonitor (`DIAGNOSTICS.md`).
    - Optional dependencies through DepDigest.
    - Required runtime attribution through Ackredit, with application-owned sessions
      and explicitly saved original records separate from scientific payloads.

## Core objects

- **Card** and **Deck** are the domain objects; users work on one card or on a deck.
- **Relationships** (`subject_ref predicate object_ref`, with qualifiers) are first-class
  knowledge between entities. Examples: `has_structure`, `has_bioactivity`,
  `interacts_with`, `classified_in`, `has_interface_with`, `engages`.

## Ops and tools

- **Ops** are methods on Card and Deck with consistent semantics: compare, filter, sort,
  views, tables.
- **Tools** are public functions, grouped by module:
  - `tools.db.*` for source access;
  - `tools.card.*` and `tools.deck.*` for building and storing cards and decks;
  - `sabueso.resolve` as the entry point.
- Tools are ad hoc by design.

## Design principles

- **Uniform SourceAssertion mechanism.** Every value is resolved from SourceAssertions
  through one model, and selection never discards them.
- **Knowledge, not project Evidence.** `SourceAssertion ≠ Evidence ≠ Provenance`. Nextia
  may cite Sabueso SourceAssertions as the basis of its own Evidence; Sabueso never
  creates Evidence.
- **Asserted and derived knowledge are different.** Derived knowledge names its rule, and
  is recomputed, not stored as an assertion. A ligand's role (inhibitor…) is a derived
  class, never asserted (#25).
- **Identity is never merged by similarity.** Two entries are one entity only when a
  source states it. Sequence similarity, a shared name or an equal residue number
  proves nothing; each is reported with its basis, for review.
- **Absence is not evidence.** What a source does not state, what was not asked, and what
  failed are told apart (`knowledge_state`).
- **Nested sections.** Cards are hierarchical and ordered, not flat.
- **Auditable decisions.** Selection rules, conflicts, resolution decisions and
  derivation rules are explicit and recorded.

## Planned, not built (from the original design)

- **Clinical layer.** Partly built (#81): ChEMBL's `clinical.max_phase`, its drug
  indications, and the trials they cite (`Card.clinical()`). Still planned:
  pharmacology, ADMET, pharmacovigilance, contraindications and interactions, as a
  section apart from physicochemical and biological data.
- **Peptide cards.** `entity_type: peptide` exists; peptide sources and views do not.
- **Inputs by sequence or structure file.** Resolution takes identifiers, names, and
  SMILES or InChI matched by PubChem (#93).
- **KnowledgeQuery and knowledge packets** (`SCIENTIFIC_POTENTIAL.md`): a prototype,
  released in 0.6.0 (`sabueso/core/packets.py`, #71), now with pinned full/index
  content, terms and attribution. MOLI #22 accepted the index guarantees; persistent
  consumer acceptance is still pending. General semantic query coverage remains partial.

Their status is tracked in `ROADMAP.md`.
