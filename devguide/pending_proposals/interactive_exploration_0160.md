---
summary: Deliver bounded interactive Card and Deck exploration in 0.16.0, with MolSysViewer-backed molecular context.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-12
verification: design_review
area: [human-exploration, deck, visualization, interoperability]
---

# Interactive exploration for 0.16.0

## Accepted objective and current decision

The latest [standalone infrastructure evaluation](standalone_infrastructure_0160.md)
uses the maintainer's confirmed Python/live-MolSysViewer/standalone constraints.
It recommends a thin Qt/WebEngine host for the first prototype, with a portable
web UI and a panel-manager evaluation. Earlier browser-first/Svelte candidates
below retain discussion context; neither is an adopted stack. Host/framework
acceptance follows the bounded integration evidence in that evaluation.

On 2026-11-12 the maintainer accepts a first complete, bounded visual exploration
experience as the product objective for **0.16.0**. Reuse the accepted functional
0.15.0 Card foundation and add coherent Card/Deck navigation, visible controls,
source inspection and molecular representation where applicable. A researcher
should orient, select, investigate and return without needing internal schema
knowledge for ordinary work.

MolSysViewer is the proposed molecular rendering provider, subject to the
platform discussion and bounded integration qualification. This objective does
not select a dependency minimum or installation route.

