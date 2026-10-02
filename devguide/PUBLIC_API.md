# Sabueso — Public API

The public surface as of main after release 0.11.0. Anything not listed here, or not exported by
`sabueso`, is internal. Tools, views, stores and source access check their arguments
through ArgDigest. Plain accessors (`get`, `set`, `sort`…) do not, and fail loudly on
wrong types (`ARGUMENT_CONTRACTS.md` lists which is which). The user guide (`docs/`)
shows how to use them.

## Entry point

- `sabueso.resolve(query, entity_type=None, profile=None, curations=None, **options)`
  returns `(card | None, resolution)`.
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
      (unreleased). One MED/PMC id or a non-empty list is accepted; `limit` is not
      accepted with `article_ids`. It does not read names or scientific claims.
      Direct UniProt mentions remain `mentioned_in`. PDB mentions supported by
      source-stated structural associations add derived `structure_mentioned_in`
      relationships and conditional `literature().publications[].structure_mentions`,
      with both identity and occurrence support retained (unreleased).
    - each source's `*_client`, and `resolver`.
  - For small molecules: `unichem`, `pubchem`, `chebi` (#83), `indications` and
    `trials` (#81).
  - For diseases: `mondo_client`.
  - Every card tool takes `terms` (`"commercial"` or `"non_commercial"`): only sources
    whose stated terms allow that use are asked (#94).
  - An option the tool does not take is refused, never ignored.
- `sabueso.resolve_protein_card`, `sabueso.resolve_molecule_card`: the card tools behind
  `resolve`; diseases through `sabueso.resolve_disease_card` (#90).
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

- `sabueso.KnowledgeQuery(subject, comparator=None, aspects=None, constraints=None,
  detail="full")`: `to_dict()`, `from_dict(data)`, `options()`. `detail="index"` gives,
  per aspect, what the cards hold and the reference of every item, without values
  (`packet_index@1`, #88).
- `sabueso.knowledge_packet(knowledge_query, store=None, packet_name=None, note=None,
  curations=None, **clients)` resolves, composes, and optionally stores.
- `sabueso.compose_packet(knowledge_query, subject, comparator=None)` composes from
  existing cards.
  In unpublished `packet_aspects@6`, the literature aspect includes direct UniProt
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
  support, conflicts and stored dependencies (`packet_terms@1`, unpublished).
  Full/index share the scope at `packet_aspects@6`; other mappings need an adapter.
  It uses the current packaged terms registry with review dates, without changing
  packet hashes/payloads or reconstructing a historical terms-registry snapshot.

## Card

- **Read.** `get(field_path)`, `extract(field_paths)`, `list_fields()`,
  `quantity(field_path)`, `quantity_columns(template)`,
  `relationships(predicate=None, object_ref=None)`.
- **Views.** Each derives knowledge with a named rule:
  - `structures(include_fragments=False, region=None)` and `predicted_structures()`;
  - `oligomer()` and `ligand_sites()`;
  - `interface_mutations()` (SKEMPI, with ΔΔG under `binding_ddg@1`, #83);
  - `variant_tissue_usage(threshold=0.1)` and `isoform_tissue_usage(threshold=0.1)`
    (the tissues expressing a variant's position or an isoform's coding bases, from
    gnomAD's pext, `pext_at_variant@1` and `isoform_exon_usage@2`, #102; with
    `gtex=True`, each tissue's UBERON or EFO term, `gtex_tissue_key@1`);
  - `sequence_differences(other)` (the positions where two equal-length sequences
    differ, nothing aligned, `equal_length_positions@1`, #103);
  - `diseases()` (a protein's diseases grouped by MONDO term, `disease_grouping@1`,
    #90);
  - `terms(use)` (what the sources state about a use of the card's knowledge,
    `terms_propagation@1`, #29; also `Deck.terms(use)` and `Deck.admissible(use)`);
  - `bioactivities(include_indirect=False, thresholds=None)`;
  - `ligands(deck, ...)` and `compare_ligands(deck, other, other_deck, ...)`;
  - `literature()` and `claims(topic=None)`;
  - `clinical()` (molecules: indications and trials, #81);
  - `knowledge_state()`;
  - `acquisition()` (how the card's statements entered: database, curation,
    extraction, #92);
  - `entities()` and `entity(ref)`;
  - `compare(other, fields=None)` and `compare_knowledge(other, residue_map=None)`.
- **Tables.** `table(view, **options)` gives flat rows; `sabueso.to_dataframe(rows,
  units=None)` needs pandas.
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
  and recorded unlinked PDB mentions (`literature_explanation@1`, unpublished).
  Missing links are `not_on_card`; missing stored support is `partial`.
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
