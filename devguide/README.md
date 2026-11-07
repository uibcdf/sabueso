# Sabueso — Developer Guide

Sabueso is MOLI's molecular Knowledge component. It builds traceable Cards and
Decks from what scientific sources state and lets researchers and agents explore
that knowledge. **Sabueso knows; it does not discover.** Source assertions,
scientific interpretation, runtime provenance and project Evidence stay distinct.

## Where to start

If you are joining the project, read [ONBOARDING](ONBOARDING.md). It explains the
purpose, architecture, development history, working practices and a first offline
task. If you are transferring the existing workspace, also follow the
[workstation handoff](WORKSTATION_HANDOFF_20261106.md) before installing or updating
anything: the remote repository does not contain the whole local state.

| Your question | Authoritative starting point |
| --- | --- |
| What does Sabueso do, and why? | [VISION](VISION.md), [ARCHITECTURE](ARCHITECTURE.md), [DATA_FLOW](DATA_FLOW.md), [GLOSSARY](GLOSSARY.md) |
| What is published, what is local, and what is next? | [CHECKPOINT](CHECKPOINT.md) |
| In what order do we work? | [Current destination actions](CONTINUATION_PLAN_20261104.md#destination-review-and-next-actions) and [integrated B0–B8 plan](CONTINUATION_PLAN_20261104.md#execution-order) |
| What must the complete Card experience deliver? | [Broad exploration inventory](pending_proposals/card_exploration_completion_0150.md) and [observable wow criteria](CONTINUATION_PLAN_20261104.md#required-wow-experience-in-0150) |
| What are the long-term goals and dependencies? | [Accepted six-stage program](ROADMAP.md#accepted-long-term-execution-stages) and [its execution](CONTINUATION_PLAN_20261104.md#accepted-six-stage-program) |
| What decisions explain the design? | [DECISIONS](DECISIONS.md), the owning issue and its feature analysis; use the [onboarding history map](ONBOARDING.md#how-the-project-reached-this-point) rather than reading the full log sequentially |
| How do I change and verify something? | [Root instructions](../AGENTS.md), [API conventions](API_CONVENTIONS.md), [TESTS](TESTS.md) |
| How do I resume on another machine without losing work? | [Handoff](WORKSTATION_HANDOFF_20261106.md), its manifest and the current checkpoint |

## Current development boundary

The latest published package is **0.14.0**. Work targets **0.15.0**, including the
entire agreed human/agent Card exploration design and observed researcher
acceptance. Completing one adapter or passing technical tests does not meet that
release gate. Candidate selection, schema freezing, staging and publication remain
paused; this documentation update does not authorize them.

The maintainer has resumed the entire [six-stage program](ROADMAP.md#accepted-long-term-execution-stages).
Complete the rich 0.15.0 profiles, obtain B7 acceptance and authorized B8 delivery,
then expand semantic/temporal access, real interoperability, scientific/source
coverage and separately scoped exploration products. The future products do not
enlarge 0.15.0. Independent authorized work continues while a reviewer or remote
runner is unavailable; dependent acceptance and exact-candidate qualification
remain open. B2 scientific/default review remains explicitly deferred.

Destination restoration and earlier corrected-source receipts retain their
[recorded scope](WORKSTATION_HANDOFF_20261106.md). Exact current state belongs
to [CHECKPOINT](CHECKPOINT.md); execution budgets belong to the
[current workstation profile](TESTS.md#current-workstation-profile). The
[current action plan](CONTINUATION_PLAN_20261104.md#destination-review-and-next-actions)
uses applicable local checks and authorized CI batching. Historical green
receipts do not qualify a changed working tree or later candidate artifacts.

The [live protein activity journey](pending_proposals/card_bioactivity_exploration.md)
connects molecules, native groups, original activity records and exact retained
assay/citation/publication support. Its separately versioned original saved reader
passes its selected 1,109-case local checkpoint, committed at `276160a`, after a clean SDK200 live capture;
the [saved receipt](evidence/bioactivity_saved_checkpoint_20261106.json) owns the
scope and limits. The broader B4 and human/scientific acceptance remain open.

The next [molecule-to-supplied-target activity journey](pending_proposals/card_molecule_activity_exploration.md)
has a selected LIVE checkpoint: explicit source identity joins retain exact
target captures, native measurements and full source/publication navigation. Its
earlier 45-case owning and adjacent/historical/copied gates total
[1,133 distinct local passes](evidence/molecule_activity_live_checkpoint_20261107.json).
The [identity-membership correction](evidence/molecule_activity_identity_checkpoint_20261107.json)
adds six controls and passes the complete 51-case cohort plus affected shared,
native/profile and copied gates: 726 distinct cases with their own source binding.
The clean corrected producer is `ddc1fc8` / SDK205; its
[complete genuine original](evidence/molecule_activity_live_original_20261107.json)
preserves 29 scenarios, 1,337 human views and 288 machine requests with all 311 pages before
independent saved reading. Saving awaits that independent reader. The checkpoint
distinguishes this unfinished profile from full-source, installed and human
qualification.

The independent molecule-activity predicate foundation now passes its
[87-case selected checkpoint](evidence/molecule_activity_frozen_checkpoint_20261107.json):
99 original scientific wires, 26 native crossings and all 288 machine requests/cells
across 311 pages. It keeps current Cards/readers/clients out of verification.
Explicit saved admission, human/source/origin replay, transport and copied
receiving remain open; this private foundation does not enable public saving.

Cross-focal receiving also exposed a [native crossing cache defect](pending_bugs/molecule_activity_cross_focal_cache.md):
after explicit molecule → target → molecule navigation, a shared cache could
return the previous molecule's crossing. The correction scopes that cache to
the exact focal capture, including distinct snapshots with the same Card ID.
Its [765-case selected checkpoint](evidence/molecule_activity_cross_focal_checkpoint_20261107.json)
passes LIVE, private original, affected shared/native/profile and copied gates.
The clean corrected `142618d` / SDK208 producer now supplies a
[genuine supplemental original](evidence/molecule_activity_multifocal_original_20261107.json):
three multi-focal routes with 176 human views and 24 machine requests/pages,
complete source/publication contexts and both exact molecule pins. The SDK205
original stays byte-identical. Resume full independently versioned saved admission
and original human/source/origin replay next.

The [shared literature catalog](pending_proposals/card_literature_exploration.md)
has its B4 LIVE producer committed: four new modules and their dispatch wiring
across Card natures pass the selected
[1,202-case local checkpoint](evidence/literature_live_checkpoint_20261107.json).
The clean producer is committed as `1145ea3` / SDK202 and its
[genuine original](evidence/literature_live_original_20261107.json) was captured
and independently hash-verified before reader implementation. Independent saved
reading passes the [9,466-case full local checkpoint](evidence/literature_saved_checkpoint_20261107.json)
and copied receiving. New @19/@20 saves also bind SDK202 activity bibliography;
older formats and their resaves stay fixed. Hosted/artifact/human acceptance
remains separate; continue molecule-target/context and the broader profiles.

## Design

| Document | Role |
| --- | --- |
| [VISION](VISION.md), [USE_CASES](USE_CASES.md) | Purpose, intended users and scientific uses |
| [ARCHITECTURE](ARCHITECTURE.md), [DATA_FLOW](DATA_FLOW.md), [GLOSSARY](GLOSSARY.md) | Responsibilities, objects, information flow and terminology |
| [SCIENTIFIC_POTENTIAL](SCIENTIFIC_POTENTIAL.md), [FUTURE_EXPANSIONS](FUTURE_EXPANSIONS.md) | Long-term directions; they are not automatic release commitments |
| [Human exploration plan](pending_proposals/card_human_exploration_api.md) and [nature-specific detailed design](pending_proposals/card_exploration_detailed_design.md) | Accepted interaction design; original staged sequences are read through the current completion inventory |
| [Agent access contract](pending_proposals/card_agent_access_v1_contract.md) | Compact structured access with full scientific support and explicit budgets |
| [Shared publication exploration](pending_proposals/card_literature_exploration.md) | Current B4 literature increment, original support/navigation and the clean-capture boundary before saved reading |
| [Global audit](GLOBAL_AUDIT_20261104.md) | Dated engineering/scientific findings, limitations and acceptance evidence requirements |
| [Continuation plan](CONTINUATION_PLAN_20261104.md) | Current B0–B8 order and required human/scientific/workload gates |
| [RISKS_AND_OPEN_QUESTIONS](RISKS_AND_OPEN_QUESTIONS.md) | Outstanding risks and decisions to revisit |

## Contracts and conventions

| Document | Role |
| --- | --- |
| [SCHEMA](SCHEMA.md), [FIELD_PATHS](FIELD_PATHS.md) | Stored Card contracts, schema versioning and canonical paths |
| [PUBLIC_API](PUBLIC_API.md), [API_CONVENTIONS](API_CONVENTIONS.md), [INTERFACES_MINIMAL](INTERFACES_MINIMAL.md) | Public interfaces and conventions; development additions are distinguished from published delivery |
| [RESOLVER](RESOLVER.md), [SELECTION_RULES_EXAMPLES](SELECTION_RULES_EXAMPLES.md) | Selection without lost alternatives or silent identity merging |
| [SOURCE_ACCESS](SOURCE_ACCESS.md), [SOURCE_ARCHITECTURE](SOURCE_ARCHITECTURE.md) | Clients, fixture/online implementations, mappings, declared enrichers and acquisition observation |
| [ARGUMENT_CONTRACTS](ARGUMENT_CONTRACTS.md), [DIAGNOSTICS](DIAGNOSTICS.md), [DIAGNOSTIC_RECEIVING](DIAGNOSTIC_RECEIVING.md) | ArgDigest contracts, SMonitor outcomes and diagnostic checks |
| [LICENSING_AND_COMPLIANCE](LICENSING_AND_COMPLIANCE.md), [TESTS](TESTS.md) | Source rights, fixture boundaries and behavior-based local/CI gates |
| [LOCATION_EXAMPLES](LOCATION_EXAMPLES.md), [UNIPROT_ENUMS](UNIPROT_ENUMS.md) | Reference examples and source vocabulary |

## Sources, storage and size

| Document | Role |
| --- | --- |
| [Source registry](sources/registry.yaml) and [source process](sources/README.md) | Source adoption/status/terms authority and evaluation workflow |
| [DATA_SOURCES_STATUS](DATA_SOURCES_STATUS.md), [SOURCE_COVERAGE](SOURCE_COVERAGE.md) | Source-specific behavior and scientific coverage; `in_use` does not mean every Card is enriched |
| [Native access](sources/NATIVE_ACCESS_REFERENCE.md), [development native APIs](sources/DEVELOPMENT_API.md), [native mapping](sources/NATIVE_MAPPING_CONVENTIONS.md) | Source-specific protocols, normalization and exact limits |
| [Fixture delivery](sources/FIXTURE_DELIVERY.md) and [inventory](sources/fixture_delivery.json) | Original bytes, protected local inputs and public/local qualification scopes |
| [STORAGE_LAYOUT](STORAGE_LAYOUT.md), [CACHE_POLICY](CACHE_POLICY.md), [CARD_SIZE_RISKS](CARD_SIZE_RISKS.md) | Persistence, reuse, costs and ownership |
| [DOCS_GAPS](DOCS_GAPS.md) | Remaining user-guide work; the user guide itself lives in [docs](../docs/index.md) |

## Working folders

- [pending_bugs](pending_bugs/README.md) and [pending_proposals](pending_proposals/README.md)
  contain issue-backed analyses. A file's presence does not imply unimplemented
  work: read its current status, original receipts and remaining acceptance.
- `evidence/` contains scoped receiving records and reproducible controls. A receipt
  proves only its named source, inputs, behavior and environment.
- [archive](archive/README.md) preserves superseded plans and chronologies. The
  [previous guide index](archive/README_before_onboarding_20261106.md) retains the
  complete older feature/receipt catalogue; it is reference, not today's queue.
- `DECISIONS.md` records accepted decisions; the owning issue carries follow-up.
  [Report template](templates/report.md) and [MolI reporting policy](../MOLI_GUIDE.md#reporting-bugs-and-proposals)
  govern new findings. External disclosure still needs its applicable authority.
- Ignored local evidence is not automatically disposable or public. Follow each
  owner's retention note and the handoff; private pilots never enter this guide.

## Keeping the guide true

A change that makes a line false updates the affected guide in the same commit.
After every implementation increment, update CHECKPOINT with its actual source,
changes, selected gate outcomes, unresolved limits and next action before
continuing. Keep unqualified work explicit and preserve earlier receipts.
Keep current state in CHECKPOINT, scheduling in the continuation plan, breadth in
the completion inventory and long-term objectives in ROADMAP. Update API/schema/
field/test/source contracts with their behavior; do not append the same chronology
to every entry page. Archive superseded explanations with a replacement link,
without rewriting original scientific results or receipt claims.

A decision goes to DECISIONS; a future risk goes to RISKS_AND_OPEN_QUESTIONS and
an owning issue when it needs later review. Every release reviews both roadmap
routes. Public documentation uses generic needs and public systems; confidential
pilot content stays private. Read [devguide instructions](AGENTS.md) before edits.

The [latest onboarding review](evidence/onboarding_review_20261106.json) records
its navigation/example checks, preserved history and known follow-ups; it does
not replace runtime, scientific or researcher acceptance.
