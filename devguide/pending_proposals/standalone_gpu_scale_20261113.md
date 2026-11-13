---
summary: Record graphics and synthetic scale observations, the accepted Qt host for 0.16.0 and explicit reassessment triggers.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: bounded_development_experiment
area: [architecture, standalone, visualization, interoperability]
---

# Graphics and scale follow-up

This follows the [first host experiment](standalone_probe_20261113.md) at
`13f86dbe686c786c36c694285c11b25a7ae4738a`. Its original software-profile
receipts retain that epoch. The [method and source](../../devtools/standalone_probe/README.md)
now add explicit graphics profiles, tiny graphics diagnostics, observed NVIDIA
contexts, and separate synthetic scale controls. Owner #154; coordinate useful
provider findings in [MolSysViewer #276](https://github.com/uibcdf/molsysviewer/issues/276)
and [embedding #368](https://github.com/uibcdf/molsysviewer/issues/368).

## Accepted 0.16.0 host and rationale

On 2026-11-13 the maintainer accepts **PySide6 + QWebEngine** for 0.16.0,
with a separate Python backend and portable web workspace. The current alternative
order is **Electron second, Tauri third**. This is an integration/maintenance
decision, not a performance ranking. Keep the workspace, Python authority and
molecular adapter replaceable; see the [decision](../DECISIONS.md#select-pyside6-and-qwebengine-for-the-0160-explorer-2026-11-13).

| Candidate | Current advantage | Current cost or unresolved limit |
| --- | --- | --- |
| Qt / PySide6 + WebEngine | Direct Python integration, existing Viewer experience and the same modern web workspace; current graphics and default-startup profiles work | Qt/WebEngine packaging and browser-engine maintenance, native event-loop/lifecycle details and exact installed-platform receiving; its Chromium base can differ from Electron |
| Electron + Python | Desktop-web tooling and control over the bundled Chromium version; credible route for future engine/browser capabilities | Node/Electron plus Python distribution and security-update work; default sandbox startup fails in this environment, and the working lab bypass cannot ship |
| Tauri + Python | Viable live integration, ordinary system WebKitGTK startup and a small native shell without a bundled browser | Adds owned Rust/build work and OS-WebView variability; this Linux WebKitGTK exposes no WebGPU API, and total-application RAM savings have not been demonstrated |

All three use the same React/TypeScript/Dockview workspace. Choosing Qt does not
require replacing it with native widget-based scientific panels. Electron could
overtake Qt if a qualified packaged/security route and consistent newer browser
capabilities outweigh the extra runtime maintenance. Tauri could rise after
native/platform and future-engine receiving demonstrates a concrete advantage.
Reassess under #154 when those conditions change.

Primary mechanisms: [Qt WebEngine architecture](https://doc.qt.io/qt-6.11/qtwebengine-overview.html),
[Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model)
and [supported release lines](https://www.electronjs.org/docs/latest/tutorial/electron-timelines),
and [Tauri WebView versions](https://v2.tauri.app/reference/webview-versions/).
These mechanisms do not establish application benchmarks or installed support.

The evidence is sufficient for this decision. Close the exploratory host
comparison; next validate the real explorer and its packaged/native execution.
Reassess under #154 if Qt misses a required platform/capability or agreed workload
budget, a provider engine change introduces a measured compatibility gap, or
another host demonstrates a material benefit under equivalent workload/security
conditions. Additional measurements qualify implementation and future needs;
they are not a prerequisite to starting 0.16.0 with Qt.

Avoid guarantees when interpreting proposed stacks. Chromium does not guarantee
WebGPU availability on every driver/session. Electron can keep scientific logic
in Python with only a thin Node host. Qt still needs frontend JavaScript and its
build tools. Reuse Rust already present in MolSysViewer/MolSysMT through their
supported interfaces; optimize measured provider bottlenecks rather than adding
another Rust engine or scientific authority to Sabueso.
[Rust/NumPy ownership transfer](https://docs.rs/numpy/0.30.0/numpy/array/struct.PyArray.html)
can avoid a local allocation copy; it does not eliminate socket, browser or GPU
costs. [Tauri binary responses](https://v2.tauri.app/develop/calling-rust/#returning-array-buffers)
also require a supported Viewer inlet and measured delivery. Heavy work must
leave the UI event loop regardless of the host or implementation language.

## Actual graphics path

The host has NVIDIA RTX 2080 Ti devices, driver 580.178.04, with no owned native
desktop session. A tiny WebGL2 triangle is deliberately separate from a molecular
test. Qt 6.11.2 and Electron 45.3.1 both draw it with an explicit ANGLE/Vulkan
request, CPU window composition and a child-local NVIDIA Vulkan-driver filter.
Their renderer strings identify NVIDIA; read-only NVIDIA samples independently
match graphics contexts to their owned process trees. The same path then draws
the actual public 1TCD model. Qt's native QWidget captures also show the content.

Tauri 2.12.5 with system WebKitGTK 2.52.6 draws the diagnostic and molecular
controls with default renderer selection. Its owned processes have NVIDIA graphics
contexts, but WebKit's fixed `Apple GPU` label does not identify the WebGL device.
Context presence can include composition and is not a separate WebGL-device
certificate. A separate Qt software control confirms this distinction: its
triangle reports Mesa llvmpipe while the owned tree still creates a 5 MB
NVIDIA context. Do not invent a device identity or work around privacy masking.

Both Chromium profiles expose WebGPU but obtain no adapter in this Xvfb setting;
WebKitGTK exposes no `navigator.gpu`. Hardware WebGL and browser WebGPU are
different observations. No unsafe WebGPU flags, global driver/security change,
native Wayland session or physical-display acceptance is introduced. The chosen
ANGLE backend is an explicit development profile, not a production requirement.

The small Vulkan query utility was verified against indexed SHA256 metadata and
extracted locally; no additional system package was installed. The previously
authorized maintainer WebKitGTK installation remains the only system-package
change. All three Python components were independently verified editable and
imported from their sibling checkouts outside the Sabueso checkout.

## Bounded synthetic cases

Public MolSysMT conversion/merge/append APIs create overlapping independent copies
of the frozen TcTIM/1TCD input and identical conformations. The two axes are
independent controls. These are not physical assemblies, molecular dynamics,
diverse trajectories, representative dense packing or a scientific finding.
Original Card knowledge and six protected input files remain unchanged. The old
Card-to-scene mapping is refused after synthetic replacement.

Three small 3,983-atom/eight-structure cases pass, one per host. Electron pilots
then pass at 15,932 atoms/eight structures and 63,728 atoms/eight structures before
all three receive the same largest case:

| Exact profile; 63,728 atoms × 32 structures | Scale checks | Summed process-tree RSS peak | Guarded complete trial |
| --- | --- | --- | --- |
| Qt, requested default sandbox, ANGLE/Vulkan | 7/7 | 2,708,799,488 bytes / 2.523 GiB | 34.022 s |
| Electron, explicit lab-only sandbox bypass, ANGLE/Vulkan | 7/7 | 2,641,469,440 bytes / 2.460 GiB | 26.919 s |
| Tauri, requested default sandbox, default graphics selection | 7/7 | 2,815,524,864 bytes / 2.622 GiB | 33.516 s |

These single trials are not a speed or unique-physical-memory ranking. Different
graphics, security, automation, caches and startup conditions remain. Summed RSS
can count shared pages repeatedly. The results do not demonstrate a whole-app
RAM advantage for Tauri, nor an inherent large RAM penalty for Electron.

Each largest case sends exactly **24,471,552 coordinate bytes** as planar
float32/angstrom arrays, observed at the owned public channel's `send` boundary.
The coordinate chunks contain 16,059,456 and 8,412,096 bytes. Box arrays remain
separate; no coordinate JSON is counted as binary delivery. Measurements count
actual buffers without changing them and are not network throughput, GPU bytes
or an end-to-end zero-copy claim.

Public `movie.capture_baseline_async()` and `movie.seek_async()` acknowledge the
primary canvas while navigating structure indices **0 → 31 → 0**. Draw-ack round
trips are approximately 82–176 ms in this Electron trial, 112–229 ms in Qt and
250–366 ms in Tauri. They include dispatch, scheduling, frame application and
the return path; they are not FPS, isolated GPU time or physical presentation.
The small cases and largest cases also accept local float/dock actions while
Python's preparation request is still pending. Recorded action times include
automation overhead and are not a usability-budget acceptance.

All eight successful scale cases preserve their before/after source/input hashes
and close with no owned survivors. Independent receipt checks verify descriptor
units/dtypes/layouts/shapes, exact byte counts and structure indices, layout
acceptance and resource limits. The earlier failed buffer-classification control
is retained: it read the flat documentation example, while the actual descriptor
is nested in `structural_arrays`. That was a measurement error, not failed
binary delivery; its corrected small control passes.

## Resource and measurement limits

Trials run sequentially, with at most four CPU affinity slots, native pools of
one, a 4 GiB sampled summed-RSS ceiling and at least 16 GiB host-available RAM.
The GPU observer stops its own tree above 2048 MB of per-GPU summed framebuffer
usage reported by `pmon`, below 20% selected-GPU available memory, above 80 Celsius
or on unavailable observation. A tiny real-context control lowers the framebuffer
threshold to 1 MB, triggers the expected stop and leaves no owned descendant.
An independent missing-utility control also stops its own sleeping command when
`nvidia-smi` is unavailable. These controlled stops are expected, not passing
molecular runs.

These are sampled controls, not reservations or enforced cgroups. `pmon` reports
MB; the device memory query labels MiB. Raw values retain their reported units.
Earlier @1 observation files mislabeled the raw `pmon` column `_mib`; the new
@2 format corrects the field and leaves originals unchanged. A process created
during device queries can initially be unattributed; the observer refreshes its
owned tree and checks PID/creation time rather than declaring that process foreign.
The [NVIDIA CLI documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
also warns that output compatibility is not guaranteed. This is an owned
experiment observer, not a general resource-management service.

Whole-device power/temperature includes background and unassigned activity.
Short synthetic runs do not establish attributable energy, thermal efficiency,
sustained rendering, an exclusive GPU reservation or a long-run memory bound.
No thermal winner is declared.

Applicable local checks pass: repository-wide Ruff formatting and lint, the local
MOLI governance gate, parsing all seven JavaScript modules, and independent
receipt checks for all eight successful scale cases. These check development
tools and documentation; no full scientific-suite or hosted-CI result is claimed
for this isolated increment.

## Provider follow-up and next decision

Use the existing draw barrier; do not substitute `on_frame_change()`, which
explicitly reports Python acceptance rather than rendering. The consumed
`data_plane_architecture.md` flat chunk example differs from current
`structural_arrays` envelopes; request a provider documentation correction under
the existing embedding/host work, with exact source links and this control.

The remote service freezes buffers into immutable `bytes` before asynchronous
socket delivery. That lifetime boundary is observed source behavior, not a
defect or an end-to-end zero-copy promise. The current Viewer materializes every
selected structure. Its existing [#55](https://github.com/uibcdf/molsysviewer/issues/55)
owns future windowed/lazy residency and its public semantics. Heavy trajectory
readers and native kernels retain their MolSysMT/Viewer owners; this probe adds
no scientific Rust parser, direct private Mol* inlet or alternate scene authority.

For future scale qualification, use a genuinely large public system and varied
conformations on qualified native platform sessions, with repeated runs and an
agreed workload budget.
Attribute preparation, copies/residency, transport and draw cost before adding a
Rust fast path. Production embedding (#368), Electron security/packaging and
future-engine WebGPU receiving remain explicit delivery or reassessment work;
they do not require extending this exploratory host comparison. The
accepted 0.15.0 functional milestone and deferred independent review are unchanged.

Local receipts and failed controls are retained in
`recovered_work/checkpoint_recovery_20261106/interactive-gpu-scale-20261113-1/`.
Owner #154; review at the first host decision or provider/engine change. Keep
useful evidence and remove only owned disposable profiles, credentials, extracted
diagnostic tools and completed scratch after final use. Provider code is unchanged.
