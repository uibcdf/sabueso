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
save the surrounding Deck workspace or its membership metadata. The Card file
retains its supplied captured Cards, under the existing original-reader format. The entry screen also provides explicit UniProt/PDB/SMILES/disease-ID queries.
They reuse `identity@1`; the initial SMILES route disables UniChem expansion.
PDB remains a structure record whose source-declared proteins require a separate
user query. Original decisions and acquisition traces stay inspectable. Return
to previous query restores the exact reading without fetching again. Query
history has 32 retained return points and can now be included by Save workspace.
Disease-name search is not offered without a candidate-search contract.

An ambiguous UniProt result or a resolved native preference can now offer exact
source-declared candidates/alternatives. An ambiguous SMILES result can offer
explicit PubChem CID record queries. These are new queries; they do not settle
the original identity or merge candidates. Available original organism/review/
length/observation context accompanies up to 32 visible follow-up buttons; the
full original report remains inspectable. Whole-workspace saving retains the
original ambiguity and exact return point, including the chosen record report.
The form folds after an accepted submission, its toggle describes its state,
and minimum reading height/outer scrolling preserve pointer access when query
controls need more vertical space. `--receive-candidates` adds the explicitly
synthetic ambiguity control to the source receiver; no identity between its CCO
control and the queried public compound is asserted.

For UniProt entry, Query scope optionally asks InterPro for source-mapped sites
or AlphaFold DB for prediction records, using the existing native enrichers.
The default remains identity-only; each choice creates a new capture with exact
Return to previous query. A candidate button stays identity-only. The bounded
Observed source access section shows original access outcomes/route/version/basis,
including fixture or failed access; native coverage/quality owns scientific scope.
No coordinate download or molecular mapping follows from an AlphaFold query.
`--receive-enrichment` adds these public fixture routes to the Qt receiver.

Native subject/object/entity links can offer Query referenced record as a new
explicit identity-only source query. Current-page item/revision admission stays
in Python; the browser supplies no destination override. UniProt/PDB/component/
PubChem/MONDO routes are finite, and pinned revisions, names, URLs or overloaded
ChEMBL references are refused. Original Card/Deck context stays in query return
history. MONDO obsolete-term choices similarly query a separately declared
replacement/consideration without rewriting the old term. The source-access
outcome summary stays visible even when identity resolves but another access fails.
`--receive-record-links --record-inputs <prepared-public-inputs>`,
`--receive-partial-source` and `--receive-obsolete-choice` extend the Qt receiver.

Queries run in one background worker while the current reading stays available.
Cancel query discards the result; an active provider request may still finish.
A result arriving after you change readings waits for explicit Open result.
There is no queue of source requests. Rich original overviews, bounded native
cell tables, source versions, sequence strips and retained-relationship graphs
complement the complete native readers. Sequence positions index the original
text only and establish no model/residue correspondence.

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

Within an opened Deck, native related-Card navigation now has all original member
captures available. A relationship can open a supplied Card even when that member
is outside the current display filter. Membership, matching names or sequences
never establish identity; native support, exact pins and revision choices remain
visible. The entry banner describes the original Deck occurrence, while the topic
index and reading follow the actual current Card. Return to Deck preserves the
original filter/order/page; following a destination never selects an arbitrary
occurrence for it. The `--cross-member` development receiver uses a public MONDO
Chagas disease/parent Deck and checks the entire original-source/save/return flow.


Save Deck reading (from the outer member/metadata view) now writes an independent
original Deck reading. It retains complete Deck metadata, all original member
occurrences/revisions, the current selection/order, metadata mode, page and Deck
Back history. Open reading or `--reading` can reopen that file in another process.
Member readings use the unchanged verified original Card format; scientific
interpretations not visited before saving remain explicitly `not_saved`.

```python
import sabueso

selected = deck.explore().overview().sort("label").filter("protein")
selected.save("deck-reading.json.gz", compression="gzip")
original = sabueso.read_deck_exploration("deck-reading.json.gz")
assert original.mode == "saved"
```

This saves the outer Deck reading. A focused Card UI trail, source queries, layout
and molecular scene are not included. Use Save reading while inside a Card for
its original within-Card scope; Save layout remains presentation only. The first
Deck envelope can repeat shared capture data across distinct focal Card bundles,
so bounded pages do not imply bounded capture or archive memory. Large-Deck
budgets and original-format receiving remain owned by #153.

Save workspace composes original Card/Deck readings with the exact inner Card
trail/pages, outer Deck selection/Back and source-query history. Reopen workspace
verifies the last saved digest; Open reading or `--reading` can independently
open the file in another execution. Saved source-query decisions are labelled
original reports. Reopening never constructs current Cards or queries sources;
unvisited science remains `not_saved`.

Pending queries, layout, model/camera/scene and provider tokens are not saved.
Use a separately saved layout and explicitly supplied model when needed.
Workspace admission is bounded to 64 MiB encoded/decoded and 256 MiB logical
receiving; the file chooser currently limits inputs to 16 MiB. Distinct native
Deck components can repeat captured data, so larger scientific workspaces may
spend substantial time in original verification. This is explicit saving, not
automatic crash recovery. The [format/scope guide](../../devguide/pending_proposals/interactive_workspace_persistence_0160.md)
and source-bound receipt own measured limits.

The scientific receiving route is
`deck_explorer_journey.mjs --receive-scientific --manifest <inputs.json>` on the
prepared public five-occurrence P52270/BTS/molecule/MONDO Deck. It receives native
assay/full-publication context and exact source-bound return through whole
workspace saving. `--reading --resume-scientific` receives independent startup
from that actual saved file. The source-entry receiver's `--receive-workspace
--receive-cancellation` uses explicit synthetic latency fences to receive
reading/cancel/stale-result behavior; it makes no source-speed claim.
Its `--receive-pending-close` control receives the owned service closing with
one additional unfinished synthetic query. The generic receiver's
`--receive-recovery` uses a bounded public Card, positively identifies only its
own launcher's direct service child on Linux, receives visible service loss
with the reading/window retained, and explicitly restarts from the saved
workspace. These are controlled receiving actions, not automatic recovery or
general process-management features.
