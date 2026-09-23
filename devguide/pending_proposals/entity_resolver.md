---
summary: Resolve source subjects to Sabueso entities (EntityResolver), with a minimal traceable Relationship model, and derive card identity from entities.
issue: uibcdf/sabueso#6
status: open
opened: 2026-09-23
closed:
verification: measured
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

## Draft contract (for review, 2026-09-23)

This is a proposal to review before any implementation. Names are provisional, and the
identifier grammar follows uibcdf/moli#3 once decided.

### MVP scope

- **Entity types:** `protein` and `structure`.
  - Small molecules come later.
  - Annotation concepts (GO terms, InterPro/CATH/SCOPe/TED classifications) stay as
    source-record references. They are not entities yet.
- **Inputs:**
  - UniProt accessions: primary, secondary/inactive, and isoform (`P60174-3`);
  - PDB IDs;
  - protein name plus organism.

  Sequence, SMILES and InChI inputs come later.

### Entities

- **Protein entity:** anchored on one explicitly chosen UniProtKB entry (the *anchor
  record*), with the reference `sabueso:protein:uniprot:<accession>`. This keeps the
  current `card_id` form, but its meaning becomes "the entity anchored on this record".
- **Structure entity:** anchored on a PDB entry, `sabueso:structure:pdb:<id>`.
- **Isoforms** are not separate entities in the MVP. An isoform accession resolves to the
  protein entity plus an `isoform` qualifier, through an `isoform_of` relationship.

### Interface

```text
resolve_entity(query: EntityQuery) -> EntityResolution

EntityQuery
  identifier     e.g. "P60174", "uniprot:P00938", "P60174-3", "pdb:1TCD"
  name           e.g. "triosephosphate isomerase"
  organism       NCBI taxon id or scientific name
  entity_type    "protein" | "structure" (optional hint)

EntityResolution
  status         resolved | ambiguous | not_found | unsupported | error
  entity_ref     when resolved
  qualifiers     e.g. {"isoform": "P60174-3"}
  candidates     when ambiguous: [{entity_ref, basis}], also returned as an ambiguity Deck
  identity_links Relationships used or proposed (same_as, possibly_same_as, isoform_of)
  decision       derivation record: rule(s) applied, inputs, sources consulted with
                 retrieval time/version, Sabueso version, explicit policies
```

The statuses keep absence apart:
- `not_found`: the sources were consulted and nothing matched.
- `unsupported`: this input type is not handled, so nothing was queried.
- `error`: a source failed, which is not the same as not found.

### Resolution rules (MVP)

1. **Active primary accession:** resolved.
2. **Secondary accession** listed by exactly one active entry, and not demerged:
   resolved, with a `same_as` link asserted by UniProt.
3. **Inactive or demerged accession:** `ambiguous`, never a silent choice.
   - Every target becomes a candidate.
   - An organism in the query may disambiguate, and the decision is recorded.
4. **Isoform accession:** resolved to the protein entity with an `isoform` qualifier.
5. **Name plus organism:**
   - every match is a candidate, annotated with reviewed status, length and sequence
     checksum;
   - exactly one match: resolved;
   - several matches: `ambiguous`;
   - an explicit policy (e.g. `prefer_reviewed=True`) may resolve the query, and the
     policy is recorded in `decision`. Never implicitly.
6. **Name without organism:** `unsupported` in the MVP. It is too broad to resolve
   responsibly.
7. **Identical sequence (checksum):**
   - within the same organism: at most a derived `possibly_same_as`, never an automatic
     merge;
   - across organisms: no identity link at all.
8. **PDB ID:** resolved to a structure entity. Its polymer entities relate to protein
   entities through `has_structure`. They are never merged into the protein card.

### Relationships in the MVP

- **Predicates:** `same_as`, `possibly_same_as`, `isoform_of`, `has_structure`.
  `member_of_family` and `interacts_with` come later, including the migration of the
  STRING/BioGRID partner lists.
