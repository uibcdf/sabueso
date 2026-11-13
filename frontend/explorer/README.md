# Explorer frontend development

This is the optional Qt-hosted Card/Deck development application under Sabueso #154.
The [living plan](../../devguide/pending_proposals/interactive_implementation_0160.md)
owns implemented versus remaining product scope. This is not a released GUI or
a verified public installation route.

Reuse the shared editable Python 3.14 environment. The frontend's exact lockfile
contains React/TypeScript/Dockview and build tooling, with no Electron/Tauri
runtime. In this directory, `npm ci`, `npm run typecheck`, and `npm run build`
produce `sabueso/explorer/_assets/`. The compiled files and dependency licence
notices ship as package data; frontend build source is included in the sdist.
Node is not required to run the compiled application.

From a development checkout with the optional PySide6/aiohttp cohort provisioned:

```bash
python -m sabueso.explorer --output-directory /path/to/new-readings
```

Open a Card JSON through the file chooser. `--card /path/to/card.json` preloads a
Card; Open reading chooses an existing original file (plain/gzip/zstd), while
`--reading /path/to/reading.json.gz` preloads an original exploration
through its ordinary verifier. `--deck /path/to/deck.jsonl` opens the original Deck envelope; all three inputs
are mutually exclusive. This
requires an actual graphical session; the automated receiver owns its Xvfb.
No sandbox bypass or automatic source acquisition is introduced.

The light entry, topic index, local search, original item/source navigation,
exact Back, finite item/text pages, save/reopen and float/reset controls are
implemented. All natures use the existing Card readers. Scalar text is available
in complete 4,096-character pages; the Python-reader navigation footer is hidden
only in the UI preview. Original reader text and saved meanings are unchanged.
The Deck workspace preserves repeated occurrences, original metadata, literal
filters/order and exact Card/source/Deck return. Saving a Card reading does not
save the surrounding Deck workspace. The entry screen also provides explicit UniProt/PDB/SMILES/disease-ID queries.
They reuse `identity@1`; the initial SMILES route disables UniChem expansion.
PDB remains a structure record whose source-declared proteins require a separate
user query. Original decisions and acquisition traces stay inspectable. Return
to previous query restores the exact reading without fetching again. Query
history is in memory, with 32 retained return points; it is not a saved workspace.
Disease-name search is not offered without a candidate-search contract.

Card upload sends the selected file body directly. Never parse and reserialize
sealed Card JSON in JavaScript: it changes integer/float distinctions and large
integers, invalidating original quantity seals. Python verifies the original
Card. Stale application revisions, foreign page items, malformed actions and
tampered original readings are refused without silently choosing another scope.

The Qt window and the Python service have separate lifetimes. One worker
serializes Knowledge actions; the GUI remains independent. Optional imports go
through DepDigest. The presently received development floors are PySide6 6.11.2
and aiohttp 3.14.5; lower versions are not claimed by this checkpoint. These
floors do not prove every admitted OS/Python/driver combination.

`devtools/explorer_journey.mjs` receives the actual application using the existing
task-scoped CDP observer, normal Qt startup and a native QWidget screenshot.
Run it through the owned CPU/RAM/GPU observers as in the development probe.
Its explicit software request is not native GPU, molecular-rendering or platform
qualification. The private debug/capture switches are development receiving aids,
not normal product flows.

`devtools/resolution_explorer_journey.mjs` receives the actual four-entry UI
against declared frozen public clients through `explorer_fixture_service.py`,
which forbids network access. This is a development receiver, not a product
offline-mode or source-selection contract. Its source-call audit proves topic
and return actions do not acquire sources.

The explicit development-only `--experimental-model /path/to/model.bcif.gz`
option adds a live MolSysViewer panel alongside an initial `--card`, `--deck`
or `--reading`. PDB/ENT, mmCIF and BinaryCIF, optionally gzip-compressed, are
accepted up to 16 MiB encoded and 64 MiB decoded. These input-byte caps do not
bound parsed model RAM. MolSysViewer and MolSysMT own parsing, geometry,
transport and rendering, including their existing Rust code. Use the exact local
editable provider cohort recorded in the molecular receipt; no published minimum
or supported embedding contract is claimed until Viewer #368 is received.

The panel exposes actual initial readiness and can float/reset without replacing
its live viewport. It always says that correspondence with the current Card is
not established. The displayed name/digest describe the captured initial input,
not current model identity: the provider's own controls may replace the model.
No annotation-to-atom mapping, scientific identity, inferred structure or linked
selection is created by opening a file. Closing/reopening the panel, whole-scene
recovery and background suspension retain separate provider receiving work.
Optional-model startup failure leaves the original knowledge reading available.
The adapter owns an immutable temporary input copy until application shutdown.

`devtools/molecular_explorer_journey.mjs` receives real drawing, public camera
observation, three float/reset cycles, main-grid return and source navigation.
Its `--unavailable` control receives a rejected empty synthetic file without
losing the Card. Linux/Xvfb software drawing remains separate from hardware,
platform, long-session or large-model qualification. XR permission is delegated
only to the owned model iframe; there is no arbitrary external embed action.

Save layout stores only the current in-page presentation in
`presentation-layout.json` beside the chosen output readings. The versioned
64 KiB envelope admits the three received panels, finite layout data and the
exact Dockview cohort; it contains no Card, source query, model/camera state or
provider session token. On startup it can arrange a separately opened reading.
A missing model, unsupported version or invalid layout explains the fallback to
the default arrangement. Reset layout restores the default arrangement without
silently replacing the saved file; Save layout is explicit. An unreadable existing
presentation or symlink is never overwritten. Native popout windows are not
admitted by this first presentation format. The separate Knowledge and model
state is never reconstructed from panel labels.
