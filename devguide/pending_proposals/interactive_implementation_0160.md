---
summary: Living 0.16.0 implementation plan and granular checkpoint for the Qt-hosted Card and Deck explorer.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: implementation_plan
area: [human-exploration, deck, architecture, standalone, visualization]
---

# Interactive Sabueso 0.16.0: implementation plan and checkpoint

## Resume here

Checkpoint date: **2026-11-13**. Reviewed implementation baseline:
planning parent `fb0d09659f8d00685f829d6781e5d256751dac66`;
[application code hashes and receiving](../evidence/interactive_card_app_checkpoint_20261113.json).

**Current position:** S0 and S1, S3.1–S3.4, S4.1–S4.2, S5.1, S5.2 and S5.4 are delivered at their bounded development scopes. The native Card/Deck application, explicit four-kind source entry and independently selected original readings have real Qt receiving. The [molecular receipt](../evidence/interactive_molecular_checkpoint_20261113.json) adds an opt-in live product panel through Viewer's experimental public service: 84 selected cases, eleven real molecular Qt checks each from checkout and an installed unpublished wheel, and six model-failure checks. A corrected native HTTP guard also passes twelve actual source-entry checks.

**Delivered observable result:** read a Card or Deck, follow source-declared relationships to supplied related Cards, inspect their original sources, return to the exact entry occurrence/Deck selection, save/reopen original Card and Deck readings, and explicitly query supported identifiers. With the received development provider cohort, also open a supplied molecular model, rotate it, float/reset without replacing its viewport, and keep reading original knowledge. The model is always labelled **correspondence not established**. This is not mapped annotation navigation or a supported embedding claim.

**Latest increment:** [rich retained presentation and original whole workspaces](interactive_workspace_persistence_0160.md) add source-linked overview fields, native cell cards/tables/units, sequence strips, current-page relationship graphs, exact breadcrumbs and nonblocking source queries with explicit cancellation/adoption. The public protein → source-bound BTS → native activity → original assay/full publication → exact repeated Deck return now passes in actual Qt, including whole-workspace saving/reopening. The [receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json) separates source epochs, installed receiving and failed controls. Original query history and inner Card trails now persist separately from layout and molecular scene.

The subsequent [candidate checkpoint](interactive_source_candidates_0160.md)
adds explicit UniProt candidate/alternative and PubChem record queries, bounded
original source context, exact saved ambiguity return and a corrected usable
reading area during queries. All 135 application cases, 134 installed runtime
cases and 32 real Qt checks each from checkout/installed wheel pass; a 14-check
live-model regression also passes. The genuine pre-change `796d20e` original
workspace receives inertly and unchanged. This extends S4.1 without resolving an
identity automatically or completing the remaining enrichment/molecular scope.

The [explicit source increment](interactive_source_enrichment_0160.md) now adds
UniProt plus either InterPro sites or AlphaFold prediction records, selected by
the researcher, using existing registered enrichers. New captures retain exact
query return and inert original saving. Bounded source-access observations expose
outcome, fixture/live route and version/basis without claiming scientific coverage.
Additional source failures remain distinct from absence. This extends S4.1/S4.2;
arbitrary source controls, mapped 3D and whole-stage acceptance remain open.

The [referenced-record increment](interactive_record_queries_0160.md) now receives
protein → BTS, compound → declared disease and repeated disease → parent queries,
with original saving and exact query/Deck return. MONDO obsolete replacements
remain explicit separate choices. Source access failures are visible independently
of resolved identity. S4.1/S4.2 close against the original bounded entry/protein
presentation criteria, with source/installed receiving in the linked receipt;
chemical depiction, complete disease associations and mapped structure remain open.
The [concrete Viewer handoff](interactive_viewer_receiving_0160.md) now specifies
current-model/index/event identity, source correspondence and lifetime controls;
it does not select a provider API or close #368.