- **Mandatory `has_structure` qualifiers:**
  - PDB id, chains and polymer entity;
  - residue range in UniProt numbering;
  - **coverage**, the fraction of the canonical length covered;
  - experimental method and resolution.

  Consumers can then tell full-length structures from fragments.
- **Asserted support:** each source that states the link contributes a SourceAssertion,
  for example the UniProt PDB cross-reference and the RCSB entity mapping. Agreement
  between sources stays visible.
- **Derived support:** derived links carry a derivation record.
- **Storage:** a RelationshipStore serialized with the subject card, like the
  SourceAssertionStore. A shared or global store is a later decision.

### Interaction with the FieldResolver

- Only SourceAssertions whose `subject_ref` belongs to the entity feed that entity's card
  fields. That means the anchor plus its `same_as` links.
- `possibly_same_as` records never feed fields automatically.
- Assertions about a structure stay on the structure entity or its relationships.

### Acceptance cases (public data, measured 2026-09-23)

UniProt and RCSB content changes over time, so tests use frozen fixtures, not live
counts.

| # | Input / case | Expected |
|---|---|---|
| A1 | `P60174` | resolved `sabueso:protein:uniprot:P60174` (human TIM) |
| A2 | `P60174-3` | resolved to A1 with `isoform` qualifier (P60174 lists isoforms -1, -3, -4) |
| A3 | `P00938` (secondary accession of P60174) | UniProt reports it `Inactive`, `DEMERGED` into P60174 (*H. sapiens*) and P60175 (*P. troglodytes*): `ambiguous` with two candidates; with organism 9606 → resolved, decision recorded |
| A4 | P60174 vs P60175 | identical sequence (same MD5) in different organisms: **no** identity link |
| A5 | P60174 vs V9HWK1 (unreviewed, human, identical sequence) | derived `possibly_same_as`; V9HWK1 assertions do not feed the P60174 card |
| A6 | name "triosephosphate isomerase" + organism 9606 | `ambiguous`: 19 UniProt matches (1 reviewed); resolved to P60174 only under an explicit `prefer_reviewed` policy, recorded |
| A7 | same name + organism 5693 (*T. cruzi*) | resolved `P52270` (single UniProt match) |
| A8 | same name, no organism | `unsupported` (29,577 matches across UniProt) |
| A9 | `P60174` structures | 29 `has_structure` links (all X-ray). 1HTI chains A/B 2–249 (coverage ≈ 1.0). 1KLG and 1KLU chain C 23–37 are a 15-residue TIM peptide in an HLA-DR1 complex (coverage ≈ 0.06) and must not appear as full-length TIM structures |
| A10 | `P52270` structures | 7 `has_structure` links, e.g. 1TCD chains A/B 3–251; RCSB polymer entity 1TCD/1 maps to P52270, so the link has two agreeing SourceAssertions |
| A11 | `pdb:1TCD` | resolved structure entity, related to `sabueso:protein:uniprot:P52270` |
| A12 | nonexistent accession / unreachable source | `not_found` vs `error`, never collapsed |

Fixtures to add at implementation time:
- UniProt entries P60175 and V9HWK1, and the inactive record P00938;
- UniProt search results for the name + organism queries;
- RCSB polymer entities for 1HTI, 1KLG and 1TCD.

### Open questions for review

1. **Anchor rule.** Should a protein entity anchor on the reviewed canonical UniProt entry
   when one exists? What anchors proteins that only have unreviewed entries?
2. **Default policy.** Should name plus organism with several matches stay `ambiguous` by
   default, or should `prefer_reviewed` be the default?
3. **Fragments.** Should they use one `has_structure` predicate with a mandatory coverage
   qualifier, as proposed, or a separate predicate?
4. **Relationship storage.** Card-attached for the MVP, as proposed, or a shared store
   from the start?
5. **Structures.** Are they full entities with their own cards in the MVP, or only
   relationship targets at first?

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
