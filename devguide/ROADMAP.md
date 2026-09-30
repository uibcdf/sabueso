# Sabueso — Roadmap

Sabueso's work follows two routes, and this roadmap integrates both. Neither replaces the
other.

1. **The foundational plan** (2026-01 → 2026-09-23). The original design:
   - the vision, architecture and use cases;
   - a roadmap in phases (`archive/ROADMAP_original_2026-01.md`) and a source plan
     (`archive/SOURCES_original_plan.md`);
   - the long-term directions written on 2026-09-23 (`SCIENTIFIC_POTENTIAL.md`,
     `archive/future_direction_2026-09-23.md`).
2. **The pilot-driven route** (since 2026-09-23). Real discovery programs, the MOLI
   vertical pilots, pull platform development: a pilot needs something, Sabueso builds
   the smallest useful slice, and real use shows what is missing. Pilots are private.
   Their needs enter this public repository phrased generically, with public test
   systems (TcTIM and HsTIM, public data only).

The pilot route decided the *order* of the work since 2026-09-23, not its *scope*. The
objectives of the foundational plan stay objectives. This document tracks each one's
status, so that none is lost because a pilot has not asked for it yet.

## How the two routes are integrated

- **A pilot blocker comes first.** When a pilot cannot advance without Sabueso, that
  work goes first, in its smallest useful form.
- **Foundations are not postponed until they are expensive.** Some objectives get
  costlier the longer they wait: identity, references, schema, stores, query
  interfaces. They are scheduled before a pilot forces them, when the design they
  constrain is being built.
- **Every slice is built toward the foundational design.** A pilot-driven slice uses the
  general model (relationships, SourceAssertions, named derivation rules, pinned
  references), never a pilot-shaped shortcut. The pilot is its acceptance test, not its
  boundary.
- **Each release is reviewed against both routes.** Its notes and `CHECKPOINT.md` say
  what it advanced in each. When this table is out of date, updating it is part of the
  release.
- **Maintainers may schedule a foundational objective on its own.** The pilots do not
  own the plan.

## Delivered so far (0.1.0 → 0.7.0)

- **Foundations.**
  - Card, Deck, `SourceAssertionStore` and `RelationshipStore`.
  - The FieldResolver with selection rules, and the EntityResolver.
  - Mappings, conflict and knowledge-state reporting.
  - Physical quantities (PyUnitWizard) and argument contracts (ArgDigest).
  - Diagnostics (SMonitor).
- **Storage and references.**
  - Content-addressed card and deck snapshots, and pinned references.
  - The `KnowledgeStore` and the `CurationStore`.
  - Honest migration and refresh of stored cards.
