# Standalone host experiment

Development-only work for [Sabueso #154](https://github.com/uibcdf/sabueso/issues/154),
coordinated with [MolSysViewer #276](https://github.com/uibcdf/molsysviewer/issues/276)
and [#368](https://github.com/uibcdf/molsysviewer/issues/368). This is not an
application release, supported consumer API, installer or final researcher UX.
Do not expose its services to a network or package its automation features.

The same React/TypeScript/Dockview build and separately running Python service
are used by thin Qt, Electron and Tauri windows. Python owns the original Card,
native exploration results and saved reading. The molecular iframe is the
provider's unmodified experimental `RemoteSessionService(render_on="client")`
client, with one public `MolSysView` and its existing binary channel. No Mol*
scene, molecular parser or scientific protocol is reimplemented here. The
preview provider surface still needs owner acceptance before production use.

## Inputs and real checks

`prepare.py --output <new-directory>` creates an offline public TcTIM/1TCD
cohort using the existing structural-context example. It copies source notices,
checks the existing declared correspondence, verifies atom ordering through
MolSysMT and records input hashes. Water or coordinate-only groups acquire no
protein identity. This bounded source mapping does not establish arbitrary
structure correspondence. It creates no SourceAssertion or Evidence.

The shared `run_host.mjs` journey checks an actual drawn molecular model,
original source navigation and exact Back, native saved/reopened reading,
source annotation to molecular selection and actual molecular pointer picking
back to its captured context. It exercises twenty float/dock/hide/show cycles,
camera/selection and iframe lifetime, one keyboard layout action, an independent
View whose close preserves the first, and refusal of stale source mapping after
replacing/reindexing the model. Input and probe hashes are checked again afterward.
`--quick-calibration` runs zero repetition cycles and cannot qualify the twenty-cycle
check. Layout JSON length records serialization only; saved layout restoration,
separate native windows and application crash/restart recovery are not tested.

Qt and Electron use the same small renderer CDP adapter; full browser-context
automation was not supported by Qt. Tauri uses the optional embedded WebDriver
plugin for observation, a fixed all-frame browser diagnostic script, and XTest
input on the experiment's private Xvfb display. Its embedded driver's scripted
pointer events are not used as native picking evidence. This adds different
automation overhead; journey wall times are not a host-performance ranking.
The observer never fabricates molecular events or changes provider scene state.

All hosts record actual WebGL renderer and browser WebGPU adapter availability
without enabling experimental WebGPU flags. Browser support does not mean the
consumed MolSysViewer/Mol* uses WebGPU. Canvas checks and screenshots are separate
from hardware acceleration, native platform qualification or human acceptance.
Qt additionally captures its actual QWidget composition: a CDP screenshot alone
does not prove final Qt composition. Tauri's browser diagnostic samples pixels
until the first nonuniform draw, then stops pixel readbacks.

## Controlled development execution

Use the repository's shared Python 3.14 editable environment, verify the three
component import paths, and read the shared-resource policy before running.
The Node project has its own exact lockfile. Build with `npm ci`,
`npm run typecheck` and `npm run build` in this directory. These are development
prerequisites, not a public Sabueso installation route.

Select a fresh owned output root outside the probe tree, then prepare the inputs
and run **one** host at a time through `run_bounded.py`. For example, from the
repository root, after defining task-specific paths:

```bash
python devtools/standalone_probe/run_bounded.py \
  --output-root "$probe_results" --cpus 4 qt-trial -- \
  node devtools/standalone_probe/run_host.mjs \
  --host qt --python "$probe_python" \
  --inputs "$probe_inputs" --output "$probe_results/qt-trial"
```

Use `--host electron` for Electron. The runner owns its Xvfb display and child
processes and expects Linux; Windows and macOS are not qualified by this tool.
The local observer samples all discovered owned descendants, limits CPU affinity
to at most four cores, sets native pools to one thread, lowers priority, stops
above 4 GiB summed RSS or below 16 GiB host available RAM, detects owned swap,
sets an elapsed ceiling and terminates only its own processes. Check load,
memory pressure, swap activity, scheduler applicability and other jobs first.
It is an observer, **not a resource reservation or enforced memory cgroup**;
short-lived descendants and transient peaks can escape sampling. Summed RSS can
double-count shared pages; it is not PSS or unique physical memory. Never treat
these limits as permission to ignore host pressure.

Normal Chromium/WebKit sandbox startup is a separate gate. A sandbox failure must
be retained as a failed default-profile observation. `--lab-no-sandbox` is an
explicit option for a trusted local calibration and is never an automatic fallback
or a deployable solution. Do not change global AppArmor, namespace policy, SUID
permissions or drivers to make this experiment pass. The optional
`--system-sandbox-helper` trial uses only an already protected root-owned helper;
requesting that profile does not prove the runtime accepted it.

For Tauri, build the Rust crate using `Cargo.lock`, one compiler job, the same
resource observer and native WebKitGTK/GTK prerequisites. The `webdriver` feature
enables a loopback automation server and must stay out of any production build.
This probe's remote-origin capability grants only that development plugin.
There are no scientific Rust kernels or Python embedding through PyO3 here.
The thin host loads the exact same Python service and web workspace.

```bash
cargo build --locked --manifest-path devtools/standalone_probe/tauri/Cargo.toml \
  --features webdriver --jobs 1
```

Run with `--host tauri --tauri-binary <built-probe>`. An optional
`--tauri-native-root <owned-extracted-sysroot>` selects locally extracted native
libraries/process helpers for that child only. No system package installation or
configuration change is performed by the runner. A locally provisioned sysroot
is a development profile, not evidence for an ordinary installed Linux desktop.
In Ubuntu's WebKitGTK release build, auxiliary-process paths remain compiled-in:
`WEBKIT_EXEC_PATH` is honored only in developer-mode builds. Local extraction can
therefore compile this host while failing runtime process startup. Do not patch
the browser binary or claim successful Tauri rendering from that build alone.
Do not infer Tauri results from a plain WebKit window or mocked browser API.

## Evidence, scope and cleanup

Each fresh result directory retains an observation JSON, screenshots, host logs,
backend cohort, original saved reading and public input manifests. The resource
observer retains its log and sampled process-tree data. The private bootstrap is
mode 0600 and removed on normal/error shutdown; raw profiles, logs and backend
cohort can contain local paths or endpoint material. Review and sanitize before
sharing. The committed report contains only public/synthetic inputs and sanitized
technical facts. Optional XR rejection is recorded, never hidden by granting
unneeded XR permission. Passing selected journey checks does not suppress those
browser errors or imply product qualification.

Owner: Sabueso #154. Retain useful observations, lockfiles and the input cohort
through the first reviewed host decision; reassess after a provider/engine change.
After the last needed run, remove only owned bootstrap/profile/cache/scratch paths
and confirm no owned descendants remain. Never delete caller outputs, other
sessions, worktrees or unrelated temporary directories. `node_modules`, `dist`,
Rust targets, downloaded packages and extracted native prerequisites are disposable
only after their final verification use. Keep retained evidence outside this source
directory so its before/after hash check remains meaningful.
