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

## Delivered so far (0.1.0 → 0.4.0)

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
- **Sources in use.**
  - UniProt, RCSB PDB, PDB CCD, PDBe-KB, InterPro, AlphaFold DB.
  - ChEMBL, BindingDB, PubChem and PubChem BioAssay, UniChem.
  - STRING, IntAct (through UniProt), NCBI Taxonomy, NCBI Gene.
  - The registry, `sources/registry.yaml`, is the index.
- **Knowledge views, each with a named rule:**
  - structures and the structural inventory; predicted models;
  - oligomer and interfaces; ligand sites;
  - bioactivities, with one measurement across sources; ligands;
  - literature and claims; knowledge states;
  - card comparison; identity audit; unique names.
- **Curation.** Literature assertions, bioactivities, engagements, relationships and
  typed claims, compared with the sources, never given priority.

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
| Phase 4 — clinical layer | partial | ChEMBL `clinical.max_phase` only; ClinicalTrials.gov queued, DrugBank deferred |
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
| Inputs: sequence (FASTA), SMILES/InChI, structure files | pending | resolution by sequence or structure would need its own identity rules |
| Disease associations of a protein | done | `annotations.disease` (#39) |
| Ligands with a role (inhibitor…) | changed | a role is a derived class, never asserted (#25): `bioactivity_class@3`, `ligand_deck` |
| Deck of inhibitors of a protein | done | `ligand_deck(card)` with derived classes |
| Local cache / store | done | `KnowledgeStore` (cards); raw payloads are not stored (`CACHE_POLICY.md`) |

### Use cases (`USE_CASES.md`)

| Use case | Status |
|---|---|
| 1. Interactions, ligands, pathways of a protein | done (Reactome queued for pathway structure) |
| 2. Clinical usage of ligands | partial (max phase only) |
| 3. TopoMT: catalytic residues, mutations as structural features | partial (positional features, ligand and family sites; no TopoMT contract yet) |
| 4. PharmacophoreMT: deck of ligands | partial (ligand decks; no exchange format agreed) |
| 5. Commercial availability of peptides | pending |
| 6. Tissue-specific isoforms | partial (tissue specificity; UniProt isoforms not mapped; AlphaFold isoform models) |
| 7. Visualization (MolSysViewer) | partial (interfaces, mutations, sites; secondary structure not mapped; no contract) |
| 8. Clinical trials of ligands | pending |
| 9. Disease associations; targets of a disease | partial (protein → disease; disease → targets needs a source, e.g. Open Targets, queued) |
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
| KnowledgeQuery (semantic queries over sources) | pending | proposed in #71; contract in uibcdf/moli#22 |
| Knowledge packets (entities, facts, conflicts, unknowns) | pending | proposed in #71; contract in uibcdf/moli#22 |
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
- names, the structural inventory and its grouping (#70).

Open, pilot-related:
- #53, the reference form (waits on uibcdf/moli#3);
- #60, biological context (deferred);
- #30, ligand proximity to sites (deferred);
- correspondence of regions across proteins. This one belongs to MolSysMT; Sabueso takes
  its residue maps (`residue_map`, `residue_maps`).

## Next candidates

Pilot route: whatever running the first pilot's notebooks exposes; nothing is scheduled
ahead of that use.

Foundational route, in the order proposed now:

1. **Knowledge packets and KnowledgeQuery (design first; #71, uibcdf/moli#22).** Most of their parts exist.
   Designing the interface now keeps later views from growing apart. It also answers the
   MOLI Agent's need for one call that returns entities, facts, conflicts and unknowns.
2. **UniProt isoforms and secondary structure.** They are small mappings that complete
   use cases 6 and 7.
3. **Clinical layer.** Evaluate ClinicalTrials.gov (queued), and DrugBank's terms, for
   use cases 2 and 8.
4. **Disease → targets.** Evaluate Open Targets (queued) for use case 9.
5. **Peptide cards.** Scope them before any source (use case 5, CPPsite).

Each is proposed as an issue before work starts, and the order is revisited at each
release.