Owners: [#154](https://github.com/uibcdf/sabueso/issues/154) for presentation and
architecture selection, [#153](https://github.com/uibcdf/sabueso/issues/153) for
Deck exploration, and [#148](https://github.com/uibcdf/sabueso/issues/148) for
existing Card semantics and researcher feedback; #112 coordinates delivery.
This document records the maintainer decision and review locally. No new issue
comment or provider change is published by it.

The maintainer requests a review of MolSysViewer **before discussing and choosing
the platform and technology**. Hosting, frontend framework, public method names,
distribution and the complete release contract remain undecided. The next action
is that discussion, followed by a small architecture comparison prototype.

This advances a bounded part of long-term stage 6. Semantic queries, temporal
knowledge, real interoperability and scientific/source coverage retain their
roadmap owners and dependencies. They can supply a concrete need of this journey;
the entire six-stage program is not the scope of 0.16.0. The accepted 0.15.0
functional milestone and separate delivery/acceptance states are preserved.

## First product slice

- Provide a readable opening with entity, captured scope, useful knowledge,
  consequential gaps and a small set of scientific next actions.
- Support a first Deck overview, explicit membership basis, member selection,
  filtering/order and Deck → Card → scientific item → source → exact return.
  Keep different entity natures and repeated member revisions distinguishable.
- Provide visible search/filter/detail/source controls and navigation history.
  Retain current scientific readers and compact headless/agent access.
- Coordinate molecular selection with knowledge reading through MolSysViewer
  on explicitly supplied, mapped structural inputs. Cards without coordinates,
  including disease Cards, retain useful nonmolecular exploration.
- Preserve original values, units, support, unknown/conflicting scope and captured
  revisions across navigation and saved reopening. Acquisition remains explicit.
- Exercise a public protein → ligand → activity → assay/publication journey with
  return to its Deck, and one structural journey connecting a supported annotation
  and its original source to a molecular selection. Refine these proposed
  acceptance scenarios before coding.
- Use actual researcher feedback after 0.15.0 and measured representative session
  costs to assess understanding and fluency. Technical tests alone do not
  demonstrate the intended exceptional experience.

Video presentation (#155), a general document exporter, CLI, broad source
expansion and general scientific preparation/analysis retain separate scope.
Review #192's aggregation meaning/correction before the next release; its
0.15.0 deferral does not automatically apply to 0.16.0. Reconsider independent
researcher and platform exceptions under their existing owners as well.

## Researcher-controlled assistant experience — 2026-11-12

The maintainer describes an accessible assistant for drug-design researchers:
start on a light, uncluttered screen, identify a molecular system or disease,
then explore Cards/Decks with strong visual support and the freedom to choose
questions and navigation. This is the accepted experience direction. Screen
details and the acquisition/visualization additions below remain proposed work.

The [layout sketch](interactive_explorer_experience_0160.svg) illustrates entry
and workspace organization. It is a static design artifact with inactive controls
and an explicit molecular-view placeholder, not a working application, scientific
result or usability observation. Owner #154; retain through the first interface
review, then replace or archive when an implemented design supersedes it.

### Entry, identity and the first useful reading

Start with a light background, a single prominent exploration field, recognizable
examples, an optional input-type selector, and opening/resuming saved work.
Suggest a few starting questions after identification; choosing a goal is optional.
No schema paths, source-assertion IDs or Python knowledge should be needed.

The interface can unify entry while preserving the distinct underlying meanings:

| Entry | Current scientific behavior | Interface work and honest outcome |
| --- | --- | --- |
| UniProt ID | `sabueso.resolve` can produce a protein Card with recorded resolution and selected enrichment | Open the identified Card, with its captured scope and clear routes to further knowledge |
| PDB ID | Current resolution returns a structure record and source-mapped related proteins, not a StructureCard | Open a structure-focused reading and offer related entity selection and explicit Deck construction; preserve source chain/occurrence context. #20 owns any future core structure-entity redesign |
| SMILES | A prefixed structure query is matched by PubChem; identity, alternatives, not-found and unsupported outcomes are retained | The input selector can supply the `smiles:` route. Show the original query and source match; a depiction or generated conformer does not establish missing identity or measured geometry |
| Disease | Supported terminology IDs resolve through source-stated MONDO identity | Open definition, hierarchy and retained associations. Free-text disease-name lookup needs a separate candidate-search contract; it is not supplied by ID resolution |

These findings follow the current [resolution guide](../../docs/content/user/resolving.md),
[resolver](../../sabueso/tools/resolve.py),
[PDB resolution](../../sabueso/resolver/entity_resolver.py),
[molecule guide](../../docs/content/user/molecules.md) and
[disease resolver](../../sabueso/tools/card/disease.py).
Keep unique identity, ambiguous candidates, related entities and an explicitly
selected Deck distinct. A search result does not acquire scientific membership
merely because its tiles look alike. Let the user select candidates without
erasing original alternatives or merging identities by similarity.

The initial Explore action declares a bounded acquisition scope using existing
source/profile semantics. Show progress and partial/failure outcomes, and make
further source acquisition a visible action. Browsing a retained topic or hovering
over an item does not silently query every source. A later acquisition creates
an explicit updated reading rather than changing an old captured answer.

### Workspace and visual continuity

The proposed workspace provides a few useful defaults and lets the researcher
compose the reading layout:

- A navigation area for Cards/Decks, with search and the exact route back.
  A scrollable first-layer topic index makes the Card's accessible areas visible;
  its horizontal/vertical orientation adapts to the layout as described below.
- A main reading area combining short orientation, questions, tables and visual
  resources. The researcher can switch between overview, sequence/chemical graph,
  molecular view, measurements, relationships and literature where supported.
- On-demand detail/source panels for the selected item: full value and units,
  relevant qualifiers, original support, alternatives/conflicts and unknown scope.
  Source inspection should preserve the originating selection and scroll/filter
  context instead of replacing the whole workspace. Panels can be docked or
  floating; the molecular view, reading text and other scientific views remain
  coordinated through explicit context rather than fixed screen positions.

### First-layer topic index and composable panels

The maintainer requires a scrollable index of the first layer of information
accessible from a Card. Recognizable topic tiles/buttons can include variants
and mutations, diseases, structures, ligands, activity and literature when
pertinent. Its purpose is both discovery and direct navigation, independently
of suggested next questions.

**Orientation stays open.** A vertical list is the first workspace candidate
because long labels, topic states and many categories fit naturally. A horizontal
strip may work well for an opening overview or a different panel arrangement.
Responsive layout and an explicit layout choice can support both; the prototype
should compare discoverability and reading space rather than freeze one direction.

The index should:

- Include the pertinent first-layer catalog, with an explicit complete-topic
  view/search and access to otherwise retained content. A short recommendation
  list must not become the only path to a topic. Distinguish the topics that
  can be investigated from information actually retained in this Card.
- Give each tile a clear label, optional icon and concise text state grounded
  in the capture: information available, partial, not consulted, unavailable,
  unknown scope or an explicit source statement of absence where justified.
  Missing retained data is not proof that the entity lacks that information.
  Numerical badges are optional and need a declared grain/scope; do not execute
  scientific questions merely to populate opening counts.
- Make overflow visible through a scrollbar/continuation cue and a complete
  index action. Support keyboard focus, touch and pointer navigation without
  depending on color, hover or dragging alone. No automatic carousel advance.
- Open/focus the chosen topic, mark the active context and preserve the index's
  selection, focus and scroll position on return. Keep stable topic identities
  through saved reading; scrolling itself triggers no source acquisition.

The maintainer also asks for interactive molecular representation, optional
floating graphical views and scrollable text so the researcher chooses what,
how and where to investigate. Treat molecular, sequence/chemical, table/plot,
relationship, reading and source views as composable panels with bounded,
explicit content. Their exact availability depends on the Card and qualified
provider capabilities; a generic graph or plot does not invent scientific scope.

Provide understandable open/close, resize, dock/undock and layout-reset controls,
with keyboard alternatives. Keep reading-text scroll independent of workspace
scroll and molecular gestures. A default layout should be useful before any
customization; save/restore personal layout separately from original scientific
reading, including viewport adaptation so panels do not reopen off-screen.

Each panel retains a visible entity/item/model context and exact captured basis.
Allow it to follow the current selection or keep a chosen context while another
panel follows a new route. This display choice does not mutate a Card, resolve
identity or create new source support. Deliberate links can synchronize a topic,
table row or mapped residue with the molecular view; unrelated contexts and
missing mappings remain explicit instead of silently changing another panel.

In-page floating panels and separate browser/native windows have different
lifecycle costs. Begin with lightweight panels and one active molecular scene;
additional molecular canvases/windows use explicit provider-supported opening,
ownership and cleanup. Reuse MolSysViewer's state/transport rather than creating
new scene authority or a renderer for every Deck member. Future comparison
viewports remain provider-owned. No multiple-window compatibility or particular
layout technology is established by the static sketch.

The [sketch](interactive_explorer_experience_0160.svg) now shows a vertical topic
index, an illustrative floating reading panel and a horizontal-index alternative.
All topic states are labelled examples, not observations of the displayed Card.
Prototype acceptance should check that a newcomer discovers off-screen topics,
distinguishes unqueried/partial information, opens a molecular view, scrolls text
without moving the camera, keeps one context while exploring another, and
restores the layout/selection without changing original values or support.

Protein reading can coordinate sequence annotations, an explicitly selected
structure/model, sites and source-supported ligand/activity context. Molecular
clicks and scientific-list selection should address the same qualified mapping.
An annotation without a valid coordinate mapping remains readable with its reason.

Small-molecule reading should offer an informative 2D representation where a
qualified depiction path exists, with original chemical identity/properties and
assay context. 3D uses an available declared structure/model; generating a new
conformer is an explicit external modeling action with its own basis. The 2D
depiction/3D input provider routes still need specification and receiving.

Disease reading emphasizes definitions, scoped hierarchy/association views and
related molecular entities. Relationship graphs show a declared, bounded retained
scope and edge meaning; graph proximity does not establish identity or causality.
Decks expose membership basis and let researchers filter, select and compare only
scientifically supported fields. Comparison need not load every molecular model.

### Assistance with user autonomy

Offer contextual next questions such as "Which structures can I inspect?",
"Which related molecules have measurements?", "What assay supports this value?"
or "What information has not been consulted?". Base suggestions on declared
catalogs and captured capabilities. Keep a source-backed reason or missing-context
explanation available for each consequential action.

The user can ignore suggestions, open any topic, alter criteria, follow sources,
add another entity, branch to another Card or return to an exact Deck selection.
Retain history, useful bookmarks and the ability to save/resume the reading.
Guidance does not impose a wizard, choose a "best drug", infer missing efficacy,
silently fetch data or adopt a project conclusion as source knowledge.

Natural-language help may later use the same validated actions and support paths
through its owning integration. This experience does not require an LLM, select
an agent/provider or authorize a second scientific engine. Plain navigation
remains complete and discoverable on its own.

### Consequences for infrastructure and the first prototype

This journey favors a dedicated reusable web interface, Python-owned scientific
and session operations, asynchronous progress/results and a public molecular
adapter. Keep native-window and notebook features in host adapters as above.
TypeScript with a component framework is the proposed frontend direction;
Svelte/TypeScript and a thin Python service are candidates for the first bounded
integration prototype, not adopted dependencies. Resolve the live Viewer bridge
and literal-type/quantity boundaries before committing to a server framework.

Prototype entry → identity/candidates → Card or selected Deck → scientific item
→ visual selection → source → exact return → save/reopen using public inputs.
Include a PDB with distinct related entity scope, an ambiguous/unmatched input,
an absent molecular model and an unqueried/failed source. Measure whether users
can choose their route and explain what a value/model means, rather than counting
panels or treating a successful rendering as scientific usability acceptance.
Independent researcher acceptance retains its actual scheduling/status.

Local owning follow-up: #154/#153 for entry/workspace orchestration and 2D/3D
integration needs, #148 for Card/source continuity, and #20 for any new scientific
structure entity. The concrete observations above describe existing boundaries;
they do not establish newly reproduced provider bugs. Prepare missing provider
capabilities in their owning issue after the consumer prototype establishes the
specific contract, within publication authority. No issue update is published by
this design record.

## MolSysViewer review: source and method

Read-only review of the clean sibling checkout at
`0dcdd6ce574d3c99483480cb38c16c1e3cc4782f`, with live GitHub issue reads on
2026-11-12. No provider file, generated bundle, dependency or environment is
changed. No new rendering, browser/Qt observation, build, integration test or
installed-package qualification is claimed. Recorded provider capabilities and
test receipts describe their own source epochs.

The authoritative starting points are its
[architecture](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/architecture.md),
[capability audit](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/capability_audit.md),
[public API](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/docs/content/developer/public_api.md),
[Studio contract](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/studio_interaction_contract.md)
and [current handoff](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/checkpoints.md#resume-in-one-page).
The source manifests and implementation confirm these findings:

| Area | Observation | Consequence for Sabueso |
| --- | --- | --- |
| Molecular rendering | Mol* `PluginContext`, TypeScript and a prebuilt ESM bundle; JS declares `molstar ^5.4.1`, TypeScript and esbuild | Reuse MolSysViewer through its supported surface; avoid another Mol* scientific/selection adapter |
| Notebook transport | `MolSysViewerWidget` uses anywidget and traitlets; Python owns canonical scene/system state, with asynchronous identity-bound messages | Jupyter is a direct Python integration candidate. Anywidget is a transport/hosting boundary, not a frontend framework choice |
| Studio UI | Custom TypeScript/DOM panels, progressive disclosures, compact navigation, retained form drafts/focus and docked/floating panels/windows | Reuse interaction lessons. Internal panel classes/styles are not a supported general application toolkit |
| Molecular APIs | Public regions, representations, annotations, selection/focus and `on_click`/`off_click`; events expose loaded-system atom indices | Useful building blocks for a bidirectional binding prototype; source residue numbering requires an explicit mapping |
| Native shell | Optional PySide6/Qt WebEngine hosts the web runtime through `QtViewChannel`; the host remains experimental | A desktop shell can potentially share frontend work. Native dependencies and qualification need their own decision |
| Browser outputs | Interactive HTML export exists; static exports have no live Python authority. Local standalone and remote sessions have separate experimental/preview status | An HTML export does not establish a live general Sabueso application or a shared saved-Knowledge contract |
| Extension points | Add-on specifications and `AddonPanelWidget` host provider-owned tools/panels | A contextual Sabueso add-on is an option. Whole Deck/disease exploration also needs a useful entry without a loaded molecular scene |

Relevant implementation anchors are
[widget.py](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/widget.py),
[interaction.py](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/viewer/interaction.py),
[runtime entry](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/js/src/index.ts),
[BasePanel](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/js/src/ui/panels/base-panel.ts),
[QtViewChannel](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/standalone_qt/view_channel.py)
and [add-ons](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/molsysviewer/addons.py).
Manifest declarations are not assertions about an installed dependency version.

The upstream [anywidget AFM specification](https://anywidget.dev/en/afm/) permits
plain or framework-generated ESM. Its current documentation describes newer
composition/lifecycle primitives than MolSysViewer's declared `anywidget>=0.9.15`
floor. A prototype must use the actually qualified API or justify its minimum;
it cannot assume every current documented feature exists at that floor.
[Qt WebEngine](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html)
provides a web-content host; choosing Qt does not remove the web frontend.

## Integration work and provider handoff

The reviewed source supplies visualization building blocks; it does not
establish a qualified Sabueso-to-MolSysViewer adapter. Define and qualify:

1. Exact captured Card/Deck and model identity, source revision, structural
   occurrence, chain, residue/atom mapping and model/frame context. Shared names
   or equal residue numbers never establish identity. Unmapped/ambiguous positions
   remain visible. MolSysViewer owns its loaded-source-to-Mol* permutation;
   Sabueso must not apply it a second time.
2. Bounded selection events in both directions, ownership of navigation versus
   camera/scene state, correlated completion and stale-result rejection.
   Closing/remounting the panel releases callbacks and molecular data.
3. Separate saved Knowledge reading and visual scene/session state, linked by
   exact inputs and qualified correspondences. A Viewer `.msv` session does not
   replace the original Sabueso exploration record.
4. An optional visualization dependency with useful headless access, explicit
   molecular-data loading and clear behavior without coordinates or live Python.
   A Card's source reference alone does not load a remote structure.

Owners: Sabueso #153/#154 for the consumer adapter; MolSysViewer for missing
public embedding/event capabilities; MolSysMT for molecular correspondence or
geometry it owns; MolI for a proposed shared Knowledge/visualization contract.
This is a local maintainer handoff of integration needs, not an observed provider
defect or accepted shared protocol. Prepare a concrete provider proposal when
the architecture/prototype identifies a missing API, reuse an existing owner
issue where appropriate, and publish only within scoped authority.

Provider follow-up already exists for notebook data retention
([#356](https://github.com/uibcdf/molsysviewer/issues/356)) and published Mol*
component-cache recovery ([#363](https://github.com/uibcdf/molsysviewer/issues/363)).
The reviewed build configuration applies a narrow local cache plugin. Qualify repeated
open/select/close on the exact integration version; those issues establish
neither a universal current leak nor final robustness. The local handoff's older
#344 open wording is superseded by its closed live issue state at this review.
Native Qt and remote previews retain the distinct limits in
[standalone surfaces](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/docs/content/developer/standalone_surfaces.md).

## Platform discussion and comparison

The review supports a web-technology frontend as a promising common direction;
the host and framework remain a maintainer decision. Compare candidates using
the same small public Card/Deck/structure tasks:

| Candidate | Main advantage | Work to establish before selection |
| --- | --- | --- |
| Jupyter first: Python + anywidget + TypeScript | Closest to current Sabueso use and MolSysViewer's supported notebook surface | Child-widget composition at actual supported versions, layout/lifecycle and usability with modest Python familiarity |
| Local browser application: Python backend + TypeScript frontend | Dedicated knowledge workspace without notebook navigation | Supported live Viewer embedding/transport, process/session lifecycle, local inputs and distribution; static HTML does not supply these |
| Qt shell around the web frontend | Native window/file integration already explored by MolSysViewer | Experimental host compatibility, event-loop/graphics and packaging qualification, compared with local browser hosting |

Product placement is separate: independent Sabueso explorer with an embedded
molecular view, or contextual Sabueso add-on inside MolSysViewer. The former
naturally accommodates Decks and entities without coordinates; the latter could
serve molecularly focused tasks. Compare entry experiences before making add-on
hosting the only route.

Plain TypeScript/DOM versus a UI framework is another independent choice. Neither
Mol* nor anywidget forces React, Svelte or Vue. Evaluate table/filter/detail
complexity, accessibility, reusable components and maintenance before choosing.
Shared patterns do not make Viewer internals a stable public dependency.

## Refined recommendation and portability requirement — 2026-11-12

The maintainer expresses a preference for an independent Sabueso application and
requires room to migrate to better infrastructure, with compatibility with
MolSysViewer and its future direction. **Infrastructure replaceability is a design
requirement.** The local-browser-first recommendation below, host/framework,
product name and shared interfaces remain proposals for discussion.

An independent application gives Cards, mixed Decks and entities without molecular
coordinates a complete home. It can preserve a full workspace, discoverable
actions, selection/history and source panels without a notebook's cell order or
kernel interaction becoming part of the researcher's ordinary task. Its costs
are real: session lifecycle, a frontend build, packaging, input handling and
application-level integration all become maintained product responsibilities.

The proposed first host is a **local browser application backed by Python**.
Provide a simple launcher, packaged frontend assets and a dedicated workspace;
ordinary retained-data browsing should work offline. Jupyter remains useful for
programmatic work and later embedding of the same components. A native window
can reuse the frontend when its value justifies its own qualification.

| Choice | Useful advantage | Cost or limitation for this product |
| --- | --- | --- |
| Notebook as the primary UI | Existing Python workflows and the most direct supported Viewer transport | Cells, kernel lifetime and notebook setup shape the user experience; a dedicated persistent Deck workspace needs extra design |
| Independent local browser application | Full workspace and a web frontend that can later serve other hosts; no notebook is needed for ordinary navigation | Python service/transport, local launcher, session recovery and live molecular embedding must be qualified |
| Native window immediately | Native file/window affordances and a clear desktop entry | Qt/Electron/Tauri each add runtime, packaging and graphics/platform receiving before the first product slice |
| Sabueso only as a Viewer add-on | Natural contextual knowledge alongside a loaded molecule | Deck/disease exploration and work without coordinates still need their own entry and scientific context |

### Boundaries that make a later migration practical

Keep the scientific core, knowledge-session operations, reusable UI and host
integration separate. The proposed dependency structure is:

```mermaid
flowchart LR
    H[Browser / notebook / optional native host] --> U[Reusable explorer UI]
    U --> K[Knowledge session interface]
    K --> S[Sabueso scientific API and saved readers]
    U --> A[Molecular view adapter]
    A --> V[MolSysViewer public integration]
```

- Scientific meaning, quantities, support and saved reading stay with Sabueso's
  existing Python APIs and versioned formats. GUI and HTTP models must preserve
  literal types and native quantity codecs; coercing values at a transport
  boundary must not silently change an original request.
- A small knowledge-session interface carries exact capture/selection references,
  bounded pages, operations and outcomes. Public Python and a web adapter use the
  same application operations. UI components consume that contract instead of
  parsing private Card storage or calling a particular server framework.
- A molecular adapter coordinates exact mapped selections and lifecycle with
  MolSysViewer. The provider owns its scene, picking, numerical buffers and
  rendering endpoints. Retain its control/data-plane separation rather than
  wrapping every molecular array in Sabueso JSON responses.
- Host-specific file dialogs, window controls, startup/shutdown and transport
  belong in host adapters. Components should not assume notebook globals,
  Qt objects, a fixed port, a workstation path or a particular rendering device.
- Persist scientific reading and lightweight workspace/view state separately,
  with explicit versions and exact references. A framework/widget object is not
  the archival representation. Future remote execution is a separate deployment
  decision, with explicit placement and infrastructure-owned resource control.

These boundaries reduce migration cost; changing framework, host or scientific
semantics still requires work and receiving. Implement only the small boundaries
needed by the first journey. Broader platform infrastructure is coordinated with
its owner rather than implemented independently inside this GUI.

### Compatibility with MolSysViewer's future plans

The additional review uses the same clean `0dcdd6ce` source and live #276.
Current contracts and dated owner decisions take precedence over older vision:

| Provider direction | Status and reference | Sabueso design implication |
| --- | --- | --- |
| One workbench and scene model across hosts | Maintained [standalone direction](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/standalone_direction.md) and [transport ownership](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/transport_state_ownership.md) | Consume provider projections/events through an adapter and preserve its authority; sharing a host does not require merging the two products' scientific state |
| Session on workstation/server/cluster; explicit client or server rendering | [Remote plan](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/remote_rendering_plan.md), retained unsupported preview outside the 1.0 contract | Keep knowledge endpoint and rendering placement separate; support capability negotiation before assuming a local WebGL canvas. Future remote or multiuser support is not delivered by local hosting |
| Binary transport now; possible windowed structural residency later | [Data plane](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/data_plane_architecture.md); [windowing #55](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/pending_proposals/post_1.0/structure_windowing_and_lazy_materialization.md) remains unimplemented design | Delegate structural transfer/materialization; avoid depending on private buffers or assuming all future frames are resident |
| Comparison viewports and synchronized cameras | [Multiview #49](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/pending_proposals/post_1.0/multiview_split_screen.md), post-1.0 design | Start with one bounded active molecular scene; let the provider own future viewport composition rather than creating a viewer for every Deck member |
| Evolved Qt versus Electron or Tauri | [#276](https://github.com/uibcdf/molsysviewer/issues/276) is open for post-1.0 evaluation; no host migration is approved | Preserve a portable frontend and a thin native adapter; compare exact workloads before selecting a shared host |
| Rust/WASM without a Python desktop backend | Separate long-term possibility in the [v2 vision](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/standalone_v2_evolution_plan.md), explicitly separated by #276 | Treat a future molecular engine or host change as a provider capability/version change. Sabueso's Python Knowledge backend has its own ownership and adoption decision |

Older installer-size, instant-start and host-superiority claims in the v2 vision
are hypotheses, as #276 explicitly records. They do not select Tauri/WASM or
establish future compatibility. Coordinate a public live-embedding contract with
MolSysViewer under #154 once the prototype identifies its exact needs; the
consumer proposal remains a local handoff pending scoped publication authority.

### Technology and first proof

TypeScript plus a component framework is a reasonable frontend candidate for
the growing selection/table/detail interactions. [Svelte](https://svelte.dev/docs/svelte/overview)
offers compiled declarative components; [React](https://react.dev/learn/add-react-to-an-existing-project)
can mount components within an existing application. Evaluate one bounded screen
against actual table/accessibility and Viewer mounting needs before adoption.
No frontend framework, minimum version or benchmark result is selected here.

For a Python web adapter, compare a thin FastAPI service (documented
[WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) and
[lifespan](https://fastapi.tiangolo.com/advanced/events/) facilities) with the
aiohttp integration already used by Viewer. The session and scientific contract
must remain usable when that server adapter changes. A shared HTTP library alone
does not establish interoperability.

Native packaging stays a later independent choice. [Tauri](https://v2.tauri.app/concept/process-model/)
uses system WebViews and supports [external binaries](https://v2.tauri.app/develop/sidecar/),
including a packaged Python service. [Electron](https://www.electronjs.org/docs/latest/tutorial/process-model)
uses a Chromium-based process model. Qt has the existing experimental Viewer
bridge. Measure installer/runtime and WebGL behavior rather than promising
unmeasured startup or memory improvements.

The first prototype should prove one complete Card/Deck/source journey and one
exact molecular select/click/close round trip, with responsive bounded work and
save/reopen. A small second-host mounting check should exercise the boundary
without building another full application. These observations decide the initial
stack; remote/multiuser services and all native installers are separate increments.

### Product name proposal

Prefer **Sabueso** as the visible application name, with a descriptive subtitle
such as "Molecular knowledge explorer". "Sabueso Explorer" can distinguish the
graphical interface in documentation when needed. Product naming, internal
module/launcher names and whether optional GUI packaging warrants a separate
distribution remain separate decisions. No new brand, public command or package
name is selected by this naming recommendation.

## Execution after the platform discussion

1. Agree first host, product entry, framework comparison and bounded public tasks;
   record the decision under #154 before full implementation.
2. Specify the smallest Deck human/agent navigation contract under #153, reusing
   existing membership, explanations and captured Card readers.
3. Prototype the selected candidate(s), with one explicit molecular mapping and
   return/source continuity, to resolve the integration questions above.
4. Implement the chosen frontend and adapter incrementally, preserving ordinary
   Python/agent access, original saved meanings and optional visualization.
5. Obtain researcher feedback and measure representative latency/memory and
   repeated-open/close behavior; correct consequential failures and record the
   final supported 0.16.0 scope and limits.

The current decision concerns the standalone host, public live-embedding surface
and frontend/panel-manager candidate in the latest infrastructure evaluation.
Notebook/browser reuse and a contextual Viewer add-on remain separate possible
entries. Dependency minima, provider receiving, platform support and publication
follow the evidence from the selected standalone candidate.
