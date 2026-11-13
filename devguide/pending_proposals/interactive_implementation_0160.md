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

**Current position:** S0 and S1, S3.1–S3.4, S5.1, S5.2 and S5.4 are delivered at their bounded development scopes. The native Card/Deck application, explicit four-kind source entry and independently selected original readings have real Qt receiving. The [molecular receipt](../evidence/interactive_molecular_checkpoint_20261113.json) adds an opt-in live product panel through Viewer's experimental public service: 84 selected cases, eleven real molecular Qt checks each from checkout and an installed unpublished wheel, and six model-failure checks. A corrected native HTTP guard also passes twelve actual source-entry checks.

**Delivered observable result:** read a Card or Deck, follow source-declared relationships to supplied related Cards, inspect their original sources, return to the exact entry occurrence/Deck selection, save/reopen original Card and Deck readings, and explicitly query supported identifiers. With the received development provider cohort, also open a supplied molecular model, rotate it, float/reset without replacing its viewport, and keep reading original knowledge. The model is always labelled **correspondence not established**. This is not mapped annotation navigation or a supported embedding claim.

**Next observable result:** exact source-bound annotation → model selection → original source → Back, including unknown/replaced contexts (S2.2/S2.5), plus richer protein/molecule multi-entity presentation (S4.2/S4.5). Cross-member source/context navigation has its [receipt](../evidence/interactive_cross_member_checkpoint_20261113.json); the [original Deck receipt](../evidence/interactive_deck_saved_checkpoint_20261113.json) now closes S3.4 at Deck-selection scope. Viewer #368 still owns the supported embedding contract. Original query/scene recovery, richer entity-specific presentation and acceptance remain open. The [presentation receipt](../evidence/interactive_layout_checkpoint_20261113.json) closes S5.2 at layout-only scope: explicit save, startup restoration and reset keep Knowledge and model state separate. Interrupted full-suite attempts never count as passes; completed source-bound collection receiving has its own receipt.

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
| S6 — Acceptance and version closeout | `todo` | Agreed functional scope, actual review/workload results and explicit remaining delivery limits |

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
| S4.1 | `partial` | The Qt entry reuses native resolution with `identity@1`, explicit source submission, pending/result states, original decisions/trace and separate source-declared PDB protein queries. Found, ambiguous, not-found, unsupported and source-error controls pass; exact query return is source-free. Remaining work: richer progress/cancellation and general candidate-selection/partial-enrichment presentation |
| S4.2 | `partial` | The generic topic index and native readers now work in the Card application. Qualify the nature-specific protein presentations, source-linked sequence/annotations, structures, ligands, changes and associations. All retained topics remain discoverable, including uncertain or unsupported scope |
| S4.3 | `partial` | Actual SMILES → PubChem-stated molecule Card and native pertinent-topic index pass in Qt. Retained chemistry/property/activity/clinical readers remain authoritative. Useful source-linked multi-entity presentation and qualified 2D/available 3D remain open; no conformer or measured geometry is invented |
| S4.4 | `partial` | Supported disease-ID → MONDO Card and pertinent-topic presentation pass in actual Qt. Definition/hierarchy and retained association routes reuse the native readers; source-declared parent Cards and their exact original return now receive inside a supplied Deck. Broader related protein/molecule/Deck journeys and disease-specific visual presentation remain open. Name search is not offered without a candidate-search contract |
| S4.5 | `partial` | PDB record → source-declared protein → source → exact original query return passes in Qt. Complete the mapped molecular part and two multi-entity public journeys: protein → ligand → activity → assay/publication → exact Deck return; and PDB record → source-declared related entity → mapped molecular reading. Qualify any graphs against the retained values/support, without adding scientific conclusions |

A PDB result is currently a structure record with related proteins, not a new
StructureCard; #20 retains that redesign if needed. An ambiguity list is not
automatically a scientifically justified Deck. Optional suggestions expose
existing questions; the researcher chooses topic, depth, route and layout.

## S5 — Durable sessions and delivery foundation

Objective: preserve original readings, recover useful workspace state and keep
optional GUI/process resources independently owned.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S5.1 | `done` | Open an independently selected original Card reading through its existing verifier, preserving original values/units/support, mode and scope. Plain/gzip/zstd inert controls and thirteen actual Qt checks pass; [receipt](../evidence/interactive_original_file_checkpoint_20261113.json). Original Deck selection restoration is delivered in S3.4; whole query restoration remains open; presentation-only restoration is delivered in S5.2 |
| S5.2 | `done` | Versioned 64 KiB presentation-only persistence admits the three known panels and exact Dockview cohort. Real save/reload preserves reading/float arrangement; Reset uses defaults, live-model saving keeps the viewport, and missing-model/unknown-version controls explain fallback. Unknown originals and symlinks are never overwritten; no Knowledge, query history or scene is restored. [Receipt and limits](../evidence/interactive_layout_checkpoint_20261113.json) |
| S5.3 | `partial` | The product owns a separate service process, startup deadline, bounded shutdown and optional model cleanup; rejected molecular input keeps the Card usable. Backend failure/restart, pending work, cancellation, atomic bootstrap handoff and Windows event-loop shutdown receiving remain open |
| S5.4 | `done` | Include the compiled frontend/resources in the optional product closure, qualify headless/GUI boundaries and verify a development launch outside the checkout. Keep Electron/Tauri comparison runtimes out of the shipped Qt closure |
| S5.5 | `partial` | One actual public molecular session and failed-input control have bounded RSS/CPU-affinity/cleanup receipts. Measure active/idle/repeated-open behavior and agreed larger/varied public cases. Preflight shared resources, run sequential graphics trials and record actual CPU/RAM/graphics and cleanup; do not import an unrelated budget or claim thermal superiority |

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
| S6.1 | `todo` | Review the first Card and molecular slices with the maintainer, then obtain independent researcher observations of agreed tasks. Record understanding, navigation/accessibility failures and actual review status; the 0.15.0 deferral does not waive 0.16.0 review |
| S6.2 | `todo` | Agree workload-specific budgets from the real application and repeat representative measurements. Attribute preparation/residency/transport/draw costs before proposing provider optimizations; report actionable findings to their owners |
| S6.3 | `todo` | Reconcile every accepted 0.16.0 journey against implementation, regressions, original saved compatibility and visible limits. Reconsider #192's meaning/correction and the #194 macOS exception before the version decision; neither 0.15.0 deferral silently extends |
| S6.4 | `todo` | Record functional-milestone acceptance separately from exact-source CI, installed artifacts, supported platforms and publication. Complete the applicable existing release route only for the authorized candidate and actual claimed GUI/core scope |

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
