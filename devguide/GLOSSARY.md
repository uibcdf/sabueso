# Sabueso — Glossary

## Knowledge

- **Card**: a structured, nested object that represents one entity: a protein, small
  molecule or MONDO-anchored disease. Peptides have a schema type, without a peptide
  source or view yet. Resolved values are linked to the SourceAssertions that support
  them. A Card has a stable `meta.card_id`, e.g. `sabueso:protein:uniprot:P52270`.
- **SourceAssertion**: a record of what an external source (or a curated publication)
  asserts about an entity or property: value, field, source record, release and
  retrieval. It is stored in the card's `source_assertion_store`.
- **Curated SourceAssertion**: a SourceAssertion whose source is a publication, recorded
  by a curator with a locator and optionally a quote. It is compared with the databases,
  never given priority.
- **Relationship**: first-class knowledge between two entities (`subject_ref predicate
  object_ref`, with qualifiers), backed by SourceAssertions; e.g. `has_structure`,
  `has_bioactivity`, `interacts_with`, `classified_in`, `engages`. Stored in the
  subject card's `relationship_store`.
- **Derived knowledge**: what a view computes from stored knowledge, such as a class, a
  group, a state or an identity finding. It carries the named, versioned rule that
  produced it (e.g. `bioactivity_class@4`, `structure_state@2`), and is never stored as
  a SourceAssertion.
- **Concentration class**: a derived policy band over the retained measurement and
  its qualifier, units and thresholds. Development `bioactivity_class@4` admits a
  band only when the whole permitted concentration interval fits it; explicit `@3`
  retains the original interpretation. A band alone does not establish an inhibitor
  role, efficacy or selectivity. See the [activity contract](pending_bugs/bioactivity_interpretation.md).
- **Source-stated role or mechanism**: what an identified source states about a
  molecule in its declared context, retained with its supporting SourceAssertions.
  Chemical class/role membership does not establish activity against a particular
  target or a therapeutic effect.
- **Knowledge state**: per area and source, whether a card knows something (`known`),
  sources disagree (`conflicting`), the source was asked and states nothing
  (`not_stated`), it was not asked (`not_queried`), it failed (`unavailable`), or it
  answered only for some requests (`partial`). For biological context, which only
  curation states, "not queried" means nothing has been curated.
- **Biological context**: what decides whether a protein is worth studying as a target
  in an organism: stage expression, essentiality, accessibility and metabolic role
  (#60). Curated from publications as stated text.
- **Conflict**: disagreement among SourceAssertions for the same field or relationship
  qualifier. It is recorded, never resolved by deletion.
- **Measurement**: one experimental result, which several source records may state. The
  records are grouped by provenance or by statement (`measurement_identity@1`), and a
  copy never confirms its original.
- **Claim**: a curated free-text statement typed by topic, recorded and never compared.
- **Evidence** *(not a Sabueso concept)*: in the MOLI Platform, project-contextual
  scientific information in a Nextia DiscoveryProject that supports, contradicts or
  informs a Question or Hypothesis. It may cite SourceAssertions as its basis.
- **Provenance**: cross-cutting information about the origin, lineage, transformations
  and production context of any object. A SourceAssertion has provenance but is not
  provenance.

## Identity

- **Entity resolution**: deciding which entity a query or a source record refers to
  (EntityResolver). Ambiguity is reported (`ambiguous`, with candidates), never chosen
  silently.
- **Identity audit**: the findings among entries of related organisms
  (`protein_identity_audit@1`): `possibly_same_as` (for review), `same_gene`,
  `distinct_genes`. Nothing is merged.
- **Anchor**: the identifier a card is built on, such as a UniProt accession or a
  standard InChIKey for a molecule, or a MONDO identifier for a disease.
- **Ambiguous input**: a query that matches several plausible entities. The resolution
  returns `ambiguous` with its candidates, and `ambiguity_deck(resolution)` turns them
  into a Deck.

## Collections

- **Deck**: a collection of cards with operations for filtering, sorting, grouping,
  comparing and auditing. It records the membership basis of each card, the exclusions,
  and the operations that derived it.
- **Ligand deck**: the small-molecule cards of the ligands and measured molecules of a
  protein (`ligand_deck(card)`). Membership and derived concentration classes retain
  their stated bases; they do not make every member an inhibitor. Source-stated
  mechanisms remain separate knowledge.

## Storage and references

- **Snapshot id**: the content address of a card or deck state (`sha256:…`).
- **Pinned reference**: a reference to an exact state, whose meaning never changes:
  - `<card_id>@sha256:…` for a card;
  - `…#SA_…` for one of its items;
  - `sabueso:deck:<name>@sha256:…` for a deck.
  The form is provisional until uibcdf/moli#3.
- **KnowledgeQuery**: a structured question: a subject protein, an optional
  comparator, the aspects asked and constraints (`knowledge_query@1`, #71). Not natural
  language.
- **KnowledgePacket**: the composed answer to a KnowledgeQuery: pinned entities, facts
  per aspect with their rules, conflicts, unknowns and provenance
  (`knowledge_packet@2`; `@1` is still read). It holds each statement once and
  names it elsewhere. Distinct from a Deck, which holds whole cards. Referenced as
  `sabueso:packet:<name>@sha256:…`.
- **Content-equivalence id**: the id of a card or packet without retrieval times and
  the Sabueso version that built it. Two assemblies of unchanged knowledge share it;
  their snapshot ids differ.
- **KnowledgeStore**: Sabueso's native SQLite store of cards, decks and their revisions.
- **CurationStore**: a JSONL store of curated statements that survive rebuilds.
- **Saved exploration** *(development)*: retained human views and machine requests
  over detached Card captures, with original results, support and navigation.
  Independent reading verifies the recorded result without current scientific
  recomputation or source access. Its semantic format and physical representation
  are separate from the Card schema and scientific rule versions; see
  [the architecture](ARCHITECTURE.md#development-exploration-and-saved-reading).
- **Migration**: converting a card of an older schema, recording what it lacks
  (`migrate_card`); a **refresh** rebuilds it from its sources (`refresh_card`).

## Building blocks

- **Field path**: the canonical string of a field, e.g.
  `properties.physchem.molecular_weight` (`FIELD_PATHS.md`).
- **Selection rule**: a rule that picks a field's value among its SourceAssertions
  (FieldResolver, `RESOLVER.md`).
- **Mappings**: translation from source records to field values, relationships and
  SourceAssertions (`sabueso.mappings`).
- **Source access (tools.db)**: one module per source, with a client (online or fixture)
  and public `get_*` functions returning raw records with provenance.
- **Enrichment**: extra knowledge added when a card is built. Each outcome is recorded
  in `quality.enrichments`.
- **Profile**: a named, versioned set of enrichment options, e.g.
  `structural_baseline@1`.
- **View**: a card or deck method that returns knowledge derived on demand; `table(view)`
  gives it as flat rows.
- **Capture** *(development)*: the detached, validated Card state used by
  `Card.access()` and `Card.explore()`. `explorer.access` exposes the same explorer
  capture for machine reading. Here `live` means local active exploration, not a
  source refresh; saved reading retains the original capture.
- **Clinical layer** *(partly built, #81)*: indications (ChEMBL) and the trials they cite
  (ClinicalTrials.gov), shown by `Card.clinical()`. Planned: a section for pharmacology,
  ADMET, clinical trials and
  pharmacovigilance, kept apart from physicochemical and biological data (`ROADMAP.md`).