**Next observable result:** exact source-bound annotation → model selection → original source → Back, including unknown/replaced contexts (S2.2/S2.5), plus qualified chemical depiction and provider lifetime/scene recovery. Viewer #368 still owns the supported embedding/current-model contract. Complete disease-association journeys, chemical depiction, workload agreements and human acceptance remain open; arbitrary source controls remain a future extension. Owned reading-service loss, explicit restart and pending-query shutdown now receive in actual Qt. The [presentation receipt](../evidence/interactive_layout_checkpoint_20261113.json) closes S5.2 at layout-only scope. The whole-workspace receipt does not close remaining scopes or authorize a release. Interrupted attempts never count as passes.

The [complete frozen baseline receipt](../evidence/interactive_integrated_baseline_20261113.json)
receives all **10,059 collected offline nodes** at `e64c2ec`: **10,049 passed,
10 intentional local-only native-input exclusions, zero failures**, and eleven
expected fixture warnings. Eight disjoint completed invocations have verified
receptor integrity and an exact collection union; interrupted records were not
counted. Only the unfinished group was repeated after an elapsed ceiling.
The later molecular/layout code at `55f3b97` has separate 100-case, actual Qt and
installed-wheel receiving. This is not a monolithic run of the later source or
hosted/native-platform qualification. The root editable/headless environment and
protected inputs remain intact.

The maintainer requests this document as both the implementation plan and its
granular checkpoint. It owns stage/microstage status for 0.16.0.
[CHECKPOINT](../CHECKPOINT.md) remains the repository-wide summary and links here;
[ROADMAP](../ROADMAP.md) retains the broader program and dependencies.

## Scope and ownership

Deliver the [accepted experience](interactive_exploration_0160.md): accessible,
researcher-controlled Card/Deck exploration, a scrollable pertinent-topic index,
original-source inspection, exact return context, composable reading/graphical
panels and live molecular representation where supported. Keep local saved
reading, ordinary Python and compact agent use available.

