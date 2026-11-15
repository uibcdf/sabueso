---
summary: Track the separately developed MolSysSketcher dependency and Sabueso's source-bound 2D receiving requirements.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-14
verification: consumer_design_handoff
area: [human-exploration, visualization, interoperability, architecture]
blocked_by: [uibcdf/molsyssuite#199]
---

# Reusable molecular 2D component: MolSysSketcher consumer handoff

## Current decision and independent work (2026-11-15)

The maintainer assigns MolSysSketcher to another development team. Its local
repository at `../molsyssketcher` contains the reviewed staged design for an owned
TypeScript scene, initially SVG, with molecular and interaction views as equal
product pillars. Scientific preparation remains delegated to qualified providers;
chemical editing is staged after exploration. The design supersedes the earlier
renderer-selection experiment recorded below. It does not constitute an
implemented, published or admitted dependency. Shared coordination remains in
[MolSysSuite #199](https://github.com/uibcdf/molsyssuite/issues/199).

Sabueso resumes independent workspace durability, measured performance and
researcher navigation. Do not implement a second 2D engine here while waiting.
S4.3 stays partial until a supported provider surface receives the actual
source-bound journey. Integration should first receive:

- One retained molecular declaration, its exact input/capture identity and
  provider capabilities; unsupported preparation remains visible.
- Read-only zoom/pan/selection with explicit stable atom/bond mappings, generation
  and stale-event refusal; no chemical mutation or automatic conformer creation.
- Return from the visual selection to its original retained source and Back,
  without inferring correspondence from order, labels or coordinates.
- Owned replacement/disposal, host resizing, keyboard access and bounded resource
  observations in the actual Qt host; a picture alone does not qualify the route.

Interaction views use domain-owned results and explicit coverage/method/units;
their equal importance in MolSysSketcher does not authorize Sabueso to calculate
interactions or import project conclusions as knowledge. Coordinated 2D/3D
selection also needs qualified mappings on the separate Viewer #368 surface.
Dependency admission, artifacts and concrete API receiving follow the provider
team's implemented contract; no speculative adapter is committed here.

## Historical source screening (superseded execution direction)

The remaining sections preserve the initial alternatives and their inspected
basis. Their proposed prototype order and D1–D3 are historical, not Sabueso's
current execution queue. Use the handoff above and the provider's living design
for new work.

### Original direction and boundary

The maintainer proposes a separate reusable **MolSysSketcher** component rather
than placing general 2D depiction in MolSysViewer's 3D core. Sabueso is the first
concrete consumer; BindingMT and PharmacophoreMT are prospective consumers, not
received integrations. The name retains the suite's full `MolSys` prefix.
The [living plan](interactive_implementation_0160.md) still owns Sabueso S4.3.
The shared ownership/evaluation proposal is
[MolSysSuite #199](https://github.com/uibcdf/molsyssuite/issues/199).

At that screening checkpoint this was a proposed comparison protocol, not a created or
registered repository, chosen engine, new dependency or implemented 2D product.
The earlier [Viewer #387](https://github.com/uibcdf/molsysviewer/issues/387)
records the consumer need; its ownership direction needs the separate suite
proposal. Supported 3D embedding/current-model work stays under
[Viewer #368](https://github.com/uibcdf/molsysviewer/issues/368).

## Chemical science and visual scene are separate layers

The proposed division is:

| Responsibility | Proposed owner |
| --- | --- |
| Molecular model, chemical interpretation, scientific operations and explicit atom/index mappings | MolSysMT and its supported chemical providers, including RDKit; inventory actual public capabilities before adoption |
| Specialized interaction or pharmacophore definitions/results | The relevant domain component; drawing a feature does not transfer its scientific ownership |
| 2D scene, overlays/shapes, selection, navigation, presentation state, events and supported embedding | MolSysSketcher; the original existing-toolkit hypothesis is superseded by the owned-scene design above |
| Card/source knowledge, original assertions, conflict/ambiguity and investigator navigation | Sabueso |
| 3D molecular representation and its existing scene | MolSysViewer, with explicit mappings for any coordinated 2D/3D selection |

RDKit can provide chemical characterization and graphical resources even if
another toolkit supplies the interactive view. Reuse supported scientific tools
through their owner rather than putting a new descriptor/feature engine inside
the sketcher. Possible inputs include a chemical graph, a generated 2D layout,
source stereo declarations, molecule-level descriptors and explicitly indexed
atom/bond/feature results. Their actual supported provider routes remain to be
qualified; this proposal does not claim that every RDKit API already has a
MolSysMT facade.

The [RDKit feature reference](https://www.rdkit.org/docs/RDKit_Book.html#the-feature-definition-file-format)
and [partial-charge API](https://www.rdkit.org/docs/source/rdkit.Chem.rdPartialCharges.html)
illustrate the scientific-provider role. Choosing a different visual toolkit
does not require giving up those resources. Their comparative scientific coverage
and actual suite exposure still need an inventory; renderer choice alone does
not settle which provider is best for every characterization.

For example, a provider may supply calculated atom charges, a molecule descriptor
or domain-owned donor/acceptor features; the sketcher displays a color scale,
labels or regions. Preserve method, parameters, tool/version, input/state and
applicability. Physical quantities retain their value/unit records. Unknown
parameters and failed computations must not become a numerical zero. Atom-level
contributions, molecule-level values and group features keep their distinct scope.

Two transfer routes should be tested rather than assumed:

- Give the renderer a declared chemical graph and existing RDKit-generated 2D
  coordinates, retaining the input layout where requested.
- Use an RDKit SVG depiction as a base layer under a controlled scene/overlay
  surface, if the candidate supports exact anchors and hit testing.

The graphic engine may need an internal chemical representation. It must not
silently become another scientific authority, normalize the input differently
or compute substituted properties. Atom order, canonical SMILES, matching element
labels and drawing coordinates do not establish cross-engine correspondence.
Keep exact model/input generation and explicit atom/bond mappings; reject stale
events after replacement/reindexing. A changed layout updates visual transforms;
a changed chemical graph invalidates applicable scientific results.

Drawing coordinates are layout, not measured 3D geometry. Reusing a 2D depiction
does not generate or validate a conformer. Calculated overlays remain separate
from source assertions and do not silently enter a Sabueso Card as source facts
or project Evidence.

## What the reusable component should add

Reuse a molecular layout/rendering toolkit. Keep the suite-owned layer small:
host-independent scene composition, stable selection/event context, optional
Python access and an embeddable web surface. Prototype generic circles, arrows,
regions and labels attached to exact atoms/groups, with theme/style controls and
application-defined interactions. Domain consumers supply the scientific meaning
of those shapes and tooltips.

Selection, hover, zoom/pan and annotations are required for exploration. Chemical
editing is a separate explicit capability; the name Sketcher leaves room for it,
but Sabueso starts in a mode that preserves its original molecular declaration.
Hiding editing buttons alone is not proof of a read-only contract.

Prefer public extension hooks and a bounded adapter. Retain source access and
license-compatible modification as an escape route; measure the patch and
maintenance burden if private hooks or a fork are needed. An open-source label
alone does not demonstrate a stable extensibility API. Prototype alternatives
do not require shipping or maintaining all engines in the final product.

## Source-screened candidates

The maintainer's expanded candidate list is an inventory, not an executed
ranking. RDKit as chemical support is compatible with selecting a different
visual/interaction toolkit. WASM by itself does not establish identical versions,
options, supported APIs, atom indexing or chemistry with the Python backend.

| Candidate | Inspected basis | Question for the prototype |
| --- | --- | --- |
| RDKit.js / RDKit drawing | Official [RDKit.js documentation](https://github.com/rdkit/rdkit-js/blob/master/readme.md) describes MinimalLib/WASM and SVG/canvas drawing; high-level UI remains application work. The actual engine/build source is [RDKit MinimalLib](https://github.com/rdkit/rdkit/tree/master/Code/MinimalLib) | Use as a chemical/depiction reference. Measure how much scene/interaction code would remain ours before considering it a complete visual foundation |
| Butlerov | Source [e4e64ae4](https://github.com/eizemazal/butlerov/tree/e4e64ae461832ce63bfeb5ff260ac8501edbac80/packages/core) supplies a TypeScript/Konva editor; its package declares Konva as a runtime dependency and MIT licensing | Test custom layers/shapes, nonmutating selection, stereo/input scope, import/export maps and supported lifecycle; TypeScript and a small dependency list do not prove chemical completeness or low runtime cost |
| Kekule.js | The [viewer tutorial](https://partridgejiang.github.io/Kekule.js/documents/tutorial/content/chemViewer.html) separates interaction and editing controls. Source [336b6271](https://github.com/partridgejiang/Kekule.js/blob/336b6271b9a394b7cc8a48ec0aa12f7d85167a27/src/render/2d/kekule.render.renderer2D.js) contains rendering primitives/registration | Test a maintainable third-party extension route, exact bindings and portable embedding; library age or default appearance alone is not a rejection criterion |
| Ketcher / Indigo | [Ketcher](https://github.com/epam/ketcher) provides an embeddable editor and a standalone Indigo-backed route | Receive a supported exploration-only mode and custom scene extension; retaining RDKit science does not make the renderer's chemical model automatically equivalent |
| OpenChemLib.js | Source [a365da1d](https://github.com/cheminfo/openchemlib-js/blob/a365da1d195d55cc942d40561be179ddb6301efb/lib/index.d.ts) provides molecular/SVG APIs and CanvasEditor. readOnly suppresses user interactions; editor actions mutate the supplied model. The JavaScript distribution is built from Java with GWT | Test a selectable nonmutating scene and modification/build effort rather than assuming editor readOnly supplies interactive exploration |
| SmilesDrawer | The [official drawing API](https://reymond-group.github.io/smilesDrawer/getting-started/) provides SVG drawing and atom highlighting | Consider a depiction-focused alternative. Measure required scene/picking extensions and resource use; fastest/lightest claims are unqualified |
| ChemDoodle Web Components | The [published licensing route](https://web.chemdoodle.com/installation/license) offers GPLv3 or proprietary licensing | Review exact artifact/redistribution/branding terms and extension scope before adoption; no legal compatibility conclusion or proprietary purchase is made here |
| JSME | The [project](https://jsme-editor.github.io/) is distinct from Kekule.js and supplies a molecular editor | Inspect actual source/build accessibility and supported interaction/extension scope separately; do not inherit a judgment from a combined aesthetic category |

### Bounded prototype order

Keep RDKit/MolSysMT as the proposed common scientific reference, subject to
actual supported API receiving. Begin interactive prototypes with **Butlerov and
Kekule.js**, because their inspected source exposes concrete scene/graphics
mechanisms worth testing. Add **Ketcher/Indigo** only if its source/API screening
justifies a third comparison. This order is an architectural hypothesis, not a
winner or a runtime/chemical-quality ranking. The suite owner may replace a
candidate after the first controls.

Use a bounded RDKit depiction as a reference, without building a fourth full
application. Retain OpenChemLib.js and SmilesDrawer as alternatives if required
capabilities or integration cost justify substitution. Final scientific results
still carry exact methods/definitions, versions, input mappings and limitations;
"same RDKit" is not a conformance test.

Repository/license inspection is preliminary. Final chosen artifacts, optional
dependencies, licenses, source/build identity, consumed API minima and Python/
browser compatibility need their own receiving. No packages have been installed
or adopted for this design review.

## Trial stages and acceptance

| ID | State | Observable result |
| --- | --- | --- |
| D0 | done | Source inspection, ownership proposal, science/scene split and comparison criteria recorded; no executed engine claim |
| D1 | todo | Two or three bounded prototypes use the same minimal host, supplied molecule and declared interaction path; record all runtime versions and limits |
| D2 | todo | Receive chemical fidelity, indexed selection, anchored shapes, redraw/resize, replacement/stale events, disposal and one source-linked Sabueso journey; capture actual native output |
| D3 | todo | Select a primary engine and the minimum suite-owned layer; record tradeoffs, patch burden and remaining gaps; decide component admission/repository and qualify the initial consumer API |

Start each prototype with one exact declared molecular input: show it, zoom/pan,
select an atom/group, draw an anchored shape, change its style, emit a bounded
event and return to the original source. Repeat with a replacement input and
retire the old scene. No network or hidden scientific preparation merely to draw.

Then use the same public small molecule, declared stereo pair, charged/salt
example, isotope/explicit-hydrogen case, congested or macrocyclic example and
invalid/unsupported input. Preserve original bytes, atomic/bond scope, visible
ambiguity and failures. Compare fixed supplied layout and engine-owned layout
separately. Receive a public calculated-property overlay with its exact method,
units and mapping, while keeping it distinct from retained source assertions.

Assess visual legibility with the maintainer, extension effort, mapping/event
correctness, read-only enforcement, accessibility, host portability, resource
use, lifecycle and reproducibility. Screenshots alone cannot qualify interaction,
chemical fidelity or ease of modification. Record supported hooks versus private
patches and the quantity of suite-owned glue; reject a candidate that requires
rebuilding its chemical renderer to satisfy the basic use case.

Use conservative bounded sequential runs first. Select only one production
engine unless a real consumer capability justifies more; keep an internal
adapter boundary that permits later replacement. Actual BindingMT/PharmacophoreMT
adoption, supported platforms, publication and full 0.16.0 acceptance remain
separate from this evaluation.
