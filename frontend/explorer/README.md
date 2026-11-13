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
Card; `--reading /path/to/reading.json.gz` opens an existing original exploration
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
save the surrounding Deck workspace. No molecular panel or identifier acquisition
is delivered at this checkpoint.

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
