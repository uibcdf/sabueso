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

**Current position:** S0 and S1 are complete at the first development-application
scope. S3.1 reuse audit and S5.4 development artifact receiving also pass. The
Qt Card application opens original files, navigates and saves/reopens them.
Next: **S2.1**, the product molecular adapter; continue **S3.2** independently
while the stable provider embedding surface remains open under Viewer #368.

**Delivered observable result:** the first supplied-Card/topic/item/source/Back/
save/reopen journey works in a dedicated Qt window, including entry from a blank
window and a separately installed unpublished wheel. **Next observable result:**
link that reading to an explicitly mapped live molecular view, without copying
provider internals or silently inventing correspondence.

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
| S3 — Deck exploration | `partial` | Shared human/agent Deck contract plus exact Deck → Card → source → Deck navigation |
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
| S2.1 | `partial` | The probe has a live provider adapter and original source mapping. Isolate the product adapter, negotiate actual capabilities/readiness and receive the provider-owned embedding contract under #368; do not ship copied private Viewer internals |
| S2.2 | `partial` | Probe picking/selection and stale-mapping refusal pass. Implement product selection ↔ reading navigation for exact captured model/occurrence/residue references; test unknown, ambiguous, replaced and reindexed contexts without inferring identity |
| S2.3 | `partial` | Probe retains camera/selection through 20 layout cycles. Integrate the molecular panel with reading/graph panels, resize/dock/float, optional fixed context and layout reset; verify scene continuity and keyboard-accessible alternatives to dragging |
| S2.4 | `partial` | Probe independent disposal and public Movie draw acknowledgments work. Receive product hide/show/final-close, pending-operation and surviving-view behavior; qualify background suspension only when the provider supports it |
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
| S3.1 | `done` | Existing `Deck` has membership/exclusion explanations, filters/order, snapshots and scientific operations. Initial inspection confirms no general `Deck.explore()` entry. The [reuse audit](deck_exploration_contract_0160.md) records mutable/captured boundaries, repeated-member semantics and existing metadata-preserving persistence; S3.2 owns the missing contract |
| S3.2 | `todo` | Implement the bounded human/agent Deck contract: overview, membership basis, selections, typed discovery, finite pages and exact captured members. Names such as `explore()`/`access()` require the actual API review; GUI code must not invent a competing contract |
| S3.3 | `todo` | Add the Deck workspace and Deck → selected Card → item → source → exact Deck return, preserving filter, order, selection, repeated occurrence and original revision |
| S3.4 | `todo` | Exercise public homogeneous/mixed decks, empty selection, missing members, duplicates/revision ambiguity and historical reopening. Keep complete metadata/support access and compact agent retrieval available outside the GUI |

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
| S4.1 | `partial` | Core UniProt, PDB, prefixed SMILES and disease-ID resolution exists with distinct outcomes. Connect it to bounded explicit acquisition, progress and selected candidates. Test found/ambiguous/not-found/partial/failed results; browsing retained topics performs no background acquisition |
| S4.2 | `partial` | The generic topic index and native readers now work in the Card application. Qualify the nature-specific protein presentations, source-linked sequence/annotations, structures, ligands, changes and associations. All retained topics remain discoverable, including uncertain or unsupported scope |
| S4.3 | `todo` | Provide small-molecule identity/representations, scoped properties with units/methods, targets/activity and clinical context; qualify the chosen provider for 2D/available 3D. A generated conformer is explicit modeling, not measured geometry or source identity |
| S4.4 | `todo` | Provide disease definition/hierarchy and retained target/drug/phenotype associations, with related Cards/Decks and exact return. Supported disease IDs are the initial bounded entry; name search needs an actual candidate-search contract before being offered |
| S4.5 | `todo` | Complete two multi-entity public journeys: protein → ligand → activity → assay/publication → exact Deck return; and PDB record → source-declared related entity → mapped molecular reading. Qualify any graphs against the retained values/support, without adding scientific conclusions |

A PDB result is currently a structure record with related proteins, not a new
StructureCard; #20 retains that redesign if needed. An ambiguity list is not
automatically a scientifically justified Deck. Optional suggestions expose
existing questions; the researcher chooses topic, depth, route and layout.

## S5 — Durable sessions and delivery foundation

Objective: preserve original readings, recover useful workspace state and keep
optional GUI/process resources independently owned.

| ID | State | Delivered work, remainder and completion check |
| --- | --- | --- |
| S5.1 | `partial` | Card saved exploration and inert independent reading already exist; probe save/reopen passes. Integrate actual user-selected files and exact digest/scope verification, preserving original values, units, source support and historical readers |
| S5.2 | `todo` | Persist versioned presentation layout separately from Knowledge and provider scene/model references. Restore or explain unavailable context without silently loading a current revision; validate unknown layout versions and reset behavior |
| S5.3 | `partial` | The probe owns startup/shutdown and bounds experiments. Implement product process lifetime, backend failure/restart, pending-work handling and any supported cancellation without freezing the UI or affecting another session |
| S5.4 | `done` | Include the compiled frontend/resources in the optional product closure, qualify headless/GUI boundaries and verify a development launch outside the checkout. Keep Electron/Tauri comparison runtimes out of the shipped Qt closure |
| S5.5 | `todo` | Measure one representative active/idle/repeated-open session, then agreed larger/varied public cases. Preflight shared resources, run sequential graphics trials and record actual CPU/RAM/graphics and cleanup; do not import an unrelated budget or claim thermal superiority |

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

The initial plan alone marked no product milestone done. The current S1/S5.4
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

S2 stable embedding, S3 Deck contracts/UI, identifier acquisition, 2D/3D chemistry,
workspace persistence/recovery and researcher/whole-version acceptance remain
open. Source acquisition is still absent from ordinary application reading.
