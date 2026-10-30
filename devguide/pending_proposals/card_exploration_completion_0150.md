---
summary: Maintainer-required complete exploration design and human acceptance before 0.15.0.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-22
closed:
verification: inspected
area: [public-api, human-exploration, scientific-views, release]
blocked_by: []
supersedes: []
---

# Complete Card exploration before 0.15.0

## Maintainer decision and release gate

On 2026-10-22 the maintainer explicitly required **the entire broad exploration
design and the human experience before 0.15.0**, including activities, clinical
context, variants, sites and comparisons. This supersedes treating those panels
as extensions after this release. The [A–D checkpoint](card_exploration_v1_closeout.md)
remains an intermediate milestone; completing its finite queue alone cannot
admit 0.15.0. The [detailed nature-specific design](card_exploration_detailed_design.md)
and [human exploration plan](card_human_exploration_api.md) define the target.

The implementation remains authorized. Version changes, schema freezing,
candidate selection, staging, publication and release consolidation remain paused.
No human usability, full implementation or release qualification is claimed by
this decision. #148 owns local exploration delivery; #112 owns release coordination.

## Broad profile delivery inventory

Each row needs a scientific presentation and supported navigation, not merely a
generic dictionary browser. Existing readers and their original explanations,
rules and scope are reused; missing adapter work is distinguished from missing
source knowledge. Current initial routes are implemented in development, not
accepted as the complete broad profile.

