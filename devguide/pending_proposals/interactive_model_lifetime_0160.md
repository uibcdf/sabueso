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
copy after capture, then by default checks three release/reopen/draw cycles, retired TCP
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

## Extended bounded observations (2026-11-15)

The [stability receipt](../evidence/interactive_model_stability_checkpoint_20261115.json)
extends S5.5/S6.2 with eight complete runtime cycles on each of two sequential
installed profiles: public 1TCD BinaryCIF and AlphaFold Q8WZ42 F2 mmCIF. The
AlphaFold input is deliberately unrelated to the P52270 reading. Every model
remains correspondence-not-established. Two independently owned Qt windows are
used during each runtime sequence; the second retains its camera/selection.

Each profile receives 32 checks, twelve float/reset cycles, two 60 s single-window
idle observations and 3 s closed/opened observation windows after every runtime
transition. Retired listeners, old capabilities, the initial-copy digest, actual
drawing, source reading and exact Knowledge context survive all sixteen cycles.
Knowledge HTTP probes occur after readiness and do not qualify responsiveness
during synchronous provider parsing. Both profiles finish without owned process
survivors or captured-model directories left behind. A three-cycle source pilot
remains a separate calibration receipt.

| Installed profile | Elapsed | Peak summed RSS, two-window run | Mean owned CPU, single-window idle before / after layout |
| --- | --- | --- | --- |
| 1TCD | 267.31 s | 3.41 GiB | 0.077 / 0.105 cores |
| AlphaFold Q8WZ42 F2 | 289.75 s | 3.54 GiB | 0.082 / 0.114 cores |

Opened-checkpoint median RSS grows about 34/48 MiB from cycle one to eight;
closed-checkpoint medians grow about 114/133 MiB. All per-cycle values are retained.
Cycle one also contains deliberate occupied-origin failure/retry and page reload;
process warmup, allocator retention, two independent hosts and receiver overhead
are part of these observations. Finite RSS changes cannot attribute or exclude
a leak. RSS sums count shared pages in each process and are not unique physical
RAM; software rendering establishes no GPU, thermal or native-platform result.
The 3 s post-readiness windows are observation gaps, not proof of complete heap
settling. Larger declared scales, longer sessions and workload targets stay open.

Only receiving code changes in this increment. The inspected application/SOURCE
bytes still match the previously received noneditable diagnostic wheel; no new
package, dependency or provider patch is introduced. Actual consumed heads are
Viewer `0dcdd6ce` and MolSysMT `6deb0200`, distinct from the earlier provider epoch.
Twelve existing admission/lifetime Python cases and four owned-process Node
controls pass. The receiver now diagnoses early owned-child exit and drains both
output streams within a 256 KiB budget per child, recording truncation explicitly.
A synthetic failed display starts no product journey and supplies no rendering
qualification; other developer receivers retain their own adoption work.

The result closes a bounded repeated-lifetime receiving item, not S5.5, S2 or S6.
Supported mapping/lifetime contracts under #368 and human acceptance remain due.

## Chemical representation handoff

The previously prepared provider proposal is now published as
[Viewer #387](https://github.com/uibcdf/molsysviewer/issues/387) under the
maintainer's standing authority for technical reports in UIBCDF repositories.
It asks the provider to own or explicitly delegate source-bound optional 2D
depiction, preserve the exact chosen chemical declaration and define supported
inputs, limits and provenance. Issue delivery does not implement that capability,
adopt a renderer or close S4.3. Third-party publication keeps its separate prior
permission requirement.

The later [MolSysSketcher handoff](interactive_2d_component_0160.md) assigns general
2D molecular/interaction scenes to its separate development team under MolSysSuite
#199. Viewer #387 retains the earlier consumer request; supported 3D embedding
and correspondence remain under #368.