- **Release route.** Staged conda releases:
  - a dependency-contract preflight;
  - inspection of the exact artifact;
  - immutable coordinates, and a recorded public poststate (#76–#78).
- **Sources in use.**
  - UniProt, RCSB PDB, PDB CCD, PDBe-KB, InterPro, AlphaFold DB.
  - ChEMBL, BindingDB, PubChem and PubChem BioAssay, UniChem.
  - STRING, IntAct (through UniProt), NCBI Taxonomy, NCBI Gene.
  - Since 0.6.0: PHI-base, DISEASES, Open Targets, Orphanet, Reactome, ClinVar, gnomAD,
    ChEMBL indications and ClinicalTrials.gov (#81–#83).
  - Since 0.7.0: SKEMPI 2.0 (#83), MONDO and MedGen (#90), Europe PMC (#92).
  - The registry, `sources/registry.yaml`, is the index.
- **Knowledge views, each with a named rule:**
  - structures and the structural inventory; predicted models;
  - oligomer and interfaces; ligand sites;
  - bioactivities, with one measurement across sources; ligands;
  - literature and claims; knowledge states;
  - card comparison; identity audit; unique names.
- **Curation.** Literature assertions, bioactivities, engagements, relationships and
  typed claims, compared with the sources, never given priority. Since 0.6.0, the
  biological context of a target (#60).
- **Since 0.6.0.**
  - Variants placed only through stated transcripts and isoform maps (#83, #85).
  - Knowledge packets, a prototype (#71).
  - Declared enrichers with shared network, release-cache and key services (#86).
- **Since 0.7.0.**
  - Diseases as entities, anchored at MONDO; a protein's diseases grouped; a
    disease's targets and drugs (#90).
  - What may be done with the knowledge, and terms profiles (#29, #94).
  - Scientific operations: expand, explain, as of (#91).
  - Molecules given as SMILES or InChI, through PubChem's stated match (#93).
  - How each statement entered, and text-mined literature mentions (#92).

## Status of the foundational plan

Status: **done**, **partial** (part delivered, the rest named), **pending**, or
**changed** (replaced by a decision, which is cited).

### Original roadmap (phases 0–5)

| Item | Status | Where / next |
|---|---|---|
| Phase 0 — conceptual schema, repository structure, devguide | done | `schemas/`, this devguide |
| Phase 1 — UniProt, RCSB, ChEMBL, PubChem connectors | done | `sabueso.tools.db.*`, `SOURCE_ACCESS.md` |
| Phase 2 — aggregator, SourceAssertionStore, conflict detection | done | `DATA_FLOW.md` |
| Phase 3 — selection engine with per-field rules | done | `RESOLVER.md`, `SELECTION_RULES_EXAMPLES.md` |
| Phase 4 — eMolecules, ChemSpider, DrugBank | pending | registry: eMolecules and ChemSpider queued; DrugBank deferred (licence) |
| Phase 4 — physchem and bioactivity fields | done | PubChem, ChEMBL physchem; three bioactivity sources (#66, #68) |
| Phase 4 — clinical layer | partial | ChEMBL max phase and indications, ClinicalTrials.gov trials by cited NCT id (#81); DrugBank deferred; ADMET and pharmacovigilance pending |
| Phase 5 — SDK entry points | done | `sabueso.resolve`, views, `PUBLIC_API.md` |
| Phase 5 — CLI | pending | no need has been stated |
| Phase 5 — Sphinx documentation | done | `docs/` |
| Phase 5 — pytest coverage, contract tests, snapshots | done | `TESTS.md`: offline suite, online tests, frozen cards, recorded card shape |

### Original vision and architecture

| Item | Status | Where / next |
|---|---|---|
| Protein cards | done | `resolve_protein_card` |
| Small-molecule cards | done | InChIKey anchor (#25) |
| Peptide cards | pending | `entity_type: peptide` exists in the schema; no peptide source or view (CPPsite queued) |
| Inputs: identifiers, names | done | UniProt, `pdb:`, `pubchem:`, `chembl:`, `pdb.ligand:`, `inchikey:`, name + organism |
| Inputs: SMILES, InChI | done | matched by PubChem, never a computed key (`pubchem_structure_lookup`, #93) |
| Inputs: sequence (FASTA), structure files | pending | resolution by sequence or structure file would need its own identity rules |
| Disease associations of a protein | done | `annotations.disease` (#39) |
| Ligands with a role (inhibitor…) | changed | a role is a derived class, never asserted (#25): `bioactivity_class@3`, `ligand_deck` |
| Deck of inhibitors of a protein | done | `ligand_deck(card)` with derived classes |
| Local cache / store | done | `KnowledgeStore` (cards); raw payloads are not stored (`CACHE_POLICY.md`) |

### Use cases (`USE_CASES.md`)

| Use case | Status |
|---|---|
| 1. Interactions, ligands, pathways of a protein | done (pathway structure from Reactome, #83) |
| 2. Clinical usage of ligands | partial (max phase and ChEMBL indications, #81; DrugBank clinical content deferred, licence) |
| 3. TopoMT: catalytic residues, mutations as structural features | partial (positional features, ligand and family sites, interface mutations from SKEMPI, #83; no TopoMT contract yet) |
| 4. PharmacophoreMT: deck of ligands | partial (ligand decks; no exchange format agreed) |
| 5. Commercial availability of peptides | pending |
| 6. Tissue-specific isoforms | partial (tissue specificity; UniProt isoforms and alternative sequences, #80; AlphaFold isoform models; isoform sequences not fetched) |
| 7. Visualization (MolSysViewer) | partial (interfaces, mutations, sites, secondary structure from UniProt and per chain from RCSB, #80; no contract) |
| 8. Clinical trials of ligands | done for the trials ChEMBL's indications cite (#81); a trial is never matched to a molecule by name |
| 9. Disease associations; targets of a disease | done on main: protein → diseases from UniProt, DISEASES, Open Targets, Orphanet and ClinVar, grouped through MONDO (#82, #90); disease → targets and → drugs as decks (#90) |
| 10. Knowledge baseline for a target and a comparator (pilot route) | done |
| 11. Curating what the literature states (pilot route) | done (human curation) |
| 12. Citing knowledge from a project (pilot route) | done, provisional reference form (#53, moli#3) |
| 13. Choosing structures to model (pilot route) | done |
| 14. A cohort of related proteins (pilot route) | done |

### Strategic directions (`SCIENTIFIC_POTENTIAL.md`, 2026-09-23)

| Direction | Status | Where / next |
|---|---|---|
| A strong SourceAssertionStore | done | MOLI-aligned fields, curated assertions, provenance |
| Cards that relate (relationships as knowledge) | done | `RelationshipStore`, typed predicates |
| More powerful decks | done | membership, derivation, pinned revisions, lineage, audits, inventory |
| Entity resolution as a central piece | done | EntityResolver, identity audit, curated names |
| Temporal knowledge | partial | snapshots, revisions, source releases; no "as of a date" query |
| Knowledge from Nextia not imported automatically | done (as a boundary) | promotion of derived knowledge open in uibcdf/moli#17 |
| Literature as a knowledge source | partial | human curation and literature views; automated extraction pending |
| KnowledgeQuery (semantic queries over sources) | partial | prototype released in 0.6.0 (#71): a protein subject, a fixed aspect mapping; contract in uibcdf/moli#22 |
| Knowledge packets (entities, facts, conflicts, unknowns) | partial | prototype released in 0.6.0 (#71): pinned, stored, with a content-equivalence id; contract in uibcdf/moli#22 |
| Unknowns as first-class output | done | `knowledge_state()` (#56) |
| Two levels of access (semantic and raw) | done | `resolve` and views; `tools.db.*.get_*` |
| Patents | pending | SureChEMBL queued |
| Proprietary / internal knowledge | pending | needs its boundary with Nextia (moli#17) and usage terms (#29) |

## Pilot-driven work

Delivered for the first pilot's knowledge baseline and structural inventory:

- organism relations and identity hygiene (#54, #55, #67, #69);
- knowledge states (#56);
- versioned decks and card comparison (#58, #59);
- predicted structures (#57) and curated engagement (#61);
- measurements across sources (#66, #68);
- migration (#51) and claims (#43);
- names, the structural inventory and its grouping (#70);
- what the first live run of the baseline found: the authors' oligomer (#72), author
  numbering (#73), partial source answers (#74), the measurement review (#75);
- the integrity of pinned item reads (#79), a case of the reference contract
  (uibcdf/moli#3).

Open, pilot-related:
- #53, the reference form (waits on uibcdf/moli#3);
- #60, biological context: step 1 (curated fields) released in 0.6.0; step 2
  (VEuPathDB) blocked on access and terms (#84);
- #30, ligand proximity to sites (deferred);
- correspondence of regions across proteins. This one belongs to MolSysMT; Sabueso takes
  its residue maps (`residue_map`, `residue_maps`).

## Next candidates

Pilot route: whatever running the pilots' notebooks exposes; nothing is scheduled ahead
of that use.

Foundational route. Reviewed on 2026-09-29 against `SCIENTIFIC_POTENTIAL.md`, the
conceptual schema and the use cases, to work beyond what the pilots have asked for.
In order:

1. **The disease as an entity (#90).** Released in 0.7.0: disease cards anchored at
   MONDO, a protein's diseases grouped through stated identity and MONDO's hierarchy,
   and a disease's targets and drugs. Open: EFO terms MONDO does not map (#96).
2. **What may be done with the knowledge (#29).** Released in 0.7.0: `Card.terms`,
   `Deck.terms`, `Deck.admissible`, depositor terms per PubChem assay, and terms
   profiles (#94). Next: terms in packets, and the shared vocabulary with MOLI.
3. **Scientific operations (#91).** Released in 0.7.0: `expand` (relationships into decks),
   `explain` (a deck member and a card's SourceAssertions), and the store's `as_of` and
   `changed_since`. Next, as use asks: explaining a view's derived items (a group, a
   state) through the same path.
4. **Literature beyond manual curation (#92).**
   - Released in 0.7.0: how each statement entered (`acquisition`: database, curation, rule
     extraction, model extraction, validation).
   - Released in 0.7.0: Europe PMC's text-mined accession mentions (`mentioned_in`). Its gene
     and protein annotations were reviewed and set aside: they ground names without
     the organism.
   - Next, when use asks: located mentions (section, sentence) of PDB ids and
     accessions, and an extraction Sabueso runs itself, with its tool and version.
5. **Continuing, in parallel when a need or a slot appears:**
   - sources of wave 2 (#83): chemistry (ChEBI done; the Chemical Probes Portal
     blocked on access), identity (Ensembl orthology; #85 closed through gnomAD's
     canonical transcript, follow-up #102), family-specific sources, patents,
     structures. iPPI-DB, VEuPathDB and TDR Targets wait on #84;
   - isoforms and variants by tissue (#102): which isoforms, and which variants,
     are tissue-specific; needs a stated source of isoform expression by tissue and
     a named rule (`RISKS_AND_OPEN_QUESTIONS.md`);
   - knowledge packets: real use decides their aspects and size (#71, #88), aligned
     with uibcdf/moli#22 once agreed;
   - the clinical layer: adverse events (openFDA), after a terms review; isoform
     sequences (#80);
   - peptide cards: scope them before any source (use case 5, CPPsite).
6. **Contracts with other MOLI components**, raised in uibcdf/moli when those
   components are ready:
   - the reference form (uibcdf/moli#3, #53) and knowledge packets (uibcdf/moli#22);
   - exchange with TopoMT (positions, interface mutations), MolSysViewer (features to
     show) and PharmacophoreMT (ligand decks). Use cases 3, 4 and 7 are partial for
     want of these.

Each is proposed as an issue before work starts, and the order is revisited at each
release.
