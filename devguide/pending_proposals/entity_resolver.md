---
summary: Resolve source subjects to Sabueso entities (EntityResolver), with a minimal traceable Relationship model, and derive card identity from entities.
issue: uibcdf/sabueso#6
status: active
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

## Contract (agreed 2026-09-23)

The Sabueso owner reviewed and agreed this contract on 2026-09-23 (see *Decisions* below).
Names are provisional, and the identifier grammar follows uibcdf/moli#3 once decided.

### MVP scope

- **Entity type with Cards:** `protein`.
  - Experimental structures are **structure records** (`pdb:<id>`). They are relationship
    targets and subjects of their own SourceAssertions, shown inside the ProteinCard.
    There is no StructureCard in the MVP (#20).
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
  - **Anchor rule:** use the reviewed (Swiss-Prot) canonical entry when one exists.
    Otherwise use the entry selected by the explicit, recorded preference mechanism
    (rule 5), for example the reference-proteome entry, and keep the alternatives.
  - **Anchor changes** never rewrite identity silently. If UniProt merges or demerges the
    entry, or a reviewed entry appears later, the old anchor gets a `superseded_by`
    relationship and the history stays inspectable.
  - **Consumers treat the reference as opaque**, even though it currently embeds the
    accession. A later move to a Sabueso-native identifier must not break them.
- **Structure record:** a PDB entry, referenced as `pdb:<id>`. It is not a separate Card
  in the MVP.
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
  alternatives   when resolved by a preference policy: the non-preferred candidates with
                 their basis (reviewed status, length, checksum, organism)
  policy         the preference policy applied, named and versioned (e.g. prefer_reviewed@1)
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
   - several matches: resolved only when an explicit, versioned **preference policy**
     (default `prefer_reviewed@1`) selects exactly one candidate. The non-preferred
     candidates are kept as `alternatives`, with their basis, and stored with the Card
     (`quality.entity_resolution`). They never feed Card fields;
   - no policy selects exactly one candidate (e.g. two reviewed entries): `ambiguous`;
   - preferences never choose across organisms.
6. **Name without organism:** `unsupported` in the MVP. It is too broad to resolve
   responsibly.
7. **Identical sequence (checksum):**
   - within the same organism: at most a derived `possibly_same_as`, never an automatic
     merge;
   - across organisms: no identity link at all.
8. **PDB ID:** resolved to the structure record `pdb:<id>`, together with the protein
   entities its polymer entities map to through `has_structure`. Structure facts are
   never merged into protein fields.

### Relationships in the MVP

- **Predicates:** `same_as`, `possibly_same_as`, `isoform_of`, `has_structure`.
  `member_of_family` and `interacts_with` come later, including the migration of the
  STRING/BioGRID partner lists.
- **Mandatory `has_structure` qualifiers** (raw facts), with object `pdb:<id>`:
  - PDB id, chains and polymer entity;
  - residue range in UniProt numbering;
  - **coverage**, the fraction of the canonical length covered;
  - experimental method and resolution;
  - the **other polymer entities present** in the structure, which reveals complexes
    such as 1KLG.
- **Derived classification:** `full_length | domain | fragment_or_peptide`, recorded as
  derived knowledge with its derivation (rule and thresholds). It is not a separate
  predicate and not a SourceAssertion. Default views exclude fragments, say so, and let
  the user change that.
- **Asserted support:** each source that states the link contributes a SourceAssertion,
  for example the UniProt PDB cross-reference and the RCSB entity mapping. Agreement
  between sources stays visible.
- **Derived support:** derived links carry a derivation record.
- **Identity:** each Relationship has a deterministic id, a hash of subject, predicate,
  object and key qualifiers. The same relationship is then recognisable wherever it
  appears.
- **Storage:** a RelationshipStore serialized with the subject Card only, like the
  SourceAssertionStore. Inverse navigation uses Deck-level indexing. The decision is to be
  re-evaluated in #19.

### Structures inside the ProteinCard

- The ProteinCard exposes a `structures` section. It is a view built from its
  `has_structure` Relationships, with one summary per structure: PDB id, method,
  resolution, chains, coverage, derived classification and ligands present.
- Structure-level facts are SourceAssertions with `subject_ref = pdb:<id>`. They are
  displayed through the view but never merged into protein fields.
- The scalar `structure.entry_metadata.*` fields of the protein card, which today can read
  as "the resolution of the protein", are replaced by this view.
- The decision to have no StructureCard is to be re-evaluated in #20.

### Interaction with the FieldResolver

- Only SourceAssertions whose `subject_ref` belongs to the entity feed that entity's card
  fields. That means the anchor plus its `same_as` links.
- `possibly_same_as` records never feed fields automatically.
- Assertions about a structure keep the structure record (`pdb:<id>`) as subject, or stay on its relationships.

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
| A6 | name "triosephosphate isomerase" + organism 9606 | 19 UniProt matches (1 reviewed): resolved to P60174 by `prefer_reviewed@1`, with the 18 non-preferred matches recorded as `alternatives` |
| A7 | same name + organism 5693, exact taxon | resolved `P52270` (single UniProt match at species level) |
| A7b | same name + *T. cruzi* including strains (taxonomy subtree) | 2 matches: P52270 (reviewed) and Q4DV43 (unreviewed, strain CL Brener, same length, 4 substitutions: S90K, S161A, R162H, T201A). Resolved to P52270 by preference, with Q4DV43 recorded as an alternative. No `possibly_same_as`, because the sequences differ |
| A8 | same name, no organism | `unsupported` (29,577 matches across UniProt) |
| A9 | `P60174` structures | 29 `has_structure` links (all X-ray). 1HTI chains A/B 2–249 (coverage ≈ 1.0). 1KLG and 1KLU chain C 23–37 are a 15-residue TIM peptide in an HLA-DR1 complex (coverage ≈ 0.06) and must not appear as full-length TIM structures |
| A10 | `P52270` structures | 7 `has_structure` links, e.g. 1TCD chains A/B 3–251; RCSB polymer entity 1TCD/1 maps to P52270, so the link has two agreeing SourceAssertions |
| A11 | `pdb:1TCD` | resolved structure record `pdb:1TCD`, related to `sabueso:protein:uniprot:P52270` |
| A12 | nonexistent accession / unreachable source | `not_found` vs `error`, never collapsed |

Fixtures to add at implementation time:
- UniProt entries P60175, V9HWK1 and Q4DV43, and the inactive record P00938;
- UniProt search results for the name + organism queries;
- RCSB polymer entities for 1HTI, 1KLG and 1TCD.

### Decisions (2026-09-23)

1. **Anchor.** Option A, the UniProt anchor record, with an explicit anchor rule,
   `superseded_by` history and opaque references. Rejected alternatives:
   - a Sabueso-native opaque id, which needs a persistent shared registry, premature for
     a local-first MVP;
   - content identity (organism + sequence checksum), which breaks on sequence
     corrections, isoforms and variants.
2. **Preference with trace.** Ambiguity may be resolved only by a named, versioned policy.
   The non-preferred candidates are kept as `alternatives` on the Card and never feed
   fields.
3. **Fragments.** A single `has_structure` predicate with mandatory raw qualifiers,
   including the other entities present, plus a derived classification with visible
   thresholds.
4. **Relationship storage.** With the subject Card, with deterministic relationship ids.
   Re-evaluation tracked in #19.
5. **Structures.** Managed inside the ProteinCard as a `structures` view, with structure
   facts kept on their own subject (`pdb:<id>`). No StructureCard for now. Re-evaluation
   tracked in #20. The reasons for avoiding a StructureCard now:
   - a Deck mixing protein and structure cards would be confusing;
   - a card type per source database (PDB, …) would blur the rule that Cards describe
     scientific entities, not database outputs.

### Known future risks

- **Anchor churn.** UniProt merges, demerges (P00938) and new reviewed entries will
  change anchors. `superseded_by` must be implemented before any consumer persists
  references, together with the grammar of uibcdf/moli#3.
- **Proteins without reviewed entries.** This is common in non-model organisms and
  strains. The preference may then choose among close variants: for *T. cruzi*, strain
  CL Brener Q4DV43 differs from P52270 at 4 positions. Views must surface the
  `alternatives`, because variant differences can matter scientifically.
- **Default preference hides options.** A default `prefer_reviewed@1` is convenient but
  can bury relevant alternatives. They must stay visible in the Card and in any summary.
- **Arbitrary thresholds.** The fragment/domain/full-length thresholds are arbitrary.
  They are recorded as derivation parameters and must be revisited with real use.
- **Card-attached relationships** may scale badly for interaction networks and dense
  bioactivity data (#19).
- **Protein-centric structures** duplicate complexes across protein cards, and may need a
  structure-level entity later (#20).

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
- Preference-based resolutions keep their `alternatives` and `policy` on the Card.
- The ProteinCard has no scalar structure fields. Structures appear through the
  `structures` view, and their facts keep `pdb:<id>` as subject.
- Card identity follows the grammar decided in uibcdf/moli#3.
- Offline tests cover unambiguous, ambiguous and cross-source cases, including one
  protein entity with several experimental structures (e.g. human and *T. cruzi* TIM).
- If the relationship vocabulary becomes a contract consumed by Nextia or Context
  Assembly, it is raised in `uibcdf/moli` (compare uibcdf/moli#3) rather than frozen
  locally.

## Implementation progress

1. **Relationship model and RelationshipStore** (`fcbd22e`, 2026-09-23). Done:
   - deterministic ids, predicate vocabulary, and asserted or derived support;
   - merged support, with `qualifier_conflicts` when sources disagree;
   - card serialization and the `Card.relationships()` accessor;
   - rejection of relationships that cite missing SourceAssertions.
   Tests: `tests/core/test_relationships_offline.py`.
2. **EntityResolver for UniProt accessions** (A1–A5, A12). Done:
   - `sabueso/resolver/entity_resolver.py` and `uniprot_client.py` (online and fixture
     clients);
   - active, merged, demerged and isoform accessions;
   - organism filtering with recorded alternatives, `not_found / unsupported / error`
     kept apart, and derived `sequence_identity_link`.

   Tests: `tests/core/test_entity_resolver_offline.py`, plus an online check in
   `test_online_entity_resolver.py`.

   Observed UniProt REST behaviour (2026-09-23):
   - a merged secondary accession (Q6FHP9) answers HTTP 303 with an inactive `MERGED`
     body. HTTP clients that follow the redirect receive the active entry instead.
     Both paths resolve to the same entity with a `same_as` link, and only the recorded
     rule differs;
   - a demerged accession (P00938) answers 200 with an inactive `DEMERGED` body;
   - an isoform accession has its own record, but resolution uses the canonical entry's
     ALTERNATIVE PRODUCTS listing;
   - an invalid format answers 400. It is rejected locally as `unsupported` before any
     query;
   - a well-formed but unknown accession answers 404 (`not_found`).

   Implementation choices:
   - a demerged accession relates to each successor through `superseded_by`, not
     `same_as`, because the old record covered several proteins;
   - an identifier that contradicts the requested organism does not resolve
     (`not_found`, rule `organism_mismatch`).

   Still pending from A5: V9HWK1 assertions must not feed the P60174 card. This is
   enforced when cards are built from resolved entities, in step 4.
3. **Name + organism with preference and trace** (A6, A7, A7b). Done:
   - `EntityQuery(name, organism, include_subtaxa)`;
   - the UniProt search is captured in the decision (query, total, UniProt release,
     retrieval time);
   - `prefer_reviewed@1` resolves only when exactly one reviewed match exists. All
     other matches are kept as `alternatives`, and identical-sequence alternatives in
     the same organism are surfaced as derived `possibly_same_as` links (V9HWK1 for
     human TIM);
   - `policy=None` keeps several matches `ambiguous`;
   - a truncated search never resolves;
   - a name without an organism is `unsupported`.

   Clarification: with `include_subtaxa`, strain entries below the queried species (e.g.
   Q4DV43, *T. cruzi* CL Brener) are within the requested organism scope, so the
   preference may choose among them. The "never across organisms" rule forbids choosing
   between organisms the query did not ask for, for example human vs chimpanzee.

   Deferred: the contract says ambiguous candidates are "also returned as an ambiguity
   Deck". They are returned as a list for now. Materializing them as a Deck of Cards
   needs card building from resolved entities (step 4).
4. **`has_structure` and the ProteinCard `structures` view** (A9–A11), in three parts.
   - **4a. UniProt side.** Done:
     - PDB cross-references become `has_structure` relationships backed by UniProt
       SourceAssertions (the raw `Chains`/`Method`/`Resolution` as stated), with
       normalized chains, ranges and coverage;
     - `Card.structures(include_fragments=False)` returns the view, lists excluded
       fragments, and carries the derived-classification record. HsTIM gives 24 items,
       with its 5 peptide complexes excluded. TcTIM 3Q37, a loop-deletion construct,
       comes out `partial` (0.805);
     - tests: `tests/core/test_structures_offline.py`.

     Two deviations from the agreed contract, found while implementing:
     - **Class names:** `full_length | partial | fragment_or_peptide` instead of
       `… domain …`, because a domain cannot be told from coverage alone.
     - **`has_structure` identity:** it no longer includes `polymer_entity`. UniProt
       cross-references do not name polymer entities, so UniProt and RCSB could never
       agree on the same relationship. The (protein, structure) pair is the identity,
       and polymer entities are qualifiers.
   - **4b. RCSB entity mapping**. Done:
     - `resolver/rcsb_client.py` (one GraphQL request per entry, online and fixture);
     - `mappings/rcsb_structures.py`: `has_structure` per aligned UniProt accession,
       restricted to the card's subjects, with polymer entities, other entities and
       ligands. Coverage is computed from reference lengths, and methods are normalized
       to UniProt's vocabulary;
     - `pdb:<id>` resolves to the structure record with `related` proteins.

     Results:
     - UniProt and RCSB agree on 1HTI, 1KLG and 1TCD, with two sources and no
       conflicts;
     - 1KLG is an HLA-DR α/β complex with staphylococcal enterotoxin C3 and the TIM
       peptide 23–37;
     - 1HTI carries PGA (2-phosphoglycolate);
     - a forced range disagreement shows up in `qualifier_conflicts`.

     Tests: `test_structures_offline.py` and `test_entity_resolver_offline.py`
     (A9–A11).
   - **4c. Cards built from resolved entities**. Done:
     - `build_card_from_mapping(..., entity_subjects=...)` raises `SchemaError` if an
       assertion about another subject would feed a field. This is the A5 boundary:
       V9HWK1 assertions can never feed the P60174 card;
     - `resolve_protein_card(query, resolver, structures)`: fields come only from the
       anchor record (plus `same_as` records). Identity links are relationships,
       structures are relationships shown through the view (no scalar structure fields),
       and the trace lives in `quality.entity_resolution`;
     - `ambiguity_deck(resolution)` materializes the deferred ambiguity Deck from what
       the resolver already reported. For P00938 that is a human and a chimpanzee
       candidate card;
     - tests: `tests/core/test_protein_cards_offline.py`.

     Known future risks, recorded per the devguide rule:
     - **Extra requests.** `resolve_protein_card` fetches the anchor entry again after
       resolution. Online, `structures="all"` means one RCSB request per structure (29
       for human TIM). Consider caching once real workloads show the cost.
     - **Legacy paths.** They still merge or mistype entities: PDB-entry cards typed as
       protein with scalar `structure.entry_metadata.*`; annotation-only cards typed as
       protein; unguarded multi-source merges. Tracked in uibcdf/sabueso#21, which asks
       for a decision on the public `create_structure_card_*`.

   Acceptance criteria not yet met, and where they are tracked:
   - annotation-only sources are still typed as proteins, and the cross-source
     end-to-end case still merges (uibcdf/sabueso#21);
   - card identity grammar is pending uibcdf/moli#3.

## Resolution

Pending.
