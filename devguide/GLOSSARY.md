# Sabueso — Glossary

## Knowledge

- **Card**: a structured, nested object that represents one molecular entity (protein,
  peptide or small molecule). Its resolved values are linked to the SourceAssertions
  that support them. It has a stable `meta.card_id`, e.g.
  `sabueso:protein:uniprot:P52270`.
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
  produced it (e.g. `bioactivity_class@3`, `structure_state@1`), and is never stored as
  a SourceAssertion.
- **Knowledge state**: per area and source, whether a card knows something (`known`),
  sources disagree (`conflicting`), the source was asked and states nothing
  (`not_stated`), it was not asked (`not_queried`), it failed (`unavailable`), or it
  answered only for some requests (`partial`).
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
  standard InChIKey.
- **Ambiguous input**: a query that matches several plausible entities. The resolution
  returns `ambiguous` with its candidates, and `ambiguity_deck(resolution)` turns them
  into a Deck.

## Collections

- **Deck**: a collection of cards with operations for filtering, sorting, grouping,
  comparing and auditing. It records the membership basis of each card, the exclusions,
  and the operations that derived it.
- **Ligand deck**: the small-molecule cards of the ligands and measured molecules of a
  protein (`ligand_deck(card)`). A ligand's role (inhibitor…) is a derived class, never
  asserted.

## Storage and references

- **Snapshot id**: the content address of a card or deck state (`sha256:…`).
- **Pinned reference**: a reference to an exact state, whose meaning never changes:
  - `<card_id>@sha256:…` for a card;
  - `…#SA_…` for one of its items;
  - `sabueso:deck:<name>@sha256:…` for a deck.
  The form is provisional until uibcdf/moli#3.
- **KnowledgeStore**: Sabueso's native SQLite store of cards, decks and their revisions.
- **CurationStore**: a JSONL store of curated statements that survive rebuilds.
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
- **Clinical layer** *(planned)*: a section for pharmacology, ADMET, clinical trials and
  pharmacovigilance, kept apart from physicochemical and biological data (`ROADMAP.md`).
