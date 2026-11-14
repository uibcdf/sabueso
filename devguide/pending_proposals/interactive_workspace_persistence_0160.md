---
summary: Original application workspace composition, rich retained presentation and nonblocking source-query receiving.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: implementation_checkpoint
area: [human-exploration, persistence, deck, standalone]
---

# Original interactive workspaces and retained presentation

The [implementation plan](interactive_implementation_0160.md) owns completion
states. This increment extends the real Qt application without replacing native
Card/Deck readers, source assertions or scientific rules. The
[source-bound receipt](../evidence/interactive_rich_workspace_checkpoint_20261113.json)
owns actual qualification, failed controls and resource observations.

## Researcher-visible behavior

Protein, small-molecule and disease overviews now show the original curated
fields and their retained source names/versions. Inspect original field opens
the exact native location. Cards and Table show bounded native cell previews,
states and units; Open still reaches the complete retained value/support.
Filtering a displayed value submits the original backend cell, avoiding numeric
round trips in JavaScript. Exact breadcrumbs restore the original view and pages.

Primary sequence strips preserve the retained sequence text. Their positions
index that text only; they establish no residue, structure or isoform mapping.
The named `retained_relationship_graph@1` presents current-page native
relationship endpoints. Each edge opens its original record. It does not join
names, deduplicate identities, convert membership into an association or turn
a derived relationship into a SourceAssertion. Inspect support and derivations
through the native reader. Neither presentation changes scientific results.

Explicit source queries run in one background worker, without a queue. Reading,
source inspection and Back remain available. A result arriving after the current
reading changes waits for explicit Open result; exact revision admission prevents
automatic replacement. Cancel query discards a pending result, including one
already ready. It does not promise interruption of provider HTTP requests. Until
that worker exits another source query is refused. Backend shutdown joins it
briefly; the backend process owns its final daemon lifetime.

## Save scopes

| Action | Retained scope |
| --- | --- |
| Save reading inside a Card | Existing original native Card interpretation and native navigation closure |
| Save Deck reading outside a Card | Original Deck metadata, occurrences, selection/order, page and Deck Back |
| Save workspace | Current Card/Deck application reading, inner Card trail/pages, outer Deck state, literal source-query reports/choices and up to 32 exact query return points |
| Save layout | Existing separate presentation-only arrangement |

Save workspace writes `sabueso.explorer_workspace@1`. Reopen workspace verifies
the last saved digest. Open reading and `--reading` independently admit this
format in another process. Original native components pass their existing
independent verifiers. Reading never constructs current Cards or repeats a
query. Unvisited scientific interpretations stay `not_saved`; complete literal
capture content remains governed by native capabilities.

Source-query reports are labelled original saved reports. Their recorded
resolution, acquisition trace and explicit source-declared PDB choices survive.
Operational session revisions are regenerated. A saved report is not a new
resolution or proof that the source is still current. A digest detects changed
content against a known digest; a self-sealed file does not authenticate its author.

The workspace omits pending jobs, provider tokens, model/current-model identity,
camera/scene, layout and runtime output paths. An explicitly saved workspace is
the restart route; unsaved state is not claimed to survive a backend failure.
Reopening it does not silently open a model, restore a panel layout, run an action
or issue a source request. Unknown format/scope is refused before replacing the
current reading. Existing originals are not overwritten by default; an encoder
failure leaves the destination and current reading intact.

## Composition and limits

Native Card files stay byte-identical when the internal serializer supplies its
existing navigation-node IDs out of band. The application trail binds those
verified nodes, exact original view references, item/text offsets and history;
titles and equal contents are never used to choose a navigation instance.
Shared native Card sessions are serialized once per application composition.
Their retained interpretation pool includes the views already visited through
that shared session, while each query context retains its own exact UI position.

The separate native Deck envelope preserves all original metadata and ordered,
repeated or anonymous members. An inner Card trail must have the same complete
input/capture pool. Entry occurrence remains distinct from the current focal
Card, including a supplied related ligand or an unavailable destination.

Version 1 admits at most 64 MiB encoded/decoded, an 8 MiB codec window, a
256 MiB logical receiving budget, 1,024 components, 32 query return points and
the existing finite Card trail/page limits. These are admission limits, not RSS
guarantees. The GUI file chooser currently admits 16 MiB inputs; startup original
reading admits 64 MiB. Distinct focal native Deck components can still repeat
the capture pool. Large-Deck scaling belongs to #153; a small page does not
bound capture, archive or verifier work.

## Defects exposed by the complete journey

The public mixed Deck journey reaches P52270 → source-bound BTS → native activity
with units → original target assay → complete publication → exact original Deck
return. Its first workspace save exposed a native original-reader defect:
canonical JSON sorts Card object keys, whereas the capture factory retains
first-input occurrence order. With multiple unsupported supplied natures, the
frozen molecule predicate consequently reconstructed a different ordered result
and refused the file. Restoring capture iteration from the already recorded
input occurrences fixes this boundary. Scientific wires, frozen predicates,
formats, identity and historical meanings are unchanged. A resealed input
permutation still fails independent admission.

The service bootstrap previously became visible before its JSON was complete,
and startup failure could remove a pre-existing caller descriptor. It now
publishes a complete private file atomically without replacement, and removes
only its own recorded inode. Collision, replacement, symlink and first-visibility
controls protect caller files. Actual process/Qt receiving remains distinct from
those targeted controls.

The current installed application also receives controlled loss of its own
reading service: the window and reading survive, an action explains the failure,
and explicit application restart from the saved workspace restores the original
reading and Back. A separate synthetic pending query stops with its owned service
in about 2.24 seconds, without adopting a result; the descriptor retires. This
does not claim interruption of provider HTTP or automatic unsaved recovery.

The first recovery receiver used a larger source-rich protein Card and hit the
unchanged native 64 MiB decoded saving guard before reaching its fault injection.
That is a retained bounded-admission result, not a passing recovery trial. The
corrected recovery scope uses a bounded public disease Card. The scientific
mixed workspace receives its own actual save/reopen and resource scope; neither
result establishes general Card-size or packing guarantees.

Remaining work includes supported model/source correspondence under Viewer
#368, available 2D/3D chemistry, broader ambiguity/enrichment presentation,
molecular pending-operation receiving, varied-workload budgets and human
review. This increment does not close S2, S4, S5 or S6, change dependencies or
publish a GUI/platform/release claim.
