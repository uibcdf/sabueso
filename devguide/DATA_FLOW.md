# Sabueso — Data Flow

One resolution, end to end: `sabueso.resolve(query, **options)`.

## 1. Route
- The query is an identifier (UniProt accession, `pdb:`, `pubchem:`, `chembl:`,
  `pdb.ligand:`, `inchikey:`, `mondo:` or a disease terminology MONDO maps) or an
  `EntityQuery`. [PUBLIC_API.md](PUBLIC_API.md) lists the supported forms.
- Its namespace decides the card tool: protein, small molecule or MONDO-anchored
  disease. `entity_type` explicitly selects the supported route.
- A named `profile` (e.g. `structural_baseline@1`) expands into options. Options passed
  explicitly override it.
- The route and the profile are recorded in `resolution.decision`.

## 2. Resolve the entity
- **Protein.**
  - The EntityResolver fetches the UniProt entry, or searches by name and organism.
  - It never resolves from a truncated or ambiguous result: it returns `ambiguous`
    with the candidates.
  - It applies its preference policy (`prefer_reviewed@1`) and audits the candidates'
    identities (`protein_identity_audit@1`: redundant entries, strain variants,
    paralogs, fragments).
  - With `curations=`, a curated name can anchor the resolution.
  - With `ncbi_gene=True`, NCBI Gene is asked about candidates whose gene loci are in
    different databases.
- **Small molecule.**
  - The card is anchored at the standard InChIKey.
  - Records of ChEMBL, the PDB CCD, PubChem and UniChem join it only through stated
    identities.
- **Disease.**
  - The card is anchored at a MONDO term. An external terminology identifier resolves
    only through MONDO's stated equivalence (`mondo_equivalence@1`), with its release
    and identity basis recorded.
  - A name or hierarchy relationship does not establish equivalence. An identifier
    without stated equivalence stays unresolved; obsolete MONDO terms report stated
    replacement candidates without choosing one automatically.
- The decision is kept as `quality.entity_resolution`: sources asked, rules applied,
  alternatives and identity links.
- An ambiguous result has no card. `ambiguity_deck(resolution)` turns its candidates into
  a deck of light cards.

## 3. Fetch and map
- The entry and each requested enrichment are fetched through their source clients
  (`tools.db.*`):
  - structures;
  - interfaces, ligand and family sites;
  - predicted models; taxonomy;
  - bioactivities (ChEMBL, BindingDB, PubChem BioAssay);
  - STRING partners;
  - disease definitions, terminology identity and hierarchy from MONDO.
- Each requested enrichment's outcome is recorded in `quality.enrichments`, whether
  `added`, `not_found` or `error`. A truncated result says so.
- Mappings turn each record into field values, relationships, and one SourceAssertion
  per asserted value. The SourceAssertion carries the source, its release, the record,
  the retrieval date and source metadata such as ECO evidence.

## 4. Aggregate and select
- Mapping outputs are merged.
- Each field is resolved from all its SourceAssertions by the selection rules. The
  selected value and its supporting `source_assertion_ids` are set on the card.
- Disagreements go to `quality.conflicts`, and alternatives to `quality.alternatives`.
  No SourceAssertion is deleted.
- Relationships from several sources are merged by identity. Disagreeing qualifiers are
  kept as `qualifier_conflicts`.
- Quantities are stored as `{value, unit}` and sealed (`quantities`), and are checked
  on load.

## 5. Curate (optional)
- `curations=` (a `CurationStore`) re-applies the statements curated for the entity.
  Their outcome is recomputed against the fresh sources: `new`, `corroborates`,
  `differs`, `not_comparable` or `not_compared`.
- A curator can add statements to the card. `CurationStore.save(card)` keeps them.

## 6. Read
- Views derive knowledge on demand, each with its named rule:
  - `structures`, `bioactivities`, `ligands`, `oligomer`, `ligand_sites`;
  - `literature`, `claims`, `knowledge_state`;
  - `compare_knowledge`.
- On decks: `identity_audit`, `structure_inventory`, `unique_names`, `group_by_rank`…
- `Deck.explain(card_id, structure_ref=..., ...)` follows an inventory item to its
  rules, stored inputs and supporting statements; all cards and items are pinned.
- `card.table(view)` gives flat rows. `sabueso.to_dataframe(rows)` gives a DataFrame,
  with quantities kept.
- Development `Card.access()` captures retained knowledge for machine reading;
  `Card.explore()` provides human navigation and `explorer.access` over the same
  explorer capture. Named scientific adapters read captured inputs without source
  acquisition. Source-stated roles and mechanisms keep their original support;
  derived concentration classes alone do not establish inhibitor roles.

## 7. Store and cite
- `KnowledgeStore.save(card)` stores a revision and returns its pinned reference
  (`<card_id>@sha256:…`). Items within it are cited as `…#SA_…` (provisional form,
  uibcdf/moli#3).
- Decks are saved and pinned the same way (`sabueso:deck:<name>@sha256:…`).
- A card of an older schema is converted by `sabueso.migrate_card`, which records its
  gaps. `sabueso.refresh_card` rebuilds it from its sources.
- Development exploration saving retains supported original views, machine
  requests, support and navigation. `sabueso.read_exploration(...)` verifies and
  reads them independently without Card rebuilding, acquisition or current
  scientific recomputation. Unretained optional scientific requests return
  `not_saved`. The [exploration architecture](ARCHITECTURE.md#development-exploration-and-saved-reading)
  distinguishes scientific rules, saved semantic formats and physical storage.

## Invariants

- SourceAssertions are created before any selection, and never deleted by it.
- Every field value points to the SourceAssertions that support it.
- Conflicts and ambiguity are reported, never resolved silently.
- Derived knowledge carries its rule and is not stored as an assertion.
- The SourceAssertion contract is in `SCHEMA.md`: `id`, `subject_ref`, `field_path`,
  `asserted_value`, `source`, `retrieved_at`, and optionally `normalized_value`,
  `source_metadata`, `provenance_ref`, `timestamps` and `confidence`.