The [#165 native quaternary correction](../pending_bugs/quaternary_interpretation_scope.md)
preserves all source-bound declarations and exact interface/family pairs under new
rules. The separate [live adapter](card_quaternary_interpretation.md) now shares
interface classifications and every family comparison between readable human
views and compact agent selections, with original support and explicit unknowns.
Its [original scientific saved reader](card_saved_quaternary.md) now preserves
human/agent requests, input scope and navigation. Researcher acceptance remains pending.

| Nature / topic | Current exploration position | Completion requirement |
| --- | --- | --- |
| Protein: function | Initial fields/question delivered | Finish broad-profile integration and researcher review of original function/organism/sequence scope |
| Protein: sequence and annotated regions | Original sequence/feature source panel, individual annotations with exact item support, native scope/modifiers/revision retention (#160), complete native feature identity before normalization (#162), and explicit annotation-to-region structural questions with original input links and saved reading delivered | Complete broader sequence/structure transitions, compound/other-provider scope and derived sequence context with explicit numbering; preserve historical unknowns |
| Protein: experimental structures | Initial adapter, selection, saved reading and readable original support/source orientation delivered; original subunit/assembly/interface source pane adds individual assembly detail; exact experimental/literal structure-to-ligand/assembly/chain/numbering destinations preserve original source scope; #168 exact explanation scope and #169 declaration admission qualified; live assembly-generation rows, detail, original context and typed human/agent selection delivered | Independent original assembly-result saved reading remains pending. Original coordinate/reference admission (#170) and fixed original source-selection binding (#172) have separate qualified receipts; focused regional chain reading now presents original gaps and exact numbering routes. Complete #173's generation/operation-bound native assembly reconciliation, broader cross-topic transitions and scientist acceptance |
| Protein: predicted models | Source model/version/metric/range, original MD5/identity/reference inputs, scoped whole-reference coverage, readable uncertainty/input links, a verified whole-reference question sharing the experimental region inventory, and inert historical reading delivered | Preserve historical unknowns; complete partial-fragment/region and cross-topic integration plus compact scientific agent parity without experimental equivalence |
| Protein: sites and molecular contacts | Source functional-site/contact declarations, source-bound canonical overlap with explicit uncomputed scope (#163), a readable comparison question with original source/annotation/contact and separate instance/assembly context links, original instance selection/saved reading, exact instance-to-parent declaration navigation with frozen historical compatibility, RCSB contact-rule/input binding with conservative native identity/axis scope and distinct merged derivation contexts (#156) delivered | Compact exact agent selection now shares comparison results/items and mandatory scope/support. Original saved comparison verification and exact agent requests now delivered under @3; preserve historical unknown basis and complete assembly-aware reconciliation, region/structure transitions and researcher acceptance |
| Protein: variants and isoform context | Existing tissue/variant/isoform readers; no rich explorer panel | Original genomic/transcript/isoform context, per-tissue unknowns, named rules and scoped support |
| Protein: comparative context | Existing comparison readers; no rich explorer panel | Explicit supplied-Card comparison, relationship basis and maps where required; no identity merge by similarity |
| Protein: molecules and measured activities | Existing protein-centered `bioactivities()` and explanations; no rich explorer panel | Molecule/group/measurement/assay/document drill-down with original target assignment, units, qualifiers and comparison limits |
| Protein: biological associations | Existing stored relationships/readers; no rich explorer panel | Typed disease/pathway/interaction context with exact direction and original support; no invented causality |
| Molecule: chemical identity | Initial chemistry fields and source identity links delivered | Broad-profile presentation of retained stereochemical/charge/parent context, including absent/ambiguous scope |
| Molecule: physicochemical properties | Initial fields/methods/units/alternatives delivered | Complete nature-specific presentation and scientific interpretation review; calculated/measured/unknown stay distinct |
| Molecule: chemical classes and roles | Retained ChEBI mapping; no rich explorer panel | Readable direct/inherited source classes/roles; no inferred pharmacological effect |
| Molecule: target/activity context | Literal retained context; no rich explorer panel | Exact molecule identity join to retained or explicitly supplied measurements; never apply a protein-only reader to a molecule |
| Molecule: indications and clinical studies | Existing `clinical()` semantics; no rich explorer panel | Separate indication, source-cited trial and fetched registry record; explicit unqueried/failed scope and source-specific status |
| Disease: definition and terminology | Initial definition/synonym/term context delivered | Complete broad-profile orientation, source/release/term-status presentation and researcher review |
| Disease: classification and related terms | Initial parent/identity routes delivered | Clear hierarchy/equivalence distinction, exact supported transitions and full original scope |
| Disease: retained associations | Literal/source inspection; no rich explorer panel | Explicitly retained molecular/clinical relationships or supplied-context associations; identifier basis and direction stay visible |
| Shared: identity, sources, coverage and full content | Initial discovery/inspection/support/coverage delivered | Consistent integration across all panels; generic/unknown natures retain complete literal access |
| Shared: literature | Existing literature readers/explanations; no rich explorer panel | Publication roles, exact cited identities and original locators; no implication that every paper supports every displayed claim |
| Shared: contextual navigation and saved reading | Initial capture/navigation and structural/field/coverage history delivered | Support every newly delivered panel's exact options, source closure, independent inert reading and explicit new interpretation |
| Shared: compact agent access | Literal, structural, ligand-site comparison, live quaternary interpretation and assembly-generation exact selection delivered; shared source-path membership reduces comparison delivery overhead | Original quaternary scientific saved reading is now delivered; bring parity to subsequent adapters; equivalent requests share science, scope, units and support |

An unsupported/unqueried state is a legitimate answer for a particular captured
Card. It is not proof that a missing rich adapter is implemented. Each panel
needs a positive public-data example and applicable missing/partial/conflicting
or non-applicable cases. Identity, quantity and support contracts remain mandatory.
No browsing operation may acquire new data, refresh a Card or fabricate findings.

## Implementation order

1. Finish readable structural support/source orientation and its saved compatibility.
   Include [original source-active-site selection binding](../pending_bugs/dossier_active_site_selection.md)
   (#172): preserved original inputs and coherent native outputs must answer the
   fixed declared question, independently of current scientific readers.
2. Complete protein sequence, predicted models and sites/contact/assembly routes,
   sharing existing axes, residue knowledge and original structural support.
   The [regional chain reading](card_regional_reading.md) now presents the exact
   original regional result and numbering routes without enlarging machine frames.
   Fresh acquisition now retains [original source assembly generation](rcsb_assembly_generation.md)
   for literal human/agent and inert saved inspection. Native symbolic plans and
   optional preflighted tuple expansion are now available through
   `Card.assembly_generation()`. Current generation `@4` adds exact entry-operator
   and retained component-key binding, distinguishing polymer instance records
   from ligand-neighbor references and retaining missing/ambiguous labels.
   Compact occurrence plans and deliberate preflighted expansion retain declared
   component/operation combinations and original contexts without physical identity
   inference. Explicit `@1`–`@3` preserve the earlier interpretations. Full component/physical-instance
   reconciliation remains open. The [shared live assembly adapter](card_assembly_exploration.md)
   now supplies readable rows/detail, exact original context/source navigation and
   compact typed agent selection from one captured native @4 result per request.
   Factored counts stay distinct from unknown scalars; scientific saving is
   unavailable until the independent original reader, next in
   [#173](https://github.com/uibcdf/sabueso/issues/173);
   composition and equal local labels cannot substitute for that contract.
3. Complete activity/assay/document and shared literature journeys, then molecule
   target context and clinical/classification views with explicit identity joins.
4. Complete variants/isoforms/comparisons and biological/disease associations with
   explicitly supplied context and original genomic, numbering and source scope.
5. Qualify broad-profile navigation, saved reading and compact agent parity for
   all delivered routes. Review opening menus, defaults, errors, empty recovery
   and support wording as one coherent experience.
6. Complete human walkthroughs, workload qualification and final technical gates
   before considering release consolidation. Do not declare the experience
   exceptional solely from tests, generated panels or implementation checkmarks.

Every implementation block updates this inventory, its technical tests and #148.
Use bounded public fixtures; private pilots remain read-only and do not enter
public examples or tests. A missing scientific reader/identity contract requires
a concrete design and owning issue; it does not authorize an implicit heuristic.

## Human acceptance and the intended exceptional experience

Researchers with declared Python familiarity must be able to orient themselves,
find relevant scientific questions, select and compare supported options, inspect
their full sources/qualifiers, recover from empty or ambiguous states, cross topics
without losing context, and reopen the original reading after change. They must
understand the difference between a selected value and alternatives, an unqueried
source and absence, a relationship and identity, and calculated versus measured
or unknown methods. Essential interpretation must work in text and Jupyter.

Prepare actual public protein, molecule and disease journeys across the broad
panels. Record task success, misinterpretations, navigation/help needs and fixes;
include the maintainer and a researcher unfamiliar with internals. Agree
workload-specific time/memory budgets and verify them, distinguishing capture,
materialization, cached interaction, persistence, process memory and response size.
Human acceptance needs observable reviewer feedback, not an agent's prediction
of a positive reaction. Agent conformance and human usefulness are separate gates.
The workload scope includes [#171's region expansion guard](https://github.com/uibcdf/sabueso/issues/171),
alongside #167's capture/storage costs: response byte limits alone do not bound
request normalization or process memory.
Default workload ceilings must be visible and explicitly overridable: a deliberate
caller can raise or disable the applicable ceiling through a documented public
option, with equal access for humans and agents. An over-budget request is refused
before expansion with its requested size, budget and exact override route; it is
never silently truncated, sampled or substituted. Preserve the complete request
and effective workload policy in its execution record. Scientific validity and
reference admission remain mandatory. The [receiving implementation](../pending_bugs/region_request_expansion.md)
adds public `region_budget=100_000` / explicit `None`, with separate live receiving
receipts and unchanged historical scientific readers. Read #171 for source-bound
qualification. Combined researcher/workload acceptance remains open (#148); selected technical
checks do not establish the complete experience or release readiness.

Before 0.15.0, every row above must have its implemented scope, relevant public
walkthrough and technical receipt, with human acceptance recorded for the combined
experience. Final exact-SHA CI/governance through gh-run-receptor and the existing
installed-artifact/release gates remain mandatory. Only then may the maintainer
decide to resume the separate release route.
