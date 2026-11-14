---
summary: Experimental molecular runtime close/reopen with exact initial input, unchanged Knowledge and an independently surviving native view.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-14
verification: implementation_checkpoint
area: [human-exploration, visualization, lifecycle, standalone]
---

# Owned experimental molecular runtime lifetime

The [living plan](interactive_implementation_0160.md) owns S2/S5 acceptance.
This increment extends the existing experimental public Viewer binding; it does
not receive a supported embedding/current-model contract under
[Viewer #368](https://github.com/uibcdf/molsysviewer/issues/368).

## Close, reopen and final shutdown

Close model releases the adapter's own Viewer service/view and removes its live
iframe. Knowledge, source/query history, layout and the captured initial input
remain available. Reopen initial model creates a fresh service/view from that
copy, with new session capabilities. It does not reread a changed/deleted caller
file, restore camera/selection/scene or identify the active model with a Card.
If its visible panel was removed, Show model opens the new viewport explicitly.
Final application shutdown also retires the owned input copy.

The lifecycle revision admits only current close/reopen commands. It identifies
application transitions, not scientific model/occurrence/index identity. All
models remain visibly `correspondence: not_established`. Source knowledge is not
queried, reconstructed or changed by either action.

Only the already admitted loopback origin may be reused, through Viewer's public
`listen_port`. The native host and document CSP keep that exact origin; no new
port is silently added. Reopening after a page reload while closed works under
the same finite allowlist. If the port is occupied, an explicit unavailable state
keeps Knowledge usable and offers a retry after the conflict ends. Failure to
dispose resources retains the owner/reference and refuses a competing runtime.
The initial-copy digest is checked again before loading; an altered owned copy
is refused rather than replaced with the caller's current bytes.

Model commands have an independent asynchronous lock. An owned pending close
does not hold the retained-reading lock; current page/action/source access stays
available in the HTTP control. This does not prove nonblocking provider parsing
for large inputs: the received public loader is synchronous, and its setup runs
in the service process. Model parsing, geometry and rendering remain provider
work. No extra parser, scientific engine or dependency is introduced.

Adding a missing model panel also places Context below Knowledge, preserving
reading width rather than leaving three narrow columns after closed-page reload.
The first functional receiving passed while its native capture exposed this
layout defect. The corrected receiver additionally requires at least 400 pixels
of reading width and Context below it in the fixed 1280×900 profile; this is a
bounded presentation check, not a human accessibility verdict. Earlier artifacts
and captures retain their source epoch and are not counted as final receiving.

## Receiving scope

The native receiver's `--receive-lifetime` starts two independently owned actual
Qt windows with the declared public model. It changes only its task-owned caller
copy after capture, then checks three release/reopen/draw cycles, retired TCP
listeners, rejected old capabilities and an independently surviving renderer,
camera and selection. It also receives closed-page reload, an occupied-port
failure/retry and exact Knowledge return. Empty selection observations do not
qualify nonempty mapped picking or selection. Public original inputs stay intact.

Unit/real-loopback controls cover stale/foreign/malformed commands, independently
available reading during pending close, initial-copy integrity, changed-origin
refusal and cleanup-failure ownership. Real Qt is required to receive drawing and
independent window survival; fake providers alone cannot qualify those behaviors.

The [source-bound receipt](../evidence/interactive_model_lifetime_checkpoint_20261114.json)
separates 202 source application cases, 201 installed runtime cases, 31 native
checks each from checkout/installed wheel, six failed-input controls and a separate
31-check installed current-provider profile. Artifact/original compatibility,
resources and failed controls retain their exact cohorts. S2.4 remains partial: general provider pending
operation/callback disposal, shared-session multi-view semantics, supported
background suspension, scene recovery and the supported embedding contract stay
open. S2.2/S2.5 still require exact source-bound model/index correspondence.
Native platforms, long-session/workload budgets and human acceptance are separate.

The final selected application and initial native profiles ran before an
independent MolSysMT fast-forward from `ff25f120` to `27ba3d4c`. The receipt keeps
those provider cohorts separate and adds current-provider native receiving.
Its first attempt reached the second window's API before authentication was
complete; the receiver now waits for its authenticated reading. This is an
observer race, not an observed provider regression. Failed records remain retained.
Editable distribution metadata can still name the earlier installation commit;
source paths/heads and actual consumed cohort are recorded separately.

## Chemical representation handoff

The previously prepared provider proposal is now published as
[Viewer #387](https://github.com/uibcdf/molsysviewer/issues/387) under the
maintainer's standing authority for technical reports in UIBCDF repositories.
It asks the provider to own or explicitly delegate source-bound optional 2D
depiction, preserve the exact chosen chemical declaration and define supported
inputs, limits and provenance. Issue delivery does not implement that capability,
adopt a renderer or close S4.3. Third-party publication keeps its separate prior
permission requirement.
