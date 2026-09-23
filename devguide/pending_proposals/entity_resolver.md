---
summary: Resolve source subjects to Sabueso entities (EntityResolver), with a minimal traceable Relationship model, and derive card identity from entities.
issue: uibcdf/sabueso#6
status: open
opened: 2026-09-23
closed:
verification: inspected
area: [resolver, identity, entities, relationships]
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

The EntityResolver cannot be designed alone. Linking a protein entity to its experimental
structures, families or ligands requires relationships. Those relationships must be
first-class, traceable knowledge, not untraceable identifiers. This theme therefore also
covers the **minimal Relationship model** that entity resolution needs.

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
- STRING and BioGRID store `interactions.binding_partners` as a plain list of names.
  Score, interaction type, detection method, organism and direction are lost, which is
  the "relationship = untraceable identifier" pattern.
- `card.get()` returns `None` whether a value was not asserted, not queried or not
  mapped, so absence states collapse.
- A typical target entity has many experimental structures. Human and *T. cruzi*
  triosephosphate isomerase have 29 and 7 PDB cross-references respectively, all X-ray,
  in the UniProt fixtures P60174 and P52270 (inspected 2026-09-23). They span different
  constructs, ligand states and conformations. One UniProt entity relates to many
  structures, which cannot be one merged card.

## Design constraints (from `devguide/SCIENTIFIC_POTENTIAL.md`)

- **Identity comes before composition.** External identifiers (UniProt accession, PDB
  entity, ChEMBL target, synonym, paper name) are not canonical identity. The resolver
  maps them to a Sabueso entity.
- **Preserve uncertainty rather than manufacture equivalence.** Identity relations need
  distinctions such as `same_as`, `possibly_same_as`, `isoform_of`, `variant_of` and
  `derived_from`.
- **A false entity merge is more damaging than an unresolved field conflict.** Every merge
  decision must be auditable: which rule linked which subjects, and on what basis.
- **Relationships are first-class knowledge:**
  - subject, predicate and object;
  - qualifiers and context: organism, isoform, construct, mutation, assay, conditions;
  - the supporting SourceAssertions.
  Sabueso may behave like a graph without becoming a generic knowledge-graph framework.
- **Asserted ≠ derived.** A relationship stated by a source is backed by
  SourceAssertions. A relationship Sabueso infers, for example from an identifier
  mapping, carries a derivation record and never masquerades as a SourceAssertion.
- **Absence states stay distinct:** not found ≠ not queried ≠ not available ≠ unknown ≠
  evidence of absence. The resolver's outputs, including "no entity found", must not
  collapse them.

## Minimal Relationship model (scope of this theme)

Only what entity resolution and the first knowledge slice need:

```text
Relationship
  id               stable reference
  subject_ref      Sabueso entity or source-record reference
  predicate        controlled vocabulary (initially e.g. same_as, possibly_same_as,
                   isoform_of, has_structure, member_of_family, interacts_with)
  object_ref       entity or source-record reference
  qualifiers       {organism, isoform, chain/entity, construct, ...} when relevant
  source_assertion_ids   when asserted by a source
  derivation       when inferred by Sabueso (rule, inputs, version)
```

The relationship objects are the minimum needed to express:
- one protein entity with many experimental structures (`has_structure`);
- family membership;
- identity links between records of different sources.

Richer operations (`related_to`, `shared_ligands`, Deck algebra) are out of scope here.

## Why

- Without entity resolution, cards cannot integrate sources correctly and card
  references do not mean "this molecule".
- The first knowledge slice for any target needs "which experimental structures exist
  for this protein" and "which records describe the same entity". Both are entity plus
  relationship questions.
- `DECISIONS.md` requires ambiguous inputs to return a Deck with explicit ambiguity.
- Entity-level identity is also what the platform examples use
  (`sabueso:protein:TcTIM`). The reference grammar itself is decided in uibcdf/moli#3.

## Alternatives

- **Keep source-record identity and add cross-references:** simple, but every consumer
  would have to resolve entities itself.
- **Entity objects with typed relations to source records** (selected direction): for
  example `has_structure → pdb:2NZT` and `member_of_family → interpro:IPR000001`, each
  relationship backed by SourceAssertions or by a derivation record. This preserves
  meaning and follows `SCIENTIFIC_POTENTIAL.md`.
- **Generic graph library** (e.g. storing edges in a graph package): rejected as the core
  model, because scientific qualifiers, provenance and derivation matter more than the
  graph representation. A graph view may be offered later on top of Relationship
  objects.
- **Scope:** inputs (accessions, names, sequences, SMILES/InChI) and ambiguity handling
  need a contract before implementation. The entity-type assignment of annotation-only
  cards is part of this theme.

## Acceptance criteria

- A written EntityResolver contract: inputs, outputs, ambiguity Deck, identity relations
  (`same_as`, `possibly_same_as`, `isoform_of`, …), auditable merge decisions, and the
  relation to the FieldResolver.
- A minimal Relationship model, as above, with SourceAssertion backing or a derivation
  record, and no bare identifier lists for relationships in new code.
- Annotation-only sources are no longer typed as proteins. The cross-source end-to-end
  case links protein, structure and family subjects through typed relationships instead
  of merging them into one card.
- Resolver outputs distinguish "not found" from "not queried" and "ambiguous".
- Card identity follows the grammar decided in uibcdf/moli#3.
- Offline tests cover unambiguous, ambiguous and cross-source cases, including one
  protein entity with several experimental structures (e.g. human and *T. cruzi* TIM).
- If the relationship vocabulary becomes a contract consumed by Nextia or Context
  Assembly, it is raised in `uibcdf/moli` (compare uibcdf/moli#3) rather than frozen
  locally.

## Resolution

Pending.
