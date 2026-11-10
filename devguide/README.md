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

The next B6 [protein comparative/association profile](pending_proposals/card_protein_context_exploration.md)
now implements LIVE retained orthology/cluster and disease/pathway/interaction
panels, shared with typed compact agents. Explicit supplied sequence comparison
reuses the original equal-position native rule without establishing correspondence
or identity. Its clean SDK239
[genuine original](evidence/protein_context_live_original_20261109.json) now has
independent logical @33 / shared @34 reading and public saving. The
[saved checkpoint](evidence/protein_context_saved_checkpoint_20261109.json) owns
original human/source/agent preservation, exact actual access instances and local
qualification. The next [knowledge/map comparison profile](pending_proposals/card_knowledge_comparison_exploration.md)
now shares explicit `card_knowledge_diff@2` typed field, relationship and state
results between LIVE human and compact-agent routes. Exact caller maps retain
uncertain and ambiguous scope. Its clean SDK243 [genuine original](evidence/knowledge_comparison_live_original_20261110.json)
now preserves all 37 complete public/synthetic cases, actual source/access graphs
and finite requests. Independent logical @35 / shared @36 reading and public saving now preserve those
observations. The [saved receipt](evidence/knowledge_comparison_saved_checkpoint_20261110.json)
owns local source/copied/diagnostic receiving and limits; earlier rules/defaults
and saved meanings remain fixed.
CHECKPOINT owns qualification; full B6 and B7 acceptance remain open.

The first B6 [variant/isoform tissue-context profile](pending_proposals/card_variant_tissue_exploration.md)
now shares existing scoped native results between human and typed agent access.
It preserves original genomic/transcript/CDS scope, per-tissue unknowns, source
membership and exact navigation. All 44 owning cases pass; the
[LIVE receipt](evidence/variant_tissue_context_live_checkpoint_20261108.json)
owns broader selected/copy qualification and limits. Its clean SDK230
[genuine original](evidence/variant_tissue_context_live_original_20261108.json)
now preserves all 33 observed cases, original source/actual-origin graphs and
1,415 finite agent requests. Its 140 selected and 39 copied original cases pass.
Independent @29/@30 reading and saving pass the
[saved checkpoint](evidence/variant_tissue_context_saved_checkpoint_20261108.json):
1,715 distinct selected source cases and all 200 copied owning cases outside
checkout. The next [natural-variant/mutagenesis profile](pending_proposals/card_sequence_change_exploration.md)
now implements LIVE shared annotation projection and original source/structural
questions; its [1,680-case selected checkpoint](evidence/sequence_change_live_checkpoint_20261109.json)
and all 44 copied owning cases retain their source epoch. The scoped question
continuity fix passes 49 owning and 1,636 adjacent cases. Its clean SDK234
[genuine original](evidence/sequence_change_live_original_20261109.json) now
preserves 31 cases and all actual source/parent/agent graphs: 146 selected and
38 copied original cases pass. Independent logical @31 / shared @32 reading now
preserves those immutable values, source/question routes, finite requests and
distinct actual access instances. Public sequence-change saving is enabled;
the [saved checkpoint](evidence/sequence_change_saved_checkpoint_20261109.json)
owns current qualification and limits. Remaining comparative/association and
B7 acceptance scope stays open. CHECKPOINT owns actual current results.

The [retained disease association profile](pending_proposals/card_disease_association_exploration.md)
is a delivered B5 increment: human and typed agent routes share original
relationship, indication and condition occurrences in explicitly supplied
captures. Source-supported MONDO/MedGen identity paths, direction, unknowns and
exact source/back context stay visible. The [1,031-case selected LIVE checkpoint](evidence/disease_association_live_checkpoint_20261108.json)
and all 43 copied owning cases pass. The clean SDK227 [genuine original](evidence/disease_association_live_original_20261108.json)
preserves 21 complete observed cases, exact multi-access origin graphs and
294 machine requests. The independent logical @27 / physical @28 reader now
preserves those original values, sources, finite requests and actual navigation.
All 178 owning cases pass; copied and adjacent qualification are recorded in the
[saved checkpoint](evidence/disease_association_saved_checkpoint_20261108.json).
Public human, machine and detail saving is enabled in the working implementation.
Definition, identity and hierarchy remain separate. [CHECKPOINT](CHECKPOINT.md)
owns current results and next actions.

