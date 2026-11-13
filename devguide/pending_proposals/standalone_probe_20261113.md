---
summary: Bounded development host observations, provider findings and a controlled Tauri/Rust/Python evaluation route.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: bounded_development_experiment
area: [architecture, standalone, visualization, interoperability]
---

# Standalone experiment: scope and receiving

This is the first phase's receipt. The later
[NVIDIA/scale follow-up](standalone_gpu_scale_20261113.md) adds new, separately
scoped hardware/device and synthetic-load observations. Its existence does not
turn the original software-profile timings into a hardware comparison.

Owner #154; provider coordination in [MolSysViewer #276](https://github.com/uibcdf/molsysviewer/issues/276)
and the delivered [live embedding request #368](https://github.com/uibcdf/molsysviewer/issues/368).
The maintainer explicitly requests sharing this experiment's conclusions with
MolSysViewer. Consolidate useful results in the existing host-evaluation issue;
keep observations, hypotheses and untested scope distinct. A host choice is still
open. No provider patch, production dependency adoption, package or release is
authorized by an exploratory result.

The [probe and execution method](../../devtools/standalone_probe/README.md)
define the exact real journey, input correspondence and lifecycle checks.
It runs outside the installed scientific library. Source baseline is Sabueso
`5516b6d0e74850b70766793383f0ef7aaec76236`, with the new probe identified by
per-file digests and its eventual Git checkpoint. All three windows use the
same compiled web workspace and separate Python service. Viewer owns the actual
runtime, selection/camera authority and existing binary channel. Public TcTIM
P52270/1TCD is the initial cohort, with 3,983 explicitly mapped coordinate atoms;
this is a small integration system, not a massive-structure benchmark.

## Current observations and limits

The final Qt, Electron lab and Tauri journeys each pass all **16 selected
checks**, including twenty retained-panel cycles, original SourceAssertion open,
exact Back, native saved/reopened reading, keyboard layout action, independent
View close and a model-reindexing refusal. Both preserve one original iframe
load, one mount, zero unmounts and one client registration across the repeated
layout operations. Neither makes external scientific requests. Before/after
checks preserve all protected input hashes and the probe source/build hashes.
Optional XR rejections remain recorded; product qualification is explicitly false.

| Exact development profile | Selected checks | Guarded elapsed | Sampled summed-RSS peak |
| --- | --- | --- | --- |
| Qt 6.11.2, requested default sandbox, software Xvfb | 16/16; 20 cycles | 155.863 s | 2,298,105,856 bytes (2.14 GiB) |
| Electron 45.3.1, explicit lab-only `--no-sandbox`, software Xvfb | 16/16; 20 cycles | 135.052 s | 1,734,729,728 bytes (1.62 GiB) |
| Tauri 2.12.5 / system WebKitGTK 2.52.6, requested default sandbox, software requested on Xvfb | 16/16; 20 cycles | 75.663 s | 2,116,530,176 bytes (1.97 GiB) |

Actual browser user agents report Chromium 140.0.0.0 for Qt and
156.0.8078.96 for Electron. Both use a 1280 × 900 content viewport at device-pixel
ratio one; Tauri has the same viewport/ratio and a WebKit user agent. The same
opaque Viewer runtime asset has SHA256
`c251e22e920c1d780bfbed755927c48a4888b353639d5341157915be2ea1e9ff`;
it was hashed as an artifact, never inspected as source. The declared annotation
selects atoms 700–709. The Chromium center pick yields atoms 949–955, explicitly
mapped to UniProt position 128 through retained RCSB source support; Tauri's
native pointer yields atoms 943–948 at position 127. Each retains its actual
source mapping; no result claims to have picked the annotated position 96 or to
establish pixel-identical picking across renderers/input backends.

These totals include backend setup, the same scripted reading/save/picking and
layout journey, the second View and shutdown; they are **not a host-performance
ranking**, FPS, isolated renderer cost or energy measurement. Different graphics
backends and sandbox profiles, a single run per profile, caches and shared-host
activity and different automation preclude that comparison. The Tauri-only final
driver change closes the native window through WebDriver before terminating the
cohort; the common frontend, Python service, original inputs and Chromium driver
are unchanged from their completed runs. Each cohort runs sequentially with four CPU
affinity slots, native pools of one, a 4 GiB owned summed-RSS ceiling and 16 GiB
host-available floor. No owned swap, resource-stop or surviving descendant is
observed. The smallest recorded host availability remains above 49 GiB.

Both Chromium browsers expose WebGPU in a secure loopback context but return
**no adapter**; the tested Tauri/WebKitGTK build does **not expose the API**.
These are scoped observed results, not a statement about
hardware WebGPU support. The real molecular canvas is WebGL 2.0. Selected Qt
native QWidget screenshots and Electron screenshots show the actual molecular
view and original Knowledge reading; Tauri's WebKit screenshot also shows the
actual model. Screenshots are retained with the receipt. Tauri's reading-context
panel refresh is asynchronous; the screenshot is not a UI-latency acceptance.

Tauri's reported WebGL renderer is `Apple GPU` on this Linux host. The
[consumed WebKit source](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.6/Source/WebCore/html/canvas/WebGLRenderingContextBase.cpp)
returns that literal for `UNMASKED_RENDERER_WEBGL`; it does not identify the
physical device or prove software/hardware acceleration. Use additional native
diagnostics before a GPU comparison. No fingerprinting workaround is applied.

An early Tauri calibration passes the sixteen short-journey checks but fails its
resource observer because one descendant remains at command return; the observer
cleans only that owned process. The launcher now closes the actual native window
through WebDriver and gives WebKit time to dispose before process termination.
The corrected full twenty-cycle receipt has all native children exiting normally
with code zero and no surviving descendant. This is a probe lifecycle correction,
not a newly established provider defect.

Earlier failed
calibrations remain retained: missing Xvfb GLX driver discovery, unsupported
full-browser automation on Qt, an Electron launcher's top-level-await deadlock,
and insufficient Enter-key injection were experiment setup defects. A saved
reader's intentional historical banner is not a scientific result mismatch.
An attempted `view.clear()` control used a nonexistent public method; the
corrected control replaces/reindexes the model using public loading. None is
being reported as a provider defect.

Default Electron startup failed;
the already protected system Chrome SUID helper did not repair this npm Electron
profile. No global security configuration or permissions were changed. The
kernel namespace restriction and Chromium diagnostic are observed; attribution
to a particular AppArmor rule remains a hypothesis without the denied audit log.

Both Chromium runtimes have been observed using software renderers: Qt selected
ANGLE/Mesa llvmpipe while Electron selected ANGLE/SwiftShader. Thus even similar
software flags do not establish identical graphics backends. Their timings and
summed process-tree RSS must not rank the production hosts. The runtime context
does expose NVIDIA hardware; absence of an owned native desktop session and the
deliberately software Xvfb profile limit these runs. No native NVIDIA, Wayland,
Windows, high-DPI/multimonitor or installed-distribution receiving is claimed.

The selected journey and optional browser errors are separate. Both Chromium
profiles report optional XR support rejection in the embedded frame while normal
3D and selection work. Mol* 5.4.1's
[XR support check](https://github.com/molstar/molstar/blob/v5.4.1/src/mol-canvas3d/helper/xr-manager.ts)
does not catch that promise rejection; the
[5.13.0 implementation](https://github.com/molstar/molstar/blob/v5.13.0/src/mol-canvas3d/helper/xr-manager.ts)
already catches failures and marks the optional feature unavailable. This is a
provider receiving/backport consideration, not a new upstream-unfixed claim or
authority to upgrade Viewer's engine. Granting unnecessary XR permission would
conceal the integration finding.

## Tauri native prerequisite observation

The actual thin Rust/Tauri host compiles with Tauri 2.12.5, Wry 0.57.2 and
embedded automation plugin 1.5.1. One compiler job peaks at approximately
1.49 GiB summed RSS during the initial dependency build; compilation is not an
application-memory result. Public Ubuntu prerequisites (172 new packages,
approximately 80 MB download/329 MB installed content in the APT simulation)
were SHA256-verified against local package metadata and extracted only into an
owned directory. No packages were registered, maintainer scripts run, services
changed or system libraries overwritten. Local developer-library symlinks reuse
already installed runtime libraries where needed.

In the earlier extraction-only profile, the correct executable starts but
WebKitGTK aborts before a molecular draw:
it seeks `WebKitNetworkProcess` at its compiled-in system path, absent on this
machine. The release build ignores the requested local `WEBKIT_EXEC_PATH`;
[2.52.6's process-path source](https://github.com/WebKit/WebKit/blob/webkitgtk-2.52.6/Source/WebKit/Shared/glib/ProcessExecutablePathGLib.cpp)
guards that override with `ENABLE(DEVELOPER_MODE)`. This is an environment/
relocation limitation, not a reproduced Tauri graphics crash, WebGPU failure or
evidence that Tauri cannot host Viewer. That extraction-only profile did not
qualify the native journey. The browser binary was not patched and no global
paths/security settings were changed to bypass its compiled helper paths.
The local build/path/icon/linker setup failures are retained separately from this
actual runtime limit. The later system-runtime journey above supersedes that
environment blocker and qualifies only the stated development checks.
The maintainer has explicitly authorized the reviewed minimal runtime command
`sudo apt-get install --no-install-recommends libwebkit2gtk-4.1-0` (58 new
packages, approximately 49 MB download/172 MB installed, no upgrades/removals).
The noninteractive attempt stops at sudo's required interactive authentication.
The maintainer then completes that exact installation in a human terminal:
58 new packages, no upgrades/removals, no required service/container restarts.
Post-install checks validate package configuration and dependency consistency.
The actual Tauri journey passes against the ordinary system runtime, preserving
the earlier failed extraction-only profile. No extra installation permission is
needed within that already approved scope; no security/driver configuration is
changed.

## WebGPU: current workload versus future route

Chromium's [April 2026 report](https://developer.chrome.com/blog/new-in-webgpu-147-148)
extends Linux WebGPU to modern NVIDIA drivers on Wayland. That supports evaluating
the Chromium route; it does not establish acceleration on every Electron build,
driver, X11 session or fallback configuration. Measure `navigator.gpu`, actual
adapter availability and the workload's real renderer separately, with no unsafe
WebGPU flags presented as stable support.

The consumed Viewer uses Mol* 5.4.1/WebGL. Meanwhile Mol*'s development tree
[`dabbf29f952880a034a9637e28c9844e3ae73d9f`](https://github.com/molstar/molstar/blob/dabbf29f952880a034a9637e28c9844e3ae73d9f/.v6/changelogs/plugin-default-webgpu.md)
records WebGPU-first selection where adapter features suffice, with WebGL
fallbacks. This is concrete future-engine work, not compatibility established
for the consumed Viewer or a selected Sabueso upgrade.

WebKitGTK is not inherently software-only: its
[graphics architecture](https://docs.webkit.org/Ports/WebKitGTK%20and%20WPE%20WebKit/Graphics.html)
uses accelerated paths. A Safari WebGPU claim does not establish GTK-port support,
nor do general reports of Wayland/X11 failures reproduce a defect in our exact
profile. Record the installed WebKitGTK build, display server, renderer, driver
and default versus experimental features. The locally available Ubuntu packages
are WebKitGTK 2.52.6; upstream 2.54.2 is a separate version. Python GPU inference
is independent of browser WebGPU and remains possible with any host.

## Tauri/Rust/Python hypothesis and next discriminating tests

The maintainer proposes Tauri as the native shell, Rust for high-throughput binary
data and an isolated Python analytical engine. Evaluate this design, without
assuming lower total RAM, zero-copy transfer, zero latency or better thermal
efficiency. Rust does not itself provide those properties. Python and the actual
molecular scene can dominate shell memory.

1. First measure Tauri with the existing Python/MolSysViewer binary path, fixed
   source/model, style, camera, viewport and lifecycle. This isolates the host
   choice. Compile one job at a time under the resource observer; use an owned
   local native sysroot where possible, not a global package/configuration change.
2. Attribute an actual bottleneck before introducing another trajectory reader.
   MolSysMT already contains private Rust/PyO3 kernels. Reuse its public Python
   capabilities and coordinate any needed Rust-facing API with that provider;
   its private crate is not a consumer contract. Keep scientific parsing,
   coordinates, units and frame semantics with their owners.
3. If justified, compare the baseline with a provider-supported bounded binary
   inlet fed by Rust. Measure read/decode, transfer, receive, provider update and
   observed draw independently. A Rust-to-JavaScript ArrayBuffer microbenchmark
   does not establish delivery to the real MolSysViewer canvas. Backpressure,
   bounded buffers, cancellation, per-frame identity and unit declarations are
   prerequisites; never transfer a huge trajectory as JSON.
4. Treat gRPC/local IPC as transport candidates. PyO3 embeds Python in a process
   and does not itself provide process/crash isolation. Keep long computations
   away from GUI ownership; Sabueso retains Knowledge and delegates geometry,
   simulation and project/AI reasoning to their owners.
5. Increase public or clearly synthetic workload size incrementally after a small
   run establishes peak memory. Compare total process-tree memory and useful
   work per time, not just the Rust shell. Report sampled RSS's shared-page and
   transient-peak limits. No measurements are resource reservations.
6. Thermal/energy comparisons require a repeatable hardware-accelerated scene,
   accessible counters, controlled duration and background-load observations.
   Whole-host temperature on a shared machine is not attributable energy. If
   counters or a suitable controlled session are unavailable, state the missing
   measurement rather than infer efficiency from language or shell size.

The first host decision must include supported/default security startup,
production rendering and native/platform evidence, maintenance/distribution cost,
provider-supported embedding and future engine receiving. Keep the portable
frontend and service contracts replaceable whichever host eventually wins.

## Evidence retention

Applicable local checks pass: root Ruff format/lint, local MOLI governance,
TypeScript type checking and frontend build, all JavaScript entrypoint syntax,
Rust formatting and the actual Tauri native build, scoped Markdown targets/anchors,
and Git whitespace checks. The Node lockfile audit reports no known advisory.
An independent tiny elapsed-limit control stops only its own sleeping parent/
child processes, records `elapsed ceiling` and leaves no survivor in 1.079 s.
The three final real journeys supply the selected integration checks; the unchanged
scientific library does not require a new full offline suite for this isolated
development tool. Hosted CI/governance and installed/native-GPU qualification
remain separate under the [deferred recovery record](deferred_ci.md).

Owned local receipts live under
`recovered_work/checkpoint_recovery_20261106/interactive-host-comparison-20261113-1/`.
Owner #154; review at the first host decision or provider/engine change. Keep
original inputs, hashes, failed profiles and useful screenshots. Remove only
owned disposable credentials/profiles/cache/scratch after their final use;
preserve other sessions and caller outputs. The public provider report excludes
local paths, endpoint capabilities, private environment configuration and pilot
content. Functional 0.15.0 acceptance, #192's explicit deferral and the deferred
independent researcher trial are unchanged.
