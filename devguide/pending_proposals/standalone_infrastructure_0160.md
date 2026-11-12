---
summary: Compare standalone hosts and propose a Python-owned, portable web workspace with live MolSysViewer integration.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-12
verification: documentation_review
area: [architecture, standalone, visualization, interoperability]
---

# Standalone infrastructure evaluation for 0.16.0

## Requirements and recommendation status

The maintainer confirms three constraints: a Python backend, embedded live
MolSysViewer representations, and a standalone user experience. Preserve the
[accepted experience](interactive_exploration_0160.md#researcher-controlled-assistant-experience--2026-11-12),
researcher-composable panels and replaceable infrastructure.

**Recommendation for the first integration prototype:** a thin PySide6/Qt
WebEngine host, a reusable TypeScript web frontend, and Python-owned Knowledge
sessions with a provider-owned live molecular adapter. Evaluate React with
Dockview's free core as the primary workspace candidate; Svelte with the
framework-neutral core remains an alternative. This is a proposed engineering
choice, not maintainer acceptance, dependency adoption or implemented compatibility.

Owner #154. Retain this evaluation through the first stack decision, then carry
accepted contracts and measured limits into the maintained implementation plan.

Earlier local-browser-first and Svelte suggestions were provisional. Explicit
standalone priority now favors testing the existing Qt/Python direction first;
the newly reviewed panel-library support favors evaluating React's direct
binding. These are integration-cost judgements, not measured speed or memory wins.

## Distinct choices

The native window host, UI framework, panel manager and Python transport solve
different problems. Qt can host the same web interface as another native shell;
it does not require writing every scientific panel as a QWidget. Keep file/window
functions at the host boundary and scientific operations in ordinary Python APIs.

| Host | Advantage for this use case | Work/cost still due | Proposed disposition |
| --- | --- | --- | --- |
| PySide6 + Qt WebEngine | Python-native application lifecycle and existing live Qt/Chromium experience in MolSysViewer | Native libraries, GUI event-loop/thread ownership, coherent Qt packaging and exact platform qualification; generic consumer embedding remains to qualify | First prototype candidate |
| Electron + Python process | Chromium-based standalone web workspace with native-window APIs; avoids Qt-specific runtime dependencies | Maintain Node/Electron plus Python, process ownership and a new live adapter; packaging and resource costs need measurement | Principal alternative if Qt integration is limiting |
| Tauri + Python sidecar | Native shell using system WebViews; can package an external Python service | Rust/shell layer and Python distribution, platform-specific WebViews, new adapter and WebGL/picking qualification | Later comparison candidate, aligned with Viewer #276 |
| pywebview + Python | Small Python-facing host API and a JavaScript/Python bridge | Renderer/backend varies by platform; selecting Qt inherits its native dependencies; Viewer integration remains new | Secondary option without a demonstrated advantage over the direct Qt route |
| Local browser application | Reuses the frontend and keeps native host code small; useful for development and later remote adaptation | Browser/process lifetime, file integration and desktop presentation need deliberate design | Development/alternate host; dedicated window is the proposed first product entry |

These are documented mechanisms and qualitative tradeoffs. No comparable
Sabueso host benchmark, installer measurement or native-platform receiving exists.
MolSysViewer/scene-data cost can dominate shell overhead; do not infer whole-app
memory or startup from a shell's advertised size.

Primary references: [Qt WebEngine](https://doc.qt.io/qtforpython-6/overviews/qtwebengine-overview.html),
[Electron process model](https://www.electronjs.org/docs/latest/tutorial/process-model),
[Tauri WebViews](https://v2.tauri.app/reference/webview-versions/) and
[sidecars](https://v2.tauri.app/develop/sidecar/),
[pywebview architecture](https://pywebview.flowrl.com/guide/architecture) and
[renderers](https://pywebview.flowrl.com/guide/web_engine.html).
In particular, Tauri uses WebKit on Linux/macOS and WebView2 on Windows; an
existing Chromium observation does not establish those new renderer paths.

## What MolSysViewer actually supplies

Read-only source review at clean `0dcdd6ce574d3c99483480cb38c16c1e3cc4782f`:

- [Standalone surfaces](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/docs/content/developer/standalone_surfaces.md)
  distinguishes the persistent live Qt/Python host from static HTML export.
  Rendering an export is not a substitute for a live scientific session.
- [The factory](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/standalone_qt/application.py)
  constructs a complete window and returns app/window/webview/path/title. It
  does not by itself qualify mounting a live molecular panel in an unrelated
  application workspace. Avoid treating reparenting its widgets or replacing its
  page as a supported embedding contract.
- [QtViewChannel](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/standalone_qt/view_channel.py)
  connects a persistent Python View to live runtime messages. Provider-owned
  scene identity, binary payload transport, readiness and disposal must survive
  integration; importing internal helpers is not a durable consumer contract.
- [Supported-environment notes](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/standalone_supported_environment.md)
  record bounded Linux observations and pending native/installed scope. Qt is
  still experimental for Viewer 1.0. Sabueso gains no support claim from those
  observations. [#276](https://github.com/uibcdf/molsysviewer/issues/276) remains
  an open Qt/Electron/Tauri evaluation, not an approved migration.

Outside-checkout metadata in the shared Python 3.14 environment reports editable
MolSysViewer `0.24.0+409.g0dcdd6ce`, editable MolSysMT
`0.23.0+904.gff25f1202`, PySide6 6.11.2 and anywidget 0.11.0. FastAPI and
pywebview are absent. These are metadata observations only: no scientific import, GUI,
installer, graphics or cross-component execution is qualified by this review.

## Workspace and frontend choice

[Dockview](https://dockview.dev/docs/overview/introduction/) documents docking,
tabs, floating groups, popout windows and layout serialization. Its direct React
binding gives React/TypeScript a useful first-prototype advantage. Svelte can
use the JavaScript core through an application-owned component adapter; the
review does not establish incompatibility or a measured cost difference.

The current [feature/licence matrix](https://dockview.dev/docs/overview/licence/)
lists floating panels and layout save/restore in the free MIT core. Advanced
spatial keyboard navigation/docking and layout undo history are Enterprise
features. Evaluate actual accessibility needs and free-core APIs before adoption;
no commercial extension, trial or payment is authorized. Keeping a panel's
scientific context fixed is Sabueso behavior, separate from vendor "pinned tabs".

Use the panel manager for layout and lifecycle, not scientific state. Keep
original Card/read results in Sabueso, molecular/camera state with Viewer, and
workspace geometry in a versioned presentation record. Moving/docking a panel
must preserve or deliberately restore its rendering owner; do not reload the
whole page or recapture knowledge on every move. Browser popout support does not
automatically establish Qt/Electron native-window support.

Golden Layout is another candidate, but its
[current guide](https://golden-layout.github.io/golden-layout/) advises building
from source because npm releases are old, and its
[popout contract](https://golden-layout.github.io/golden-layout/popouts/) leaves
cross-window state propagation to the consumer. Start by qualifying one panel
manager rather than building the same application around several libraries.

## Python transport and portability

A mandatory HTTP server is not required by the Python-backend constraint.
Start the Qt candidate with an explicit local message boundary and ordinary
Python session operations; use the provider-approved molecular connector.
FastAPI/aiohttp remain possible later HTTP/WebSocket adapters if required by
the selected integration or remote host. Avoid adding a server solely because
the presentation uses web technologies.

Keep small versioned commands/results, capture/selection references and native
quantity codecs independent of Qt, React and a server framework. Long-running
operations must not block the UI; qualify their bounded scheduling and supported
cancellation with the scientific/connector owners. Future infrastructure controls
execution placement and resources. Native dialogs/window actions and molecular
transport each retain an adapter with an explicit lifetime.

This preserves a practical route to Electron, Tauri, browser/Jupyter hosting or
future provider rendering changes. A migration still requires work and exact
receiving; shared web technology alone guarantees no future compatibility.

## Proposed provider handoff

Consumer need under #154: **a supported live embedding surface for external
standalone Python applications**. This is an improvement request, not a newly
reproduced rendering bug. Desired owner review:

- Mount a molecular runtime within a host-supplied workspace/container while
  retaining one Python View authority and its declared model/source context.
- Expose readiness, selection/click events, resize, scene continuity and disposal
  through a small public integration surface, preserving binary transfer.
- Specify what survives in-page docking and what requires a distinct endpoint
  for a separate native window. Keep unpublished/private protocol details owned
  by Viewer rather than copied into Sabueso.
- Receive one public molecular model with the real runtime, exact bidirectional
  selection, repeated resize/move/open/close and a surviving independent view.

Exact API and whether to extend an existing host belong to MolSysViewer. Prepare
or update the provider issue when the candidate is selected, cross-link #154 and
#276, and route a shared MolI contract to its owner if needed. This review is the
local maintainer handoff; no provider issue or shared protocol is published here.

## Bounded decision experiment

1. Agree the Qt/web candidate and public embedding scope; retain Electron as
   the alternate host instead of building several full applications.
2. Use one public model and a small real Card/Deck reading. Exercise topic
   selection, exact molecular picking/source navigation, a floating text panel,
   dock/resize, context following/keeping and original saved reopening.
3. Check actual drawn content, event-loop responsiveness, quantities/references,
   retained camera/selection and callback/process cleanup. Measure complete
   Python/renderer resources under the shared-machine policy. Native visible
   rendering and software/headless evidence keep distinct scopes.
4. If the owner-approved Qt route is usable and maintainable, accept the first
   stack with its exact versions and platform limits. A substantive Qt/bridge
   limitation triggers a same-journey Electron comparison. Do not re-evaluate
   every host on each small change or select by a visually attractive mockup.

No provider change, dependency install, runtime prototype, benchmark, paid
service, release or platform-support expansion is performed by this document.