The [clinical LIVE profile](pending_proposals/card_clinical_exploration.md) now
shares native indications, individual cited-trial occurrences and retained
registry contexts between human and compact-agent routes. Its
[576-case selected checkpoint](evidence/clinical_live_checkpoint_20261108.json)
and all 40 copied clinical cases pass. The clean SDK224 producer's
[genuine complete original](evidence/clinical_live_original_20261108.json)
is captured and byte/graph-verified before the independent @25/@26 reader.
That reader now implements original clinical values, source roles, finite typed
requests and exact navigation. Its [selected saved checkpoint](evidence/clinical_saved_checkpoint_20261108.json)
passes 805 distinct offline cases and all 91 copied clinical cases; diagnostic
wheel/sdist resource bytes also agree. Installed/hosted and human/scientific
acceptance remain open. [CHECKPOINT](CHECKPOINT.md) owns current source and actual results.
The preceding full reader receipt retains its source epoch and does not qualify
this new clinical implementation.

The [live protein activity journey](pending_proposals/card_bioactivity_exploration.md)
connects molecules, native groups, original activity records and exact retained
assay/citation/publication support. Its separately versioned original saved reader
passes its selected 1,109-case local checkpoint, committed at `276160a`, after a clean SDK200 live capture;
the [saved receipt](evidence/bioactivity_saved_checkpoint_20261106.json) owns the
scope and limits. The broader B4 and human/scientific acceptance remain open.

The [molecule-to-supplied-target activity journey](pending_proposals/card_molecule_activity_exploration.md)
connects exact source-stated molecule identities to explicitly supplied target
captures, native measurements and full source/publication context. Its genuine
SDK205, SDK208 and SDK211 originals remain immutable. The original @21/@22 writer
and independent saved reader preserve source-instance operation history, exact
cross-focal destinations and original inherited questions; current Cards,
scientific readers and clients are forbidden during original receiving.

The current implementation passes **44 complete original-file/boundary cases**,
**264 joined private/LIVE cases** and **443 adjacent cases** on their recorded
source epoch. The [capability receipt](evidence/molecule_activity_saved_capabilities_checkpoint_20261107.json)
owns those results and their earlier red epochs; the
[first real-file receipt](evidence/molecule_activity_real_file_checkpoint_20261107.json)
retains the SDK211 transport/resave and semantic-refusal foundation. Human/agent
catalogs recognize retained activity, and support/save capabilities require the
actual retained operation closure. A public LIVE round trip uses production byte
limits; complete original-file controls explicitly declare their larger scope.

All 54 copied molecule cases pass outside the checkout with complete accounting
and byte-identical inputs. The package-data correction and actual artifact
inspection pass; the [complete local checkpoint](evidence/molecule_activity_full_checkpoint_20261107.json)
qualifies 9,786 distinct offline cases with an exact discovery union.
The installed delivery wiring is applied and locally checked; actual installed
OS/Python, hosted and human/scientific acceptance remain open. The
[numeric root-return correction](pending_bugs/molecule_activity_root_selection_equality.md)
now binds LIVE navigation to the exact initiating instance and typed request;
its selected 515-case local checkpoint passes. Genuine older @21/@22 files retain their
original meaning. The corrected clean SDK218 originals preserve both operand
creation orders. The working independent @23/@24 reader adds an exact originating
node manifest and typed root-return checks while reusing unchanged frozen
scientific predicates. Public LIVE saving is restored; all 69 owning LIVE cases
pass with eight workers and a 10 GiB combined RSS ceiling. All 24 actual-file
cases and the full copied LIVE consumer also pass. Complete copied exact-origin
receiving passes all 254 cases with thirteen byte-identical inputs. The
[901-case selected checkpoint](evidence/molecule_activity_root_exact_saved_checkpoint_20261108.json)
records its selected qualification. The [complete preceding root-reader checkpoint](evidence/molecule_activity_root_exact_full_checkpoint_20261108.json)
now verifies all 10,050 discovered offline cases with an exact union, actual
historical-file receiving and verified worker placement. Installed/hosted and
scientific/human acceptance remain open. The
older 9,786-case receipt does not qualify this changed source.
[CHECKPOINT](CHECKPOINT.md) owns the exact active source, results and next action.
These clinical/root receipts retain their recorded source epochs. Independent
disease association saved reading is implemented; B6 retains its full accepted plan.

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
