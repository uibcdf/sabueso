# Sabueso — Roadmap

This page owns long-term objectives, their dependency structure and the integration
of foundational and pilot-driven work. [CHECKPOINT](CHECKPOINT.md) owns current
source/qualification; the [continuation plan](CONTINUATION_PLAN_20261104.md#execution-order)
owns the active B0–B8 schedule. New contributors start with [ONBOARDING](ONBOARDING.md).
The [workstation handoff](WORKSTATION_HANDOFF_20261106.md) owns the current transfer.

## How the two routes are integrated

1. **Foundational route.** The original vision, phases, sources and use cases remain
   tracked below. Identity, support, references, schemas, persistence and query
   contracts cannot wait until a pilot forces an expensive repair.
2. **Pilot-driven route.** Real MOLI projects determine useful implementation order
   and provide acceptance tasks. Private scientific questions stay private; public
   contracts, issues and examples express generic needs with public test systems.

A pilot blocker has priority, but its smallest useful slice uses the general
knowledge model. A pilot chooses order, not the boundary of Sabueso's scientific
purpose. Each release reviews both routes. A bounded delivered feature is not proof
of complete source coverage, live health, consumer usefulness or human acceptance.

## Latest release: 0.14.0 (#134)

Published on 2026-10-09 from `78623d0`, schema 0.3.13. Exact source, staging,
installed OS/Python gates, public clean installation and Zenodo archival are in
[the immutable receipt](../devtools/conda-build/receipts/sabueso_0.14.0_public_2026-10-09.json).
That artifact remains fixed. Current development targets **0.15.0**, schema 0.3.14;
no candidate selection, freeze, staging or publication is authorized yet.

## Current consolidation after recovery (#112)

The stash recovery is historical: accepted material became maintained code,
contracts and public controls; deferred provider needs retain explicit reopening
conditions. Do not resume indiscriminate recovery or treat old prototypes as a new
architecture. The audit and accepted broad Card exploration requirements now guide
consolidation. Preserve provenance and existing meanings while completing coherent
scientific/human/agent journeys.

### Immediate resumption sequence

First verify the [handoff](WORKSTATION_HANDOFF_20261106.md) and the
[committed chemical checkpoint](evidence/chemical_saved_checkpoint_20261106.json),
then complete destination environment and exact-final-source hosted receiving.
The source machine passed 705 selected local cases and public whole-session
controls; broader scientific/human acceptance remains open. Follow the plan without
restarting completed correctness work or claiming its deferred scientific review.

| Route | Present obligation |
| --- | --- |
| B0/B1 | Preserve qualified earlier preview/conservative activity corrections and their source receipts; scientific/consumer acceptance remains separate |
| B2 | Obtain the explicitly deferred scientist review of opt-in measurement/copy-aware scope before any default adoption; original defaults/history stay fixed |
| B3 | Complete remaining structural journeys, bounded physical-scope/modeling disposition and independent receiving/acceptance |
| B4–B6 | Finish the entire required activity/literature, molecule/clinical/disease, variant/isoform/comparative/association profile inventory |
| B7 | Demonstrate complete researcher orientation, useful questions, understandable depth, continuous navigation, scoped decision assistance and reproducible work; accept scientist/agent/workload/private-consumer routes independently |
| B8 | Consolidate only after those obligations and explicit maintainer resumption; never interpret migration or a partial test pass as release authority |

The [broad exploration inventory](pending_proposals/card_exploration_completion_0150.md)
remains the panel-completeness checklist. The full human design and observed wow
experience are required **before 0.15.0**, not deferred extensions. Deck navigation,
interactive viewers/document exports and presentation videos have their separate
future proposals; they do not silently expand or replace the agreed release gate.

## Status of the foundational plan

The tables retain original goals so they are not lost when a pilot has not requested
them. Here `done` means the named bounded capability was delivered; it does not
close the broad 0.15.0 experience or external consumer contract. Source-specific
current status/terms belong to the registry and feature contracts.


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
| Inputs: sequence (FASTA), structure files | partial development | explicit `exact_sequence_candidates@1` accepts raw/FASTA, verifies full archive/current canonical sequences and retains ambiguity, caps, failures and unqueried isoforms. Automatic sequence/structure-file resolution remains pending and needs its own identity rules. |
| Disease associations of a protein | done | `annotations.disease` (#39) |
| Ligands with a role (inhibitor…) | changed | derived concentration bands use current activity @4 / explicit original @3; a band alone does not establish an inhibitor role. Stated mechanisms remain source knowledge; `ligand_deck` crosses exact supported identities |
| Deck of measured/related molecules for a protein | delivered bounded capability | `ligand_deck(card)` crosses supported identities. An inhibitor-only selection additionally needs an explicit source-qualified scientific criterion; concentration bands alone do not establish mechanism |
| Local cache / store | done | `KnowledgeStore` (cards); retrieval archive and local mirrors, opt-in (#100, `CACHE_POLICY.md`) |

### Use cases (`USE_CASES.md`)

| Use case | Status |
|---|---|
| 1. Interactions, ligands, pathways of a protein | done (pathway structure from Reactome, #83) |
| 2. Clinical usage of ligands | partial (max phase and ChEMBL indications, #81; DrugBank clinical content deferred, licence) |
| 3. TopoMT: catalytic residues, mutations as structural features | partial (positional features, ligand and family sites, interface mutations from SKEMPI, #83; no TopoMT contract yet) |
| 4. PharmacophoreMT: deck of ligands | partial (ligand decks; no exchange format agreed) |
| 5. Commercial availability of peptides | pending |
| 6. Tissue-specific isoforms | partial (tissue specificity; UniProt isoforms and alternative sequences, #80; AlphaFold isoform models; the tissues of each variant and isoform from gnomAD's pext, with GTEx's UBERON terms, #102; isoform sequences not fetched) |
| 7. Visualization (MolSysViewer) | partial (interfaces, mutations, sites, secondary structure from UniProt and per chain from RCSB, #80; no contract) |
| 8. Clinical trials of ligands | done for the trials ChEMBL's indications cite (#81); a trial is never matched to a molecule by name |
| 9. Disease associations; targets of a disease | done: protein → diseases from UniProt, DISEASES, Open Targets, Orphanet and ClinVar, grouped through MONDO (#82, #90); disease → targets and → drugs as decks (#90) |
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
| Entity resolution as a central piece | done | EntityResolver, identity audit, curated names; a reference entry related to its genome-strain entry, never merged (#103) |
| Temporal knowledge | partial | snapshots, revisions, source releases; the store's `as_of` and `changed_since` (#91); no source asked as of a past release |
| Knowledge from Nextia not imported automatically | done (as a boundary) | promotion of derived knowledge open in uibcdf/moli#17 |
| Literature as a knowledge source | partial | human curation and literature views; literal rule extraction/intake and explicit article metadata since 0.13.0 (#92); broader extraction/validation pending |
| KnowledgeQuery (semantic queries over sources) | partial | prototype released in 0.6.0 (#71): a protein subject, versioned aspect mappings (published @6 includes literature mentions/index/unknowns; current development default @16 retains separately versioned later context); contract in uibcdf/moli#22 |
| Knowledge packets (entities, facts, conflicts, unknowns) | partial | prototype released in 0.6.0 (#71): pinned, stored, with a content-equivalence id; since 0.10.0, an index level by reference for size (#88), accepted in uibcdf/moli#22, which closes with a consumer test |
| Unknowns as first-class output | done | `knowledge_state()` (#56) |
| Two levels of access (semantic and raw) | done | `resolve` and views; `tools.db.*.get_*` |
| Patents | deferred | SureChEMBL evaluated 2026-09-30: mentions cannot be restricted to claims |
| Proprietary / internal knowledge | pending | needs its boundary with Nextia (moli#17) and usage terms (#29) |

## Pilot-driven work

Private vertical pilots are read-only acceptance context. Their needs are translated
into generic source, identity, selection, support, uncertainty, cost and navigation
contracts, using public TcTIM/HsTIM/HK2 examples. Never import project conclusions
as knowledge or publish pilot hypotheses/strategies. Real consumer receiving is
owned by the consumer; a stand-in cannot close Nextia, MOLI/Recorda or modeling
contracts. See the [coordination route](CONTINUATION_PLAN_20261104.md#vertical-pilots-and-cross-component-coordination).

## Capability backlog and dependencies

| Direction | Remaining scope / owning reference |
| --- | --- |
| Rich Card knowledge access | Complete the required nature-specific inventory, human/agent/saved parity, whole-session costs and actual researcher acceptance (#148/#112) |
| KnowledgeQuery/packets and temporal knowledge | Broader semantic query coverage, source-supported historical scope and real consumer acceptance (#71/#91, MOLI shared contracts) |
| Literature and clinical knowledge | Source-qualified methods/claims/locators, rights and broader clinical/ADMET/pharmacovigilance context; preserve citation versus outcome and extraction versus reviewed curation (#92/#81) |
| Acquisition observation and bibliography (#108) | Complete remaining source/operation observation and resource/method bibliography with explicit gaps; actual MOLI/Recorda composition and consumer acceptance remain separate |
| Admissibility and terms (#29) | Historical packet-scope terms adapters, finer admissibility and the shared terms vocabulary; original support/rights must survive filtering and consumer exchange |
| Sources and mirrors | Registry-owned evaluations/deferred triggers, explicit terms/access and current source health; postponed mirrors and unlicensed inputs are not implied new work (#83/#95/#101) |
| Peptides | Define the scientific/identity/source scope before a source implementation; schema enumeration alone is not delivered peptide science |
| Interoperability | Actual model/annotation/ligand-deck receiving by MolSysSuite consumers; source knowledge, calculated geometry, Nextia Evidence and provenance retain distinct ownership |
| Future exploration products | Deck navigation, export/interactive visual inspection and assisted video presentation remain separately scheduled proposals; reuse Card semantics and keep publication authority explicit |

The [earlier detailed backlog](archive/ROADMAP_before_onboarding_20261106.md#capability-backlog-and-dependencies)
preserves every previous capability/owner reference and dated progress record.
Use current contracts/registry/continuation to determine the next action; do not
reimplement an item solely because an older paragraph said it was pending.

<a id="next-roadmap-after-0130"></a>

## Historical roadmap context

Older links to the post-0.13.0 roadmap land here. That order is historical;
use the [immediate resumption sequence](#immediate-resumption-sequence) and
integrated continuation plan for today's work.

The [full previous roadmap](archive/ROADMAP_before_onboarding_20261106.md) preserves
release histories, feature-by-feature receipts, the old post-0.13.0 order and its
later continuations. [Original phase plan](archive/ROADMAP_original_2026-01.md),
[source plan](archive/SOURCES_original_plan.md), [DECISIONS](DECISIONS.md) and the
[audit](GLOBAL_AUDIT_20261104.md) explain how objectives evolved. Their dated next
steps are historical; the integrated continuation plan is the current schedule.
