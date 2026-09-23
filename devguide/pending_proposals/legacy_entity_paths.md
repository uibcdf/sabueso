---
summary: Retire legacy card paths that merge or mistype entities.
issue: uibcdf/sabueso#21
status: partial
opened: 2026-09-23
closed:
verification: inspected
area: [cards, entities, mappings, api]
blocked_by: []
supersedes: []
---

# Legacy card paths that merge or mistype entities

## What

Some card-building paths predate the EntityResolver contract
(`devguide/archive/entity_resolver.md`, #6). They still merge different entities or
mistype them. The current path is `resolve_protein_card`, which uses the
`entity_subjects` guard, relationships and the `Card.structures()` view.

## How / evidence

Inspected on `main` on 2026-09-23:

1. **PDB-entry cards typed as proteins.** `create_structure_card_*` and
   `mappings/pdb.py::map_structure` built one card per PDB entry with scalar
   `structure.entry_metadata.*` fields. They were structure cards in all but name.
2. **Annotation-only cards typed as proteins.** The GO, InterPro, CATH, SCOPe, TED,
   STRING, BioGRID and PhosphoSitePlus tools build cards with `entity_type="protein"`,
   e.g. `sabueso:protein:go:GO:0005524` for a GO term.
3. **Merges without the subject boundary.** `build_card_from_mapping` without
   `entity_subjects` lets any assertion feed fields.
   `tests/core/test_end_to_end_protein_sources_offline.py` still merges UniProt P52789
   with InterPro IPR000001 into one "protein" card.

## Why

As long as these paths exist, the public API can produce cards whose values come from
entities other than the card's subject. `devguide/SCIENTIFIC_POTENTIAL.md` names this as
the most damaging failure: a false entity merge is worse than an unresolved field
conflict.

## Alternatives

- **Keep the paths and document the caveats:** rejected. It keeps a known false-merge
  generator in the public API.
- **Remove or rework each path in favour of typed relationships and guarded entity
  cards:** selected.

## Acceptance criteria

- Part 1: no PDB-entry cards and no scalar structure fields.
- Part 2: annotation sources become typed relationships of protein entities
  (`member_of_family`, GO annotation, `interacts_with` with scores and methods) instead
  of protein-typed cards. Extending the relationship vocabulary is deliberate, and it is
  raised in uibcdf/moli if consumers outside Sabueso depend on it.
- Part 3: entity cards always use the `entity_subjects` guard. Unguarded merging is
  either removed or explicitly labelled as legacy, and the end-to-end test no longer
  merges a family into a protein card.
- Offline tests cover each part.

## Resolution

**Part 1: done** (`d23b9f8`, 2026-09-23, decided with the Sabueso owner):
- `create_structure_card_*`, `map_structure`, their tests and tutorials are removed;
- `structure.entry_metadata.*` is removed from both schemas and `FIELD_PATHS.md`;
- the showcase uses `resolve_protein_card` and `card.structures()`;
- `fetch_pdb_json` (raw entry) remains;
- entry title, dates and citation are currently unmapped (noted in
  `DATA_SOURCES_STATUS.md`).

**Part 2a: done** (2026-09-23). The additive part is the protein-centric knowledge that
UniProt already states, as typed relationships of the protein:
- GO cross-references become `annotated_with`, with `go_code` and `assigned_by`. This
  exposes, for example, that all 7 GO annotations of *T. cruzi* TIM are IEA, while
  human TIM has IDA, IPI and HDA annotations;
- InterPro, Pfam, Gene3D, SUPFAM, PANTHER, PROSITE and CDD cross-references become
  `classified_in`;
- curated INTERACTION comments become `interacts_with`, e.g. TIM–HTT with 6
  experiments.

The name `classified_in` replaces the `member_of_family` of the earlier draft, because
domains and sites are not families. Tests:
`tests/core/test_protein_knowledge_relationships_offline.py`.

**Part 2b: done** (2026-09-23, decided with the Sabueso owner):
- The GO, InterPro, CATH, SCOPe, TED, PhosphoSitePlus and BioGRID tools and mappings are
  removed, together with their tests, tutorials and API pages. They built protein-typed
  cards of terms, families, domains, a synthetic PTM format, and partner-name lists.
- The knowledge they were meant to provide now comes from the protein itself, as typed
  relationships stated by UniProt (part 2a).
- `annotations.go_terms` is removed from the schema, and `annotations.domains` is kept
  as reserved.
- The legacy end-to-end test that merged a protein and an InterPro family is removed.
- The BioGRID enricher is deferred to uibcdf/sabueso#22, because verifying it needs an
  access key.
- Not replaced yet: TED/SCOPe domain assignments, positional InterPro domains and
  PhosphoSitePlus PTM sites (noted in `DATA_SOURCES_STATUS.md`).
- **Part 2c: done.** STRING is an enricher of `resolve_protein_card`:
  - it produces `functionally_associated_with` relationships, a new predicate, because
    STRING edges are functional associations and not physical interactions. For
    example, TPI1–GAPDHS scores 0.999 from pathway databases (0.978) and fusion, with
    experiments at 0.137;
  - it records the channels, the query parameters and the STRING version
    (`source.version`, 12.0);
  - `create_string_card_online` and the partner-name field
    `interactions.binding_partners` are removed.

  Every enrichment outcome, from STRING and from RCSB, is recorded in
  `quality.enrichments`, and a failed enrichment no longer prevents the card. For
  example, *T. cruzi* TIM is `not_found` in STRING: its strain entry Q4DV43 is not
  attached silently.

  Also fixed a regression from part 2a: `structures="all"` would have fetched every
  relationship object (including `go:`/`pfam:` refs) as PDB entries. It now uses
  `has_structure` only. Tests: `tests/core/test_string_associations_offline.py`.

Part 3 is pending. Since uibcdf/sabueso#25 (2026-09-23), small molecules have an
identity anchor (the standard InChIKey, `resolve_molecule_card`). The legacy
`create_molecule_card_*` (ChEMBL) and `create_compound_card_*` (PubChem) paths still
derive `chembl:`/`pubchem:` card ids, so two identity schemes coexist for small
molecules. Part 3 should retire or migrate them.