Use **PySide6 + QWebEngine**, a portable web workspace and a separate Python
backend, as recorded in the [decision](../DECISIONS.md#select-pyside6-and-qwebengine-for-the-0160-explorer-2026-11-13).
Reuse the measured React/TypeScript/Dockview workspace as the first implementation
baseline; review its actual free-core capabilities and dependency versions as
part of S1, rather than reopening host selection. Node is frontend build tooling,
not a scientific runtime requirement. Rust already in MolSysMT/MolSysViewer stays
behind provider interfaces; Sabueso adds no competing native scientific engine.

Owners: [#154](https://github.com/uibcdf/sabueso/issues/154) for the application,
[#153](https://github.com/uibcdf/sabueso/issues/153) for Deck human/agent semantics,
[#148](https://github.com/uibcdf/sabueso/issues/148) for existing Card behavior and
researcher continuity, and #112 for coordination. Provider integration belongs to
[MolSysViewer #368](https://github.com/uibcdf/molsysviewer/issues/368), host findings
to [#276](https://github.com/uibcdf/molsysviewer/issues/276), and future structure
residency to [#55](https://github.com/uibcdf/molsysviewer/issues/55).

The accepted functional 0.15.0 milestone and its separate delivery remain fixed.
General document export, presentation video, broad new scientific sources,
simulation/AI engines, remote multiuser hosting and a Rust rewrite are outside
this implementation slice. Ordinary exploration requires no LLM or API key.

## Reading and updating the checkpoint

| State | Meaning |
| --- | --- |
| `done` | The stated scope has an inspectable artifact and applicable verification; link them in the row |
| `partial` | Some work exists; the row identifies both the reusable result and what remains |
| `todo` | The product deliverable has not been implemented |
| `blocked` | A specific unmet dependency prevents this microstage; record its owner and condition |
| `deferred` | A maintainer decision explicitly moves the item out of the current scope; link that decision |

Update the affected rows, current position, next action and qualification note
at each implementation checkpoint, in the same commit as the work. Preserve
failed checks and unresolved limits. A prototype result is not product receiving;
core behavior already implemented is not a delivered visual journey. Do not infer
a completion percentage from row counts or test totals.

| Stage | Current state | Exit result |
| --- | --- | --- |
| S0 — Direction and feasibility | `done` | Accepted architecture, bounded observations and owner handoff |
| S1 — First usable Card application | `done` | Generic supplied-Card → topic → item → source → Back → saved reading in Qt |
| S2 — Molecular workspace | `partial` | Live Viewer integration and layout continuity in the product, not only the probe |
| S3 — Deck exploration | `done` | Shared human/agent Deck contract plus exact Deck → Card → source → Deck navigation |
| S4 — Entry and entity-specific exploration | `partial` | Bounded UniProt/PDB/SMILES/disease entry and useful protein/molecule/disease views |
| S5 — Durable sessions and delivery foundation | `partial` | Independent reopening, separate layout/model state, owned process lifetime and optional GUI closure |
| S6 — Acceptance and version closeout | `partial` | Public review materials and measured application workloads prepared; actual reviews, budget agreement, functional acceptance and delivery decisions remain open |

## S0 — Direction and feasibility

Objective: choose one implementable host using evidence and preserve migration
boundaries. This stage is complete at its development-experiment scope.

| ID | State | Delivered result and evidence |
| --- | --- | --- |
| S0.1 | `done` | Researcher-controlled experience, topic index and composable panels: [experience design](interactive_exploration_0160.md) |
| S0.2 | `done` | PySide6/QWebEngine, portable web UI, separate Python authority and provider-owned molecular adapter: [accepted decision](../DECISIONS.md#select-pyside6-and-qwebengine-for-the-0160-explorer-2026-11-13) |
| S0.3 | `done` | Same live workspace in Qt/Electron/Tauri, 16 selected checks and 20 retained-panel cycles per final initial profile: [first receipt](standalone_probe_20261113.md) |
| S0.4 | `done` | Graphics observations and eight bounded synthetic scale cases, including 63,728 atoms × 32 identical structures: [follow-up receipt and limits](standalone_gpu_scale_20261113.md) |
| S0.5 | `done` | Conclusions delivered in [Sabueso #154](https://github.com/uibcdf/sabueso/issues/154#issuecomment-6846176298) and [Viewer #276](https://github.com/uibcdf/molsysviewer/issues/276#issuecomment-6846178277); embedding request #368 remains open |

These observations establish feasibility, not a performance/thermal winner,
realistic varied trajectories, supported native platforms or a public installer.
Reopen host selection only for the [recorded concrete triggers](standalone_gpu_scale_20261113.md#accepted-0160-host-and-rationale).

## S1 — First usable Card application

Objective: deliver a small, generic application the maintainer can actually open
and use. Reuse the probe's proven operations, not its hardcoded cohort, diagnostic
controls, globals or experimental production assumptions.
The [probe session](../../devtools/standalone_probe/backend.py) is the extraction
reference; [Card exploration](../../sabueso/core/card_exploration.py) and
[saved reading](../../sabueso/core/card_exploration_storage.py) remain authoritative.

| ID | State | Deliverable and completion check |
| --- | --- | --- |
| S1.1 | `done` | Extract a generic Knowledge session using `Card.explore()`, existing topic/item/source readers and `read_exploration()`. Define finite application requests and responses with exact result/view/item references. Verify source/Back and saved reopening against the original readers, including invalid or stale references |
| S1.2 | `done` | Establish the optional application package, portable frontend and thin Qt launcher with a separately owned Python service. Audit/pin the reused frontend cohort; derive runtime minima from consumed APIs. Verify ordinary Sabueso import/headless use without GUI dependencies |
| S1.3 | `done` | Add the light entry screen for opening a supplied Card/saved reading and the first workspace: title/scope, scrollable pertinent-topic index, readable content, source access, Back and clear loading/error/empty states. Preserve complete retained access beyond curated previews |
| S1.4 | `done` | Complete the first frozen public protein journey and a changed/unsupported-input control. Opening topics must not acquire sources, mutate the Card or silently change captured scope. Keyboard operation must cover the basic route |
| S1.5 | `done` | Run targeted session/argument/quantity/saved-reading gates and one bounded actual Qt journey. Record the exact source/input cohort and a reviewable working demonstration; update this checkpoint before expanding scope |

Initial internal placement: `sabueso/explorer/` for the optional application,
session/service and host/provider adapters; `frontend/explorer/` for web source
and its lockfile; `tests/explorer/` for consumer checks. Confirm local conventions
while extracting S1.1. Public launcher/function names and package-data declarations
are implemented and tested in S1.2, not promised by this plan. Keep
`devtools/standalone_probe/` as the comparison/reference tool, not the product.

The service exposes a closed application surface, not arbitrary Python calls.
Reuse explicit session lifetime, loopback/origin/capability handling and safe
rendering of source text. Public Python arguments use ArgDigest, optional features
use DepDigest and diagnostics use SMonitor. Do not duplicate scientific logic or
serialize quantities without their existing value/unit codecs.

## S2 — Molecular workspace

Objective: connect the researcher's current knowledge context to a real molecular
view while keeping model identity, source mapping and scene ownership explicit.
S1 remains usable when no supported molecular representation is available.
The [initial live receipt](standalone_probe_20261113.md) and
[graphics/scale receipt](standalone_gpu_scale_20261113.md) supply the partial
rows' experiment evidence, not product acceptance.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S2.1 | `partial` | The product now isolates an opt-in adapter to the experimental public `RemoteSessionService`/`MolSysView`: bounded detached initial input, live readiness/camera observations and owned cleanup pass. The current model has no established Card correspondence. Receive the stable contract under #368 before a supported embedding claim; no private Viewer protocol is copied |
| S2.2 | `partial` | Probe picking/selection and stale-mapping refusal pass. Implement product selection ↔ reading navigation for exact captured model/occurrence/residue references; test unknown, ambiguous, replaced and reindexed contexts without inferring identity |
| S2.3 | `partial` | The product adds model/reading/context panels and keyboard-addressable Show/Float/Reset buttons. Three real float/reset cycles preserve the iframe, camera and reading, returning all panels to the main grid. The selection was empty, so nonempty mapped selection, graph panels and broader layout receiving remain open |
| S2.4 | `partial` | The product owns the initial model copy, service and view through application shutdown; successful and rejected-model runs leave no owned survivors. Probe independent disposal and Movie acknowledgments remain experiment evidence. Product panel close/reopen, pending operations, a surviving second view and supported background suspension remain open |
| S2.5 | `todo` | Demonstrate the actual product's annotation → 3D selection → original source → Back journey, plus a useful no-coordinate Card. Separate native composition, actual renderer, model delivery and user-understanding observations |

#368 is a dependency of a supported molecular embedding claim, not a reason to
stop S1 or headless Deck work. Keep any temporary development binding explicitly
bounded behind the adapter and linked to its owner. Rust and future Mol* changes
remain provider work; binary transport alone does not prove zero-copy or latency.

## S3 — Deck exploration

Objective: provide complete Deck orientation and exact navigation shared by the
human interface and compact agents, without creating a second knowledge model.
The existing [Deck implementation](../../sabueso/core/deck.py) supplies the
reusable primitives below; the open #153 contract remains the missing product work.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S3.1 | `done` | Existing `Deck` has membership/exclusion explanations, filters/order, snapshots and scientific operations. The initial reuse audit found no general `Deck.explore()` entry; S3.2 now supplies it. The [reuse audit](deck_exploration_contract_0160.md) records mutable/captured boundaries, repeated-member semantics and existing metadata-preserving persistence; S3.2 owns the missing contract |
| S3.2 | `done` | Native `Deck.explore()`/`access()` implement the bounded human/agent contract: overview, membership basis, selections, typed discovery, finite pages and exact captured members. Original capture and typed pages are shared by GUI and agents; [contract and limits](deck_exploration_contract_0160.md) |
| S3.3 | `done` | Qt Deck → selected Card → item → source → exact Deck return preserves filter, order, repeated occurrence and original revision. Eleven actual Qt checks pass from checkout and installed wheel; [receiving](../evidence/interactive_deck_checkpoint_20261113.json) |
| S3.4 | `done` | Cross-member source/identity context has its [receipt](../evidence/interactive_cross_member_checkpoint_20261113.json). Independent original Deck readings now compose unchanged Card bundles with complete metadata, ordered/repeated/anonymous inputs and exact selection/order/Back. Qt also restores metadata mode, page and nonlinear Deck history; checkout, separate-process startup and installed-wheel routes pass. [Saved Deck receipt](../evidence/interactive_deck_saved_checkpoint_20261113.json). This saves the outer Deck reading; focused Card UI history, query history, layout and molecular scene retain separate scopes |

Do not display heterogeneous scientific quantities in a forced universal
comparison. Reuse existing scientific operations and named/versioned rules.
Any new Deck saved-reading envelope needs independent receiving; it must preserve
existing Card formats and retain its own scope/version under #153.

## S4 — Entry and entity-specific exploration

Objective: connect the light entry screen to real resolution/acquisition behavior
and nature-appropriate exploration, with visible user control over further work.
The [resolution guide](../../docs/content/user/resolving.md) and
[resolver entry](../../sabueso/tools/resolve.py) describe the existing core scope;
the [experience design](interactive_exploration_0160.md#entry-identity-and-the-first-useful-reading)
records the distinct input meanings and gaps.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S4.1 | `done` | Bounded UniProt/PDB/SMILES/disease-ID entry, one explicit background worker, progress/cancel/discard and late-result adoption receive with distinct positive/ambiguous/not-found/failed and partially successful source outcomes. UniProt/PubChem choices and MONDO obsolete replacements remain separate explicit queries, preserving originals. Current-page retained links can request fresh records without identity merging. [Criteria reconciliation and receiving](interactive_record_queries_0160.md#reconcile-the-bounded-s4-criteria). Arbitrary source controls are an extension; active provider HTTP interruption is not promised |
| S4.2 | `done` | The pertinent native protein catalog exposes source-linked sequence/annotations, structures, ligands, changes and associations, with original overview/value/unit cells, source inspection and exact return. Uncertain/unsupported/original-not-saved scope stays discoverable; source-selected InterPro/AlphaFold records retain their native meaning. Public nature-specific and cross-Card receiving bind this presentation scope. [Original criteria reconciliation](interactive_record_queries_0160.md#reconcile-the-bounded-s4-criteria); mapped annotation visuals retain S2 ownership |
| S4.3 | `partial` | Actual SMILES → PubChem-stated Card, original chemical/property values with units and a source-bound BTS → supplied target → native activity → assay/publication journey pass. Qualified 2D/available 3D remain open; no conformer or measured geometry is invented |
| S4.4 | `partial` | Disease-ID → MONDO, original overview fields, current-page retained relationship graph, exact edge/source/Back and source-declared parent Card receiving pass. Graphs preserve native support/derivation scope. Explicit fresh disease-parent queries and a compound’s declared condition now also receive through exact original/Deck return. Complete retained target/drug/phenotype association journeys and richer comparisons remain. Name search is not offered without a candidate-search contract |
| S4.5 | `partial` | Protein → source-bound BTS identity → native activity quantity → original assay/full publication → exact repeated/filtered Deck return now passes in real Qt, including original workspace saving/reopening. PDB record → source-declared protein → source → exact query return also passes. The PDB/entity → mapped molecular reading remains dependent on S2/#368; graphs add no scientific conclusions |

A PDB result is currently a structure record with related proteins, not a new
StructureCard; #20 retains that redesign if needed. An ambiguity list is not
automatically a scientifically justified Deck. Optional suggestions expose
existing questions; the researcher chooses topic, depth, route and layout.

## S5 — Durable sessions and delivery foundation

Objective: preserve original readings, recover useful workspace state and keep
optional GUI/process resources independently owned.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S5.1 | `done` | Independent original Card reading and Deck selection restoration retain their earlier receipts. The [whole-workspace receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json) now adds exact inner Card trails/pages, Deck occurrence/selection/Back and original source-query reports/return points, composing unchanged native formats. Plain/gzip/zstd reopening is inert; pending jobs, scene and layout stay separate |
| S5.2 | `done` | Versioned 64 KiB presentation-only persistence admits the three known panels and exact Dockview cohort. Real save/reload preserves reading/float arrangement; Reset uses defaults, live-model saving keeps the viewport, and missing-model/unknown-version controls explain fallback. Unknown originals and symlinks are never overwritten; no Knowledge, query history or scene is restored. [Receipt and limits](../evidence/interactive_layout_checkpoint_20261113.json) |
| S5.3 | `partial` | Actual installed Qt now receives controlled owned-service loss, the surviving reading/window, visible error and explicit original-workspace restart with exact Back. A synthetic pending query closes with its owned service in about 2.24 s; no result is adopted and its bootstrap retires. Cancellation/stale-result handling and atomic/private caller-safe bootstrap pass. Model pending-operation/lifetime receiving remains under S2/#368 and native Windows shutdown is unqualified; unsaved crash recovery is not claimed |
| S5.4 | `done` | Include the compiled frontend/resources in the optional product closure, qualify headless/GUI boundaries and verify a development launch outside the checkout. Keep Electron/Tauri comparison runtimes out of the shipped Qt closure |
| S5.5 | `partial` | The [source/resource increment](interactive_source_enrichment_0160.md#bounded-product-resource-observations) receives two sequential installed public model profiles, 12 float/reset cycles each and short idle/active windows, with 14 checks each and about 1.76/1.86 GiB summed-RSS peaks. Renderer is llvmpipe; the AF fragment is deliberately unrelated to the Card. Failed-input controls retain earlier receipts. Repeated provider creation/disposal, longer settled sessions and agreed scaling cases remain. Preflight shared resources, run sequential graphics trials and record actual CPU/RAM/graphics and cleanup; do not import an unrelated budget or claim thermal superiority |

Use the existing shared-resource policy and infrastructure owners. This application
does not implement a new scheduler, reserve the host or require operational Slurm
to read Cards. Exact installed/native qualification follows the actual optional
dependency and claimed platform scope; a successful local launch is not a public
installation route.

## S6 — Acceptance and version closeout

Objective: assess the complete bounded experience and state exactly what 0.16.0
delivers. Start feedback when the first useful slice exists, not only at the end.

| ID | State | Deliverable and completion check |
| --- | --- | --- |
| S6.1 | `partial` | [Public input preparation, uncoached tasks and worksheet](interactive_researcher_review_0160.md) are prepared and preparation runs without network. Maintainer and independent researcher observations remain `not_reviewed`; record understanding/navigation/accessibility, including molecular limits. The 0.15.0 deferral does not waive 0.16.0 review |
| S6.2 | `partial` | Actual source-bound rich Card/query/mixed scientific Deck workloads now have bounded checkout/installed observations. The latest installed mixed workspace saves in about 84 s and reopens in 25 s in its received two-CPU profile; the earlier cohort observed 87/25 s. This is not an agreed budget or a native-platform/scaling claim. Two installed molecular profiles now add short idle/active and repeated-layout observations; these do not establish a settled idle budget or repeated provider lifetime. Agree workload-specific targets and complete longer/lifetime measurements before provider optimizations |
| S6.3 | `todo` | Reconcile every accepted 0.16.0 journey against implementation, regressions, original saved compatibility and visible limits. Reconsider #192's meaning/correction and the #194 macOS exception before the version decision; neither 0.15.0 deferral silently extends |
| S6.4 | `todo` | Record functional-milestone acceptance separately from exact-source CI, installed artifacts, supported platforms and publication. Complete the applicable existing release route only for the authorized candidate and actual claimed GUI/core scope |

## Current closeout ledger

The 33 microstages currently contain **19 done, 11 partial and 3 todo**. This is
an unweighted status count, not a percentage of implementation effort or readiness.
Several partial rows already contain working application behavior but depend on
provider contracts or acceptance; their labels must not be promoted by automated
checks alone.

| Remaining front | Concrete next result | Owner / dependency | Can proceed locally? |
| --- | --- | --- | --- |
| Molecular correspondence and supported embedding (S2) | Versioned current-model/occurrence identity and supported selection/lifetime route, then actual annotation → selection → source → Back | Viewer #368; Sabueso #154; initial input hash cannot establish active identity | Consumer refusal/lifetime/resource work can continue; exact mapped product journey awaits the provider contract |
| Chemical depiction and nature-specific presentation (S4) | Source-bound 2D representation through a provider-owned supported surface; richer public protein/molecule/disease receiving | #154; concrete Viewer proposal retained for explicit publication approval | Public retained readers and source controls can continue; no chemical renderer or provider patch is silently adopted |
| Resource and recovery breadth (S5/S6.2) | Varied public model idle/active observations, repeated product/provider lifetime and native-platform receiving; agreed workload targets | #154/#153/#112 | Bounded local measurements can continue; measurements do not themselves establish budgets |
| Human review (S6.1) | Maintainer and independent researcher complete the prepared tasks/worksheet | Maintainer/researcher, #154/#153 | Materials are prepared; human observations cannot be supplied by an agent |
| Scientific/platform decisions (S6.3) | Decide #192 aggregation semantics and reconsider #194's macOS exception for this version | Maintainer, #192/#194 | Preserve the explicit current limitations while decisions are pending |
| Version decision and delivery (S6.4) | Functional scope acceptance followed by the authorized exact-source CI/candidate/platform/publication route | Maintainer, #154/#112 | No release/tag/CI dispatch is implied by implementation authority |

This ledger reconciles the present scope without claiming completion of S6.3:
#192/#194 and complete journey acceptance are still decisions to receive. The
original stage rows and their evidence retain authority over each delivered scope.

## Execution order and immediate handoff

1. S1.1–S1.5 now deliver the first working Qt Card application. See the
   [development instructions](../../frontend/explorer/README.md) and exact
   [receiving record](../evidence/interactive_card_app_checkpoint_20261113.json).
2. Add S2's live molecular product slice. If a provider contract is blocked,
   record the exact affected row and continue independent S3/S4 work.
3. Complete the Deck contract/UI and entity-entry journeys, retaining original
   scientific semantics. Develop S5 durability alongside each usable slice.
4. Obtain early S6 feedback; finish functional scope and actual qualification
   without reopening the completed generic host comparison.

Next checkpoint must identify the completed/partial microstages, exact source,
applicable gates and remaining dependency. Python checks use the receptor and
the shared editable 3.14 environment; core changes select the affected native,
human/agent/saved/argument/quantity gates in [TESTS](../TESTS.md). GUI receiving
adds type/build checks and bounded real-host journeys; mocks alone cannot qualify
rendering. Documentation-only updates use their applicable local gates.

Commits follow the authorized `[skip ci]` batching and
[deferred-CI recovery record](deferred_ci.md). A skipped push is not hosted
qualification. Preserve useful measurement evidence with its owner/review trigger
and remove only owned disposable resources after final use.

The initial plan alone marked no product milestone done. The later molecular slice remains experimental and partial; its initial input digest is not active-model or Card identity. The prior requests-only fixture guard did not intercept native urllib: the new guard regression and twelve-check Qt rerun correct that limit, without an observed live-source leak.

The current S1/S5.4
closures rely on implementation, 118 selected integration cases, a final
43-case application/package/dependency gate, type/build checks, and eleven
actual Qt checks each from the checkout and an installed unpublished wheel.
Optional PySide6/aiohttp and packaged web assets are introduced. No Card schema,
scientific reader, supported platform, candidate or public release is changed.

Planning-checkpoint verification: root Ruff format/lint, local MOLI governance,
diff checks and scoped local links pass. All 33 microstage IDs are unique; seven
stages, allowed states and the S1.1 resumption cursor are consistent. These remain documentation checks; the separate linked application receipt
owns actual runtime receiving and its limits.

## Latest implementation checkpoint — S1

See the [source-bound receipt](../evidence/interactive_card_app_checkpoint_20261113.json).
Generic session actions retain exact result/page/return identity; finite pages
expose complete literal text. Raw Card files cross the browser boundary without
JavaScript numeric reserialization, preserving quantity seals and large integers.
Private loopback actions require the current revision and exact page item.
Original saved reading and its digest verifier remain authoritative.

Checkout and installed-wheel Qt journeys each pass eleven selected checks and
leave no owned descendants. Summed RSS peaks are about 1.05–1.06 GiB in these
software-profile cases; this is not unique physical memory, a molecular benchmark
or native platform support. The first failed upload control is retained: JavaScript
round-tripping changed sealed numeric types; forwarding the original body fixes
the boundary without weakening verification. Earlier selector/PNG-write races
were observer errors; no failing control is counted as passing.

At the S1 checkpoint, S2 stable embedding, S3 Deck contracts/UI, identifier acquisition, 2D/3D chemistry,
workspace persistence/recovery and researcher/whole-version acceptance remain
open. Source acquisition is still absent from ordinary application reading.

## Latest implementation checkpoint — S3 native Deck and application

The [source-bound Deck receipt](../evidence/interactive_deck_checkpoint_20261113.json) records 76 selected passes and eleven real Qt checks each from checkout and an installed unpublished wheel. The native contract detaches original metadata/Cards, keeps repeated occurrences distinct, exposes byte/record-bounded typed pages and restores exact filter/order/selection. No global scientific quantity comparison or automatic acquisition is introduced.

The actual #197 correction rejects unsupported Deck envelope versions before reading members, retaining format 1 and documented legacy routes. It changes no Card schema. The new receiving has positive/negative/legacy controls. A 30-minute full offline attempt reached its time ceiling; the next attempt was interrupted by the server restart after 3,724 positive call records. Neither has a completed verdict. Full final-source/hosted qualification remains due under #154/#112. A native observer's missing optional argument failed before application startup; the corrected observer and installed receiving pass.

At this earlier S3 checkpoint, cross-member context and independent Deck saved workspace remained open. Cross-member context and original Deck-selection persistence are now received in the later S3.4 increments above; supported mapped molecular integration and remaining S4–S6 work are still open. Native Deck payload persistence and saved individual Card readings retain their separate meanings.

## Latest implementation checkpoint — S4 explicit entry and return

The [entry receipt](../evidence/interactive_entry_checkpoint_20261113.json) binds the application bytes, 73 selected application/routing/package cases and twelve actual Qt checks. All six recorded source queries are explicit user actions against public frozen clients; browsing/source/Back/query-return adds none. UI updates and scientific resolution run in separate processes, with one serialized worker. The original resolution and acquisition trace remain inspectable; `ambiguous`, `unsupported`, `not_found` and `error` are not collapsed.

Queries have finite input limits and exact Card/resolution revisions. Earlier reading survives a query that produces no Card. A successful explicit query retains an independent navigation return point; original PDB context is restored without acquiring proteins again. Initial SMILES identity uses PubChem's assertion and an explicit `unichem=False` override, recorded by native profile semantics. Disease-name lookup, generic ambiguity selection, new enrichments, molecule depiction, complete scientific cross-member journeys and durable whole-workspace recovery remain open.

## Latest implementation checkpoint — S5.1 original file entry

The [original-file receipt](../evidence/interactive_original_file_checkpoint_20261113.json) receives the integrated Card/Deck/entry application with 124 selected passes and thirteen actual Qt checks. Open reading forwards the original file body to the existing original reader, independently of a save in the current session. Plain/gzip/zstd controls preserve literal float/large integer/false/null/quantity values and forbid Card reconstruction; malformed originals and stale uploads preserve the prior reading. Existing transport/semantic verifiers and formats stay unchanged. The original reader retains its own captured scope; no whole-workspace saving is implied. The final full offline collection is being qualified through disjoint resumable groups after the two retained interruptions; no incomplete attempt counts as passing.
