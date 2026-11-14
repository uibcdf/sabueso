---
summary: Concrete consumer receiving requirements for supported molecular correspondence and lifetime.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: consumer_handoff_prepared
area: [human-exploration, visualization, interoperability]
---

# Molecular integration: concrete consumer receiving

This is Sabueso's bounded consumer handoff for
[Viewer #368](https://github.com/uibcdf/molsysviewer/issues/368), not a selected
provider API, a new platform contract or a report of a newly reproduced defect.
The [living plan](interactive_implementation_0160.md) owns S2/S5 acceptance.
Provider source remains `0dcdd6ce574d3c99483480cb38c16c1e3cc4782f` in the reviewed
local cohort. The existing issue and two consumer updates already report the
need; this document makes the next receiving work concrete without publishing
another provider comment or modifying that repository.

## What already exists

The product uses public `RemoteSessionService(render_on="client")` and
`MolSysView` experimentally, with actual renderer/structure readiness observations,
public camera and active-selection observations and owned final cleanup. Current
source/wheel resource observations include two public models and twelve layout
cycles each. None establishes a supported embedding or correspondence contract.

Viewer has a public read-only `view.molsys` property and public selection/click
facilities. The returned MolSys can be mutable. This handoff does not claim loaded
model inspection or selection is absent. What Sabueso still needs is a supported,
coherent current-model/index-domain identity and event/lifetime surface it can
receive through the application embedding. Private scene/protocol fields are not
a stable substitute. Viewer's own
[transport ownership](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/transport_state_ownership.md)
and [data-plane architecture](https://github.com/uibcdf/molsysviewer/blob/0dcdd6ce574d3c99483480cb38c16c1e3cc4782f/devguide/data_plane_architecture.md)
retain provider authority over current projection, transport and scientific model.

## Minimum information and responsibility

These are semantic requirements, not prescribed Python methods or JSON fields:

| Boundary | Required meaning | Owner |
| --- | --- | --- |
| Current model/index domain | A coherent token or equivalent supported observation identifying the loaded molecular composition and atom/occurrence index domain; replacement or reindexing must invalidate old bindings even if filenames/labels match | Viewer, with MolSysMT-owned model/index semantics |
| Source context | Exact source/entry/model/entity/occurrence identifiers where retained, including chain/author/insertion-code distinctions and explicit unknowns; a filename or equal residue label cannot supply identity | Provider source data; Sabueso verifies the Card/source binding |
| Selection request | A nonempty exact bounded selection tied to the model/index domain it was prepared against; stale bindings are rejected before applying | Viewer applies and acknowledges; Sabueso owns the retained annotation request |
| Selection/click event | The original event's model/index domain and exact selected indices, including empty/unknown/replaced states; reading the current token after the event must not retroactively certify it | Viewer |
| Correspondence | Exact Card capture, native annotation/source locations and explicit model occurrence mapping, with original support and ambiguity retained | Sabueso consumes provider-owned indices/mapping; MolSysMT owns geometric/index operations |
| Lifetime | Readiness, hide/move versus disposal, pending-operation completion/failure and independently owned views, through a supported application surface | Viewer and the thin Sabueso adapter |
| Coordinates/rendering | Existing binary control/data separation; no coordinate arrays copied into Sabueso Card JSON or a competing renderer | MolSysViewer/MolSysMT, including existing Rust |

The domain token need not be a hash of every coordinate frame. The provider must
define which topology/index changes invalidate it and how pose/frame changes are
represented. Camera motion alone must not accidentally certify or invalidate a
scientific binding. No consumer API is adopted until these semantics are received.

## First product journey and controls

Use an existing declared public model and a retained annotation whose source
explicitly supports the molecular occurrence/numbering relation. Do not infer the
relation from equal sequence, names or residue numbers. A model with no such mapping
continues to be useful as an explicitly unbound visual context.

| Case | Required observable behavior |
| --- | --- |
| Positive mapped reading | Choose one retained annotation, apply a nonempty selection to its explicitly bound occurrence, inspect the original assertion and return to the exact Card/Deck context |
| Positive picking | Pick a source-bound region/atom, inspect only its exact retained knowledge scope and return; original event/model identity accompanies the event |
| Missing or ambiguous binding | Explain the gap and preserve original support/alternatives; no automatic selection or identity merge |
| Same label, different entity/occurrence | Refuse the false match, including repeated chains, insertion codes and unrelated Card/source revisions |
| Replace or reindex | Invalidate the old mapping; delayed selections/clicks from the old domain cannot target the new model |
| Float/reset/hide | Retain the same live endpoint, camera, nonempty selection and original reading where supported; distinguish hiding from final disposal |
| Close/reopen | Dispose only owned view resources, make pending results explicit and start/restore only through the provider's declared semantics; do not call a new empty viewport a restored scene |
| Independent surviving view | Closing one view must not silently terminate another independently owned view or session |
| Shutdown/disconnection | Retire owned callbacks/services/input copies, leave no owned descendants and preserve Knowledge reading/recovery semantics |
| Unmapped/no-coordinate Card | Keep source/topic/graph navigation useful without silently fetching coordinates or creating a conformer |

Receive checkout and installed unpublished artifacts in actual Qt, then the actual
claimed platforms/candidate scope separately. Record provider/source versions,
original public input hashes, event order, selection membership, model-domain
changes, camera/reading continuity, cleanup and resource bounds. Mocks may verify
refusal logic; they cannot qualify real picking, renderer acknowledgement or lifetime.

## Next handoff

1. Viewer owners identify an existing supported route or define/document the small
   missing application/current-model surface under #368. They choose the exact API.
2. Agree the public positive mapping fixture and source-numbering/occurrence basis.
   A valid rendering input alone is not a correspondence fixture.
3. Implement the thin Sabueso adapter and the cases above against the received route.
   Keep the current explicit unknown correspondence until that receiving passes.
4. Record the actual provider cohort/minimum and bounded supported scope. Platform,
   long-session, workload-budget and human acceptance remain distinct.

Source-bound chemical 2D depiction is a separate capability/ownership proposal;
its prepared proposal is now [Viewer #387](https://github.com/uibcdf/molsysviewer/issues/387). Neither it
nor this handoff authorizes sibling implementation, an extra dependency, a provider
release, a new shared protocol or removal of the current visible limitations.
