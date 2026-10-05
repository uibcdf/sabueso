# Sabueso — Public API

The public surface as of main after release 0.12.0. Anything not listed here, or not exported by
`sabueso`, is internal. Tools, views, stores and source access check their arguments
through ArgDigest. Plain accessors (`get`, `set`, `sort`…) do not, and fail loudly on
wrong types (`ARGUMENT_CONTRACTS.md` lists which is which). The user guide (`docs/`)
shows how to use them.

## Entry point

- Unreleased: `sabueso.extract_literature_mentions(text, identifier, publication, locator)`
  runs `literal_uniprot_mention@1` on supplied text with an explicit canonical UniProt
  accession and publication reference. It returns detached per-occurrence
  `source_assertions`, supported `relationships` and original `extraction_trace` with
  portable Ackredit attribution. Explicit namespace/official URL, case-sensitive
  token boundaries and Unicode offsets are required. It makes no card intake,
  curation, identity merge, article fetch or biological inference (#92).

- `sabueso.resolve(query, entity_type=None, profile=None, curations=None, extractions=None, **options)`
  returns `(card | None, resolution)`.
  - Unreleased: `extractions` accepts an `ExtractionStore` or its path. It explicitly
    applies original literal-rule results for the exact UniProt subject and records
    reuse. It does not execute extraction; fragment terms remain unknown.
  - `query` is an identifier (UniProt accession, `pdb:`, `pubchem:`, `chembl:`,
    `pdb.ligand:`, `inchikey:`, a structure (`smiles:`, `inchi:`, matched by PubChem,
    #93), a disease id: `mondo:`, `doid:`, `orphanet:`, `omim:`,
    `mesh:`, `efo:`… (#90)) or an `EntityQuery(name=..., organism=...,
    include_subtaxa=...)`. `entity_type` is `protein`, `small_molecule` or `disease`.
  - Options go to the card tool. For proteins:
    - `structures`, `interfaces`, `ligand_sites`, `family_sites`;
    - `chembl`, `bindingdb` (`{"cutoff", "limit"}`), `pubchem_bioassay` (`True` or
      `{"limit"}`), `string`;
    - `predicted_structures`, `taxonomy`, `ncbi_gene`;
    - `phi_base` (pathogen phenotypes, #83), `diseases`, `open_targets` and
      `orphadata` (disease associations, #82), `reactome` (pathways, #83), `clinvar`
      and `gnomad` (variants, #83), `skempi` (interface mutations, #83), `klifs`
      (kinase classification, structures and pocket, #83), `gpcrdb` (GPCR numbering
      and structure states, #83), `sabdab` (antibody complexes, #83), `oma` (orthologs, #83), `uniref` (sequence
      clusters, #103),
      `medgen` and `disease_identity` (identity of the card's diseases through MedGen
      and MONDO, #90), `europepmc` (publications whose text states the accession,
      #92);
      `europepmc={"article_ids": "PMC:PMC12400196"}` instead adds located accession
      mentions from explicit articles, with native locators and per-occurrence support
      (since 0.12.0). One MED/PMC id or a non-empty list is accepted; `limit` is not
      accepted with `article_ids`. It does not read names or scientific claims.
      Direct UniProt mentions remain `mentioned_in`. PDB mentions supported by
      source-stated structural associations add derived `structure_mentioned_in`
      relationships and conditional `literature().publications[].structure_mentions`,
      with both identity and occurrence support retained (since 0.12.0).
    - each source's `*_client`, and `resolver`.
  - For small molecules: `unichem`, `pubchem`, `chebi` (#83), `indications` and
    `trials` (#81).
  - For diseases: `mondo_client`.
  - Every card tool takes `terms` (`"commercial"` or `"non_commercial"`): only sources
    whose stated terms allow that use are asked (#94).
  - An option the tool does not take is refused, never ignored.
- `sabueso.resolve_protein_card`, `sabueso.resolve_molecule_card`: the card tools behind
  `resolve`; diseases through `sabueso.resolve_disease_card` (#90).
- `Card.acquisition_trace`, `EntityResolution.acquisition_trace` and
  `KnowledgePacket.acquisition_trace` (since 0.12.0, #108): detached runtime source
  events for declared built-in UniProt/Europe PMC/RCSB boundaries. Resolution failures
  returning no card retain their trace; escaping exceptions also carry it.
  `knowledge_packet` retains its intake, while composition from existing cards
  creates no new acquisition trace. Independent copies preserve original versions,
  routes, response identities, empty answers and failures. Saved scientific payloads
  return `None`; retain original JSON sidecars. Other sources/custom clients are
  explicitly unobserved. `SOURCE_ACCESS.md` defines the coverage and local formats.
  Unreleased chemical identity access adds CCD batches and both UniChem lookup
  methods, alongside ChEMBL/PubChem/BindingDB observation. `resolve_molecule_card`
  retains card/resolution traces; `ligand_deck` exposes `Deck.acquisition_trace`,
  including its native snapshot id, output card pins and input protein pin.
  The trace is detached from deck metadata/hashes. Saved or ordinarily derived
  decks have no new trace; preserve original sidecars explicitly.
  Unreleased PDBe-KB ligand-site and interface-residue access also retains
  separate aggregate query traces, native structural references and unknown versions.
  Listed providers/structures do not claim additional direct source access.
  Unreleased AlphaFold DB `prediction` access keeps native model identities,
  per-model versions, declared tool/provider/URL context and original source receipts.
  It downloads no linked artifact and claims no local model-generation execution.
  Unreleased InterPro `site_residues` access retains native signature/site context,
  header/fixture releases, original archive receipts, empty and failed outcomes.
  It runs no alignment/InterProScan and claims no direct member-database access.
- `sabueso.ambiguity_deck(resolution)`: the candidates of an ambiguous resolution as a
  Deck.
- `sabueso.resolve_disease_card(identifier)`, `sabueso.disease_targets(disease,
  limit=50)` and `sabueso.disease_drugs(disease, limit=50)`: a disease card, and decks
  of its targets and of the drugs whose indications name it (#90).
- `sabueso.ligand_deck(protein_card, ...)`: the small-molecule cards of a protein's
  ligands and measured molecules.
- `sabueso.expand(card, predicate, limit=50, options=None, terms=None)`: a deck of the
  cards of the entities a card relates to by a predicate, or several
  (`relationship_expansion@1`, #91). Also `Card.expand` and `Deck.expand`.

## Knowledge packets (prototype, #71; contract in uibcdf/moli#22)

- `KnowledgePacket.attribution` (since 0.12.0, #108) automatically retains a detached
  composition record outside the scientific payload and hashes. Its accessor returns
  an independent copy; payload-only saved readers return `None` and add no credit.
  Save the original JSON sidecar alongside the scientific packet.
  `sabueso.attribution()` yields an `AttributionRun`; its
  `records` accessor returns detached JSON records for completed packet composition.
  Its separate `acquisitions` accessor retains observed source operations, including
  failures. Collection is optional; runtime attachment is automatic.
  Unreleased `literature` separately collects original literal-extraction execution
  and intake/reuse events, including stored-support-only refresh gaps.
  Applications own Ackredit sessions. The required lazy adapter preserves per-result
  reused resources and contributes to enclosing captures/workflows; provider failures
  preserves knowledge and host records. Records carry source-record versions and
  exact support pins, separately from packets/terms. Acquisition uses the separate
  bounded source adapter described above. Ackredit is required in runtime
  metadata/recipe; public Ackredit 0.9.0 satisfies the qualified API floor.
  See the user attribution page and
  `examples/ackredit_pilot/`.

- `sabueso.KnowledgeQuery(subject, comparator=None, aspects=None, constraints=None,
  detail="full")`: `to_dict()`, `from_dict(data)`, `options()`. `detail="index"` gives,
  per aspect, what the cards hold and the reference of every item, without values
  (`packet_index@1`, #88).
- `sabueso.knowledge_packet(knowledge_query, store=None, packet_name=None, note=None,
  curations=None, **clients)` resolves, composes, and optionally stores.
- `sabueso.compose_packet(knowledge_query, subject, comparator=None)` composes from
  existing cards.
  In published `packet_aspects@6`, the literature aspect includes direct UniProt
  mentions and derived PDB mention context in both the index and unknowns. Automatic
  `knowledge_packet` acquisition requests bibliography only (`europepmc={}`);
  located annotations enter via explicit article intake on prebuilt cards, then
  `compose_packet`. The index cites separate relationships and names the structure
  mention rule; it does not copy fragments. Earlier packets keep their stored mapping.
- `KnowledgePacket`: `entities`, `facts`, `conflicts`, `unknowns`, `provenance`,
  `query`, `ref`, `format`, `detail`; `snapshot_id()`, `content_id()`,
  `same_knowledge(other)` (None across formats, aspect mappings and levels of detail),
  `cite(role, item_id)`, `item(role, item_id, store)`, `to_dict()`.
  `terms(use, store)` reads exact saved card pins and reports represented statement
  support, conflicts and stored dependencies (`packet_terms@1`, since 0.12.0).
  Full/index share the scope at `packet_aspects@6`; other mappings need an adapter.
  It uses the current packaged terms registry with review dates, without changing
  packet hashes/payloads or reconstructing a historical terms-registry snapshot.

## Card

- **Read.** `get(field_path)`, `extract(field_paths)`, `list_fields()`,
  `quantity(field_path)`, `quantity_columns(template)`,
  `relationships(predicate=None, object_ref=None)`.
- **Views.** Each derives knowledge with a named rule:
  - `structures(include_fragments=False, region=None)` and `predicted_structures()`;
  - `oligomer(*, agreement_rule="interface_site_agreement@2")` and `ligand_sites()`;
  - `interface_mutations()` (SKEMPI, with ΔΔG under `binding_ddg@1`, #83);
  - `variant_tissue_usage(threshold=0.1)` and `isoform_tissue_usage(threshold=0.1)`
    (the tissues expressing a variant's position or an isoform's coding bases, from
    gnomAD's pext, `pext_at_variant@1` and `isoform_exon_usage@2`, #102; with
    `gtex=True`, each tissue's UBERON or EFO term, `gtex_tissue_key@1`);
  - `sequence_differences(other)` (the positions where two equal-length sequences
    differ, nothing aligned, `equal_length_positions@1`, #103);
  - `diseases(grouping_rule="disease_grouping@2")` (unreleased default: every stored
    identity path, explicit contradictory/unfinished branches, #90/#115).
    `grouping_rule="disease_grouping@1"` reproduces the published historical lookup;
  - `terms(use)` (what the sources state about a use of the card's knowledge,
    `terms_propagation@1`, #29; also `Deck.terms(use)` and `Deck.admissible(use)`);
  - `bioactivities(include_indirect=False, thresholds=None)`;
  - `ligands(deck, ...)` and `compare_ligands(deck, other, other_deck, ...)`;
    unreleased keyword-only `counting_rule="ligand_measurement_count@2"` counts
    distinct included groups across matched molecule items; explicit `@1` retains
    the published source-record counter. `bioactivity.records` reports distinct
    included source relationships under either rule. `measurement_counting` records
    the rule, original input pins and counting bases (per side for comparisons);
  - `literature()` and `claims(topic=None)`;
  - `clinical()` (molecules: indications and trials, #81);
  - `knowledge_state()`;
  - `acquisition()` (how the card's statements entered: database, curation,
    extraction, #92);
  - `entities()` and `entity(ref)`;
  - `compare(other, fields=None)` and `compare_knowledge(other, residue_map=None)`.
- **Tables.** `table(view, **options)` gives flat rows; `sabueso.to_dataframe(rows,
  units=None)` needs pandas.
- **Literal extraction (unreleased).**
  - Unreleased `Card.add_literature_extraction(extraction)` preserves delivered
    literal-rule support and returns a detached reuse event. An older card must be
    explicitly migrated first; different subjects and inconsistent support are refused.
    `Card.literature_intake_traces` returns copies of original runtime events and is
    empty for payload-only readers. Unknown fragment terms cannot enter a terms-profile
    card. `ExtractionStore(path).save(extraction)` preserves the exact original result;
    `records()` reads without credit and `apply(card)` explicitly reuses matching
    records. Neither API uses `CurationStore`.
- **Curation.**
  - `add_literature_assertion(field_path, value, publication, curator, ...)`;
  - `add_literature_relationship(...)`;
  - `add_literature_bioactivity(...)`;
  - `add_literature_engagement(...)`;
  - `add_literature_claim(topic, text, publication, curator, ...)`.
- **Identity and references.** `id`, `snapshot_id()`, `pinned_ref()`.
- **Serialization.**
  - `to_dict()`, `to_json(path)`, `to_sqlite(path, ...)`;
  - `Card.from_dict(data)`, `Card.from_json(path)`, `Card.from_sqlite(path, ...)`.
- **Provenance.** `explain(source_assertion_ids)`: each SourceAssertion's field,
  subject, source, record, version, retrieval and asserted value (#91).
  `explain_literature(publication_ref)` explains the publication's links and both
  legs of structural mention context, with pinned references, qualifier alternatives
  and recorded unlinked PDB mentions (`literature_explanation@1`, since 0.12.0).
  Missing links are `not_on_card`; missing stored support is `partial`.
  Unreleased `explain_disease(disease_ref)` explains a MONDO disease group at the
  exact card pin (`disease_group_explanation@2`), following stored association and
  selected annotation-member support, MedGen/MONDO identity and hierarchy steps.
  Stored alternatives/conflicts and whole-card ungrouped context remain visible;
  missing support is `partial`; contradictory targets are ungrouped. Keyword-only
  `grouping_rule="disease_grouping@1"` explicitly uses the historical view and
  `disease_group_explanation@1`, including its exposed lookup ambiguity. No source
  is asked. `MONDO:<seven-digit id>` and `mondo:MONDO:<seven-digit id>`
  select groups, never names or cross-ontology aliases.
  Unreleased `explain_knowledge_state(knowledge_area=None, knowledge_source=None)`
  explains all state rows or an exact area/source selection at the current or
  loaded historical card pin (`knowledge_state_explanation@1`). Selected fields,
  alternatives/conflicts and counted UniProt relationships have original support;
  absence/curation coverage and matched enrichment reports are classification
  inputs, not negative assertions. Report locators use the pin, field path and
  index; load that card to read them. Related scientific knowledge is separate
  context with per-request membership explicitly `not_recorded`.
  Missing support is `partial`, including fields/relationships whose source can
  no longer be identified. A missing row is `not_on_card`, never evidence of absence.
  No source is asked, mappings rerun, card changed or execution credit added.
  Unreleased `explain_measurement(measurement_ref)` selects an exact native `REL_`
  record or `MG_` group at this card pin (`measurement_group_explanation@1`). It
  retains actual grouping joins, publication/molecule keys, precision quantities,
  provenance selectors, ambiguity, unresolved-copy and review diagnostics.
  Unreleased `explain_bioactivity(molecule_ref, include_indirect=False, thresholds=None)`
  selects the exact namespaced item key returned by `bioactivities()`
  (`bioactivity_explanation@1`). Pass the same options as the explained view. Each
  group retains included records, voters, voter classes and copy-only fallback;
  strongest-class selection and discordance remain explicit. Original measurement
  units, ranges, single-point concentrations, thresholds and consistency checks survive.
  Both readers retain exact relationship/assertion pins and original source versions.
  Whole-card grouping/glossary inputs are separate context because candidate
  uniqueness depends on them. Stored identity records have card/field/key locators,
  never invented SourceAssertion membership or identity paths. Missing input support
  is `partial`; a missing item is `not_on_card`, never inactivity. These readers fetch
  nothing, change no card or credit and do not resolve aliases or explain ligand
  deck/site aggregation. The existing scientific rules and stored schema are unchanged.
  Unreleased `explain_ligand_site(ligand_site_ref)` selects the native `REL_` id
  from `ligand_sites()` (`ligand_site_explanation@1`). It retains the actual
  `annotated_site_overlap@2` result, selected annotation fields, alternatives,
  conflicts, original support, numbering and stored structural-instance context.
  No stored annotation/overlap is not external absence; absent instance data keeps
  `spans_chains=None`, and source relevance statements remain separate.
  Unreleased `explain_oligomer(*, agreement_rule="interface_site_agreement@2")`
  explains the complete matching `oligomer()` view under `oligomer_explanation@2`:
  actual partner-class and agreement rules, the card
  anchor, source assembly alternatives/methods, interfaces and exact family-site
  members. Relationships/assertions and field/index locators retain the original
  pin, versions and bibliography; selected, competing and conflicting support
  stay separate. Structural support is relationship-level, not invented mapping
  lineage for individual qualifiers. Source aggregate residues are not allocated
  to individual assemblies. Missing/empty assembly data and original source
  request outcomes remain distinct. Missing support is partial; no stored input
  is `not_on_card`, never external absence. Default agreement `@2` requires
  declared UniProt numbering, the exact family sequence reference and 1-based
  indexing, with no conflicting interface numbering/positions (#120).
  The interface must state the card's exact subject; missing positions and
  nonpositive indices prevent comparison even with a numbering declaration.
  A row is `comparable`, `undetermined` or `not_comparable`, with original context
  and reasons. Uncomputed `both`/`family_only`/`observed_only` are None; a computed
  empty set is an empty list. `agreement_state` distinguishes missing inputs,
  no comparable site, partial and fully computed views. Unconfirmed comparisons
  keep the explanation partial. Explicit `agreement_rule="interface_site_agreement@1"`
  in either reader reproduces the legacy integer-only view and
  `oligomer_explanation@1`, including at historical pins. No
  acquisition, credit, alias resolution, schema change or local method execution
  occurs; saved scientific payloads cannot recreate original runtime attribution.
  Unreleased `explain_ligand(molecule_ref, deck, include_indirect=False, thresholds=None, *, counting_rule="ligand_measurement_count@2")`
  selects the exact SmallMoleculeCard id from `ligands(deck)`
  (`ligand_deck_explanation@2`). Protein and molecule inputs keep distinct pins.
  Actual identity links, class selection, names, measured groups, sites, structure
  flags and deck membership remain visible. Duplicate deck members are retained
  as multiple `items` with partial status, never selected by snapshot/order.
  The deck's native snapshot id and metadata locate its supplied contents; they
  are not invented KnowledgeStore deck references. Load a saved named/pinned deck
  separately for historical reads. Missing support is partial, missing items are
  not absence, and readers acquire nothing or add credit.
  The #118 correction counts distinct included group ids in `bioactivity.measurements`
  and source relationship ids in `bioactivity.records`. Crossing inputs retain both
  sorted id lists, including groups spanning matched molecule/parent items.
  Explicit `counting_rule="ligand_measurement_count@1"` reproduces the published
  numeric counter, including at historical pins; it still adds the new `records`
  field and counting metadata. Neither historical views nor saved cards are rewritten.
  The explanation records its selected count policy alongside nested support;
  measurement identity, class/voter, assay-scope and site policies are unchanged.
  Missing activity-only originals retain the exact `copy_of` pointer with
  `original_not_on_card` in unresolved-copy diagnostics (#117, unreleased fix).
  A later provenance or statement join removes that singleton diagnostic. This
  describes final local grouping, not external absence or proof that a named
  original was acquired; original pointers remain in pinned relationship support.
- **Other.** `to_deck()`, `expand(predicate, ...)` (see `sabueso.expand`).

## Deck

- **Build.** `Deck(cards)`, `add(card, basis=None)`, `extend(cards)`,
  `exclude(candidate, reason, by=None)`, `basis(card_id)`.
- **Explain.** `explain(card_id)`: why a card is in the deck, or why it was left out,
  and the operations that produced the deck (#91).
  With `structure_ref="pdb:1SUX"` and the keyword options of `structure_inventory`,
  explains that protein's inventory item, its group or exclusion, named rules and
  relationship-level SourceAssertion support for all group members. Card and item
  references are pinned; no source is asked (`structure_inventory_explanation@1`).
- **Derive.** Each derived deck records the operation that produced it:
  - `filter(predicate)`, `sort(key, reverse=False)`;
  - `intersect(other)`, `difference(other)`;
  - `in_lineage(taxon)`;
  - `group_by(field_path)`, `group_by_rank(rank)`;
  - `expand(predicate, limit=50, options=None, terms=None)` (#91).
- **Views.**
  - `identity_audit()`;
  - `structure_inventory(regions=None, include_fragments=False, group_by=None,
    residue_maps=None, reference=None)`;
  - `unique_names(return_cards=False)`;
  - `summarize(fields)`, `compare(other, key_fields)`, `map(fn)`.
- **Identity and serialization.**
  - `ids()`, `snapshot_id()`, `to_list()`;
  - `to_jsonl(path)`, `to_sqlite(path, ...)`;
  - `Deck.from_jsonl(path)`, `Deck.from_sqlite(path, ...)`.

## Stores

- `sabueso.KnowledgeStore(path)`:
  - `save(card, note=None)` returns a pinned reference, and `load(ref)` reads it;
  - `history(card_id)`, `card_ids()`;
  - `source_assertion(ref)`, `relationship(ref)`, `relationships(object_ref=None,
    predicate=None, subject_ref=None, all_revisions=False)`;
  - `save_deck(deck, deck_name, note=None)`, `load_deck(name_or_ref)`,
    `deck_history(name)`, `deck_names()`;
  - `save_packet(packet, packet_name, note=None)`, `load_packet(name_or_ref)`,
    `packet_history(name)`, `packet_names()`;
  - `import_card_table(path, table="cards")`;
  - `as_of(ref, when)` and `revision_as_of(ref, when)`: the card, deck or packet as
    stored by a date, or None; `changed_since(ref, when)` for a card or a packet (#91).
- `sabueso.RetrievalArchive(path)` (#100), three contexts: `recording()` (every answer
  a source client receives is archived), `reusing(max_age)` (answers archived within a
  `datetime.timedelta` are used instead of asking again), `replaying(of=None)` (the
  network is never asked; `of` a card replays its build). A card built inside lists
  its answers in `quality.retrievals`. Also `get(ref)`, `find(method, url,
  request_body, max_age=None)`, `sources()` (answers per source, with what their
  licence allows: `sabueso.core.terms.retention`), `stats()`. `NotArchivedError` when a
  replay meets a request the archive does not hold. `Card.explain` links a statement to
  the answers its source gave the build.
- `sabueso.mirrors` (#100): `install(source, release="latest", mirror_dir=None,
  from_file=None, md5=None)`, `status(mirror_dir=None, check=False)`, `update(source,
  policy="manual"|"notify"|"auto", keep=2)`, `remove(source, release)`,
  `using(mirror_dir=None, mode="mirror_first"|"offline", releases=None)`. Sources:
  `bindingdb`. `OfflineError` when a request is made offline.
- `sabueso.CurationStore(path)`: `save(card)`, `apply(card)`, `records()`,
  `retract(source_assertion_id, reason, curator)`, `entities_named(name)`.
- `sabueso.migrate_card(data, store=None)` and `sabueso.refresh_card(card,
  curations=None, store=None, **options)`.
- Files: `save_card_json`, `save_card_sqlite`, `save_deck_jsonl`, `save_deck_sqlite`.

## Source access (`sabueso.tools.db`)

Raw records in a provenance envelope, one client per source (`SOURCE_ACCESS.md`):

- `uniprot.get_entry`, `rcsb.get_entry`, `pdb_ccd.get_components`;
- `pdbe_kb.get_ligand_sites`, `pdbe_kb.get_interface_residues`;
- `interpro.get_site_residues`, `alphafold.get_prediction`;
- `chembl.get_bioactivities`, `chembl.get_molecules`;
- `bindingdb.get_affinities`, `pubchem.get_compound`, `pubchem_bioassay.get_assays`;
- `unichem.get_compound`, `stringdb.get_partners`;
- `ncbi_taxonomy.get_taxon`, `ncbi_gene.get_gene`;
- `skempi.get_mutations`, `mondo.get_term`, `medgen.get_concepts`;
- `europepmc.get_mentions(identifier, limit=5000)` and
  `europepmc.get_annotations(article_ids)`: bibliography by explicit accession, or
  located accession annotations for explicit MED/PMC articles. The latter returns
  source-native sections, providers, tags and quote fragments without enriching cards
  or extracting scientific claims; article terms govern fragment storage (#92);
- `gnomad.get_variants`, `gnomad.get_transcript_variants`, `klifs.get_kinases`,
  `klifs.get_structures`, `gpcrdb.get_receptor`, `sabdab.get_complexes`, `oma.get_orthologs`, `uniref.get_clusters`.

Each source also has an `Online<Source>Client` and a `Fixture<Source>Client`. The legacy
`create_*_card_*` builders are deprecated and will be removed before 1.0.

## Errors

Defined in `sabueso/core/errors.py`:
- `SabuesoError`, the base;
- `ResolverError`, `SchemaError`, `StorageError`, `ConnectorError`;
- `RecordNotFoundError`;
- `MissingKeyError`, for a source that answers only with a personal key (#86);
- `ArgumentError`, a `ValueError` for refused arguments.

Diagnostics are SMonitor signals with stable codes (`DIAGNOSTICS.md`).

## Stability

- The package is pre-1.0. A breaking change is announced in the release notes, and
  deprecated names are kept until 1.0 when possible.
- Stored cards follow the card schema's versioning policy (`SCHEMA.md`), and older
  cards are read or migrated (`migrate_card`).
- The reference forms are provisional until uibcdf/moli#3 (#53).

## Explicit article metadata (unreleased, #92/#108)

`tools.db.europepmc.get_article(identifier, client=None)` returns the standard source
envelope for pubmed:/pmc:/doi: identifiers, with a detached acquisition trace. Its core
bibliographic projection excludes abstract/full text, preserves native identifiers,
author records, journal/pages/dates and licence declarations, and exposes matching
alternatives/truncation. `extract_literature_mentions(..., article_metadata=envelope)`
explicitly binds one complete source-stated publication identity with separate database
support under `article_metadata_binding@1`. Original fragment assertions/rule/unknown
rights stay unchanged. ExtractionStore, intake and refresh preserve original support;
literature views/explanations and exact packet support retain alternatives/citations.
`Card.terms` and pinned packet terms expose optional `declared_article_terms`; neither
the native licence literal nor an open-access flag grants supplied-fragment rights.
