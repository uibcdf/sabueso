# Sabueso — Public API

The public surface as of release 0.4.0. Anything not listed here, or not exported by
`sabueso`, is internal. Every public function and method checks its arguments through
ArgDigest (`ARGUMENT_CONTRACTS.md`). The user guide (`docs/`) shows how to use them.

## Entry point

- `sabueso.resolve(query, entity_type=None, profile=None, curations=None, **options)`
  returns `(card | None, resolution)`.
  - `query` is an identifier (UniProt accession, `pdb:`, `pubchem:`, `chembl:`,
    `pdb.ligand:`, `inchikey:`) or an `EntityQuery(name=..., organism=...,
    include_subtaxa=...)`.
  - Options go to the card tool. For proteins:
    - `structures`, `interfaces`, `ligand_sites`, `family_sites`;
    - `chembl`, `bindingdb`, `pubchem_bioassay`, `string`;
    - `predicted_structures`, `taxonomy`, `ncbi_gene`;
    - each source's `*_client`, and `resolver`.
  - An option the tool does not take is refused, never ignored.
- `sabueso.resolve_protein_card`, `sabueso.resolve_molecule_card`: the card tools behind
  `resolve`.
- `sabueso.ambiguity_deck(resolution)`: the candidates of an ambiguous resolution as a
  Deck.
- `sabueso.ligand_deck(protein_card, ...)`: the small-molecule cards of a protein's
  ligands and measured molecules.

## Card

- **Read.** `get(field_path)`, `extract(field_paths)`, `list_fields()`,
  `quantity(field_path)`, `quantity_columns(template)`,
  `relationships(predicate=None, object_ref=None)`.
- **Views.** Each derives knowledge with a named rule:
  - `structures(include_fragments=False, region=None)` and `predicted_structures()`;
  - `oligomer()` and `ligand_sites()`;
  - `bioactivities(include_indirect=False, thresholds=None)`;
  - `ligands(deck, ...)` and `compare_ligands(deck, other, other_deck, ...)`;
  - `literature()` and `claims(topic=None)`;
  - `knowledge_state()`;
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
- **Other.** `to_deck()`. `expand(kind)` is reserved and not implemented.

## Deck

- **Build.** `Deck(cards)`, `add(card, basis=None)`, `extend(cards)`,
  `exclude(candidate, reason, by=None)`, `basis(card_id)`.
- **Derive.** Each derived deck records the operation that produced it:
  - `filter(predicate)`, `sort(key, reverse=False)`;
  - `intersect(other)`, `difference(other)`;
  - `in_lineage(taxon)`;
  - `group_by(field_path)`, `group_by_rank(rank)`.
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
  - `import_card_table(path, table="cards")`.
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
- `ncbi_taxonomy.get_taxon`, `ncbi_gene.get_gene`.

Each source also has an `Online<Source>Client` and a `Fixture<Source>Client`. The legacy
`create_*_card_*` builders are deprecated and will be removed before 1.0.

## Errors

Defined in `sabueso/core/errors.py`:
- `SabuesoError`, the base;
- `ResolverError`, `SchemaError`, `StorageError`, `ConnectorError`;
- `RecordNotFoundError`;
- `ArgumentError`, a `ValueError` for refused arguments.

Diagnostics are SMonitor signals with stable codes (`DIAGNOSTICS.md`).

## Stability

- The package is pre-1.0. A breaking change is announced in the release notes, and
  deprecated names are kept until 1.0 when possible.
- Stored cards follow the card schema's versioning policy (`SCHEMA.md`), and older
  cards are read or migrated (`migrate_card`).
- The reference forms are provisional until uibcdf/moli#3 (#53).
