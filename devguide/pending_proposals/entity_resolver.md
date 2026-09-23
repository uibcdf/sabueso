---
summary: Resolve source subjects to Sabueso entities (EntityResolver) and derive card identity from entities.
issue: uibcdf/sabueso#6
status: open
opened: 2026-09-23
closed:
verification: inspected
area: [resolver, identity, entities]
blocked_by: []
supersedes: []
---

# EntityResolver: from source subjects to Sabueso entities

## What

Sabueso needs an EntityResolver that links the subjects of SourceAssertions from different
sources to a single Sabueso entity, and that returns an explicit ambiguity Deck when an
input does not identify one entity. Card identity should then come from the entity, not
from one source record. MOLI Architecture 1.0 lists "EntityResolver vs FieldResolver
contracts" as open.

## How / evidence

Inspected on `main` on 2026-09-23:

- `sabueso/resolver/base.py` is a placeholder. Only the FieldResolver exists.
- Every SourceAssertion carries `subject_ref = <namespace>:<record_id>`, for example
  `uniprot:P52789`, `pdb:2NZT` or `interpro:IPR000001`.
- `meta.card_id` is derived from the primary identifier assertion, e.g.
  `sabueso:protein:uniprot:P52789`, so it names a source record.
- `tests/core/test_end_to_end_protein_sources_offline.py` merges UniProt P52789,
  PDB 2NZT and InterPro IPR000001 into one "protein" card. The PDB entry is a structure
  and the InterPro entry is a family, but nothing records how they relate to the protein.
- Cards built from annotation sources receive `entity_type = "protein"`, which gives
  identities such as `sabueso:protein:go:GO:0005524` for a GO term. The affected tool
  modules are `tools/db/go.py`, `interpro.py`, `cath.py`, `scope.py`, `ted.py`,
  `stringdb.py`, `biogrid.py` and `phosphositeplus.py`.

## Why

- Without entity resolution, cards cannot integrate sources correctly and card
  references do not mean "this molecule".
- `DECISIONS.md` requires ambiguous inputs to return a Deck with explicit ambiguity.
- Entity-level identity is also what the platform examples use
  (`sabueso:protein:TcTIM`). The reference grammar itself is decided in uibcdf/moli#3.

## Alternatives

- **Keep source-record identity and add cross-references:** simple, but every consumer
  would have to resolve entities itself.
- **Entity objects with typed relations to source records:** for example
  `has_structure → pdb:2NZT` and `member_of_family → interpro:IPR000001`. This preserves
  meaning and fits the relationship model in `future_direction.md`.
- **Scope:** inputs (accessions, names, sequences, SMILES/InChI) and ambiguity handling
  need a contract before implementation. The entity-type assignment of annotation-only
  cards is part of this theme.

## Acceptance criteria

- A written EntityResolver contract: inputs, outputs, ambiguity Deck, and the relation to
  the FieldResolver.
- Annotation-only sources are no longer typed as proteins, and merged cards record typed
  relations to non-protein subjects.
- Card identity follows the grammar decided in uibcdf/moli#3.
- Offline tests cover unambiguous, ambiguous and cross-source cases.

## Resolution

Pending.
