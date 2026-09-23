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

Parts 2 and 3 are pending.
