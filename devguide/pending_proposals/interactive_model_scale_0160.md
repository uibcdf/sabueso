---
summary: Larger public model conversion failures, bounded longer-session receiving and owned process-memory observations.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-15
verification: bounded_development_experiment
area: [human-exploration, visualization, lifecycle, resources]
---

# Larger public models and longer sessions

This extends the [eight-cycle lifetime observations](interactive_model_lifetime_0160.md#extended-bounded-observations-2026-11-15)
under S5.5/S6.2 of the [living implementation plan](interactive_implementation_0160.md).
It does not reopen the host comparison or establish a supported Viewer embedding
contract, platform qualification, accepted workload budget or version acceptance.

## Declared larger inputs and provider failure

Two unmodified deposited coordinate files were retrieved from RCSB on 2026-11-15
UTC, with explicit 16 MiB encoded / 64 MiB decoded bounds. RCSB's
[usage policy](https://www.rcsb.org/pages/usage-policy) declares the coordinate
archive and API data CC0. Credit the depositors and RCSB PDB/wwPDB. Exact original
files, API metadata, policy observation, hashes and acquisition sizes remain in
the owned receiving evidence; they are not new frozen Sabueso fixtures.

| Input | Source-declared deposited atom count | Encoded / decoded bytes | Direct conversion result |
| --- | --- | --- | --- |
| [3WU2](https://www.rcsb.org/structure/3WU2) | 54,036 | 1,403,413 / 6,185,581 | `KeyError: 31` in nonpolymer classification |
| [5XNL](https://www.rcsb.org/structure/5XNL) | 98,986 | 2,529,055 / 11,380,481 | `KeyError: 9` in polymer classification |

These counts describe deposited source records, not successfully imported native
atom inventories. No biological assembly is expanded and no relationship with
the P52270 Card is inferred. Both failures reproduce directly in
`molsysmt.convert(path, to_form="molsysmt.MolSys")`, without Sabueso, Qt or Viewer,
on actual source `6deb0200`. The 3WU2 failure also reproduces through Viewer's
public load surface on `0dcdd6ce`. Direct conversion peaks at about 0.22/0.27 GiB;
the failures occur before rendering and do not establish a resource limit.

[MolSysMT #763](https://github.com/uibcdf/molsysmt/issues/763) owns the defect and
the exact public reproduction. The current atom-site loop reuses `entity_index`
as both a current index and an allocation counter. Revisiting an earlier entity
can make the next new entity collide with an existing index. Replaying that
assignment on original atom-site IDs produces 41 IDs/31 distinct indices for
3WU2 and 42/11 for 5XNL. These are diagnostic replays, not successful native
conversions or a claim of silently wrong output. Original entity declarations
are present and first-occurrence order matches the entity table. Provider review
must preserve explicit source identity and the complete input.

The actual 3WU2 Qt attempt retains the Card reading and exposes model
unavailability. Its original positive-rendering receiver waited for 60 seconds
after the terminal model error. The corrected receiver detects that state and
preserves the diagnosis immediately: complete trials take about 81.33 s versus
21.29 s in these single bounded observations. Both remain failed rendering
attempts. No provider fix, source filtering, input rewriting or dependency update
is applied to manufacture a passing larger-model case.

## Longer independent control and memory method

The separate installed 1TCD control declares twelve runtime close/reopen/draw
cycles, twenty layout cycles, two 120 s single-window idle windows and 10 s
observations after every closed/opened transition. The runtime portion retains
a second independently owned Qt window. It uses the same immutable initial-input,
fixed-origin, stale-capability, fresh-view and exact Knowledge checks as the
earlier profiles. These are bounded observations, not a generally long-session
memory guarantee. Knowledge probes run after readiness, not during synchronous
provider parsing.

The [source-bound receipt](../evidence/interactive_model_scale_checkpoint_20261115.json)
receives all **32 checks and twelve cycles** in **611.49 s**, with a sampled
summed-RSS peak of **3.54 GiB** and a minimum of about **41 GiB** host-available RAM.
One native thread and four-CPU affinity are retained under a 10 GiB sampled
ceiling. All owned processes and captured-model/launcher directories retire.
A separate actual 3WU2 unavailability journey passes six checks: visible failure,
retained Knowledge, original source navigation, native capture and unchanged
inputs. This qualifies failure isolation, not drawing of the larger model.

The task-owned observer now offers opt-in process snapshots every 5 or 15 seconds,
separate from its 250 ms summed-RSS guard. It samples only tracked PID/creation-time
pairs, with available RSS/USS/PSS, and never stores command lines or capabilities.
Denied/missing fields remain explicit and incomplete totals remain null. Execution
families use reported argv: forked WebEngine workers can retain zygote arguments,
so that label cannot identify actual renderer ownership. All those workers are
grouped together for comparison. The Python service combines Knowledge and
Viewer; browser processes combine frame content. These are non-atomic OS samples,
without provider-heap, GPU-allocation or unique whole-machine-RAM attribution.

Correlate only snapshots wholly inside a declared phase and retain sample counts,
missingness, medians and first/last checkpoint changes. The first runtime cycle
also contains deliberate occupied-port failure/retry and page reload. Allocator
retention, process warmup, caches and receiving overhead remain possible
contributors; positive retention does not diagnose or exclude a leak.

The longer trial retains 116 detailed snapshots, with no unavailable fields.
The two idle phases each contain 23 complete snapshots and average approximately
0.078/0.091 owned CPU cores. Runtime checkpoints contain only one or two detailed
snapshots each; their medians have that limited scope. Comparing opened cycle one
with opened cycle twelve gives the following OS-memory changes:

| Reported execution family | Change in median USS | Change in median PSS |
| --- | --- | --- |
| Knowledge and molecular Python services | +10.98 MiB | +1.71 MiB |
| Qt application processes | +8.44 MiB | +7.50 MiB |
| WebEngine workers, grouped across reported argv roles | +81.42 MiB | +81.90 MiB |
| Receiver | +6.60 MiB | +6.31 MiB |
| Display | 0.00 MiB | -0.08 MiB |
| Complete sampled tree | +107.43 MiB | +97.35 MiB |

The 250 ms summed-RSS median grows about 109 MiB across those opened checkpoints
and 182 MiB across closed checkpoints. WebEngine is the largest changing group
in this finite run; this does not identify an iframe, component or leaked object.
PSS can change when other processes share pages. The earlier eight-cycle 1TCD/AF
profiles retain their own inputs and timing/sampling epochs; these results are
not a direct performance comparison or a reason to change the selected host.

The native split-layout capture also shows long literal source headings requiring
horizontal scrolling. A readable compact heading that keeps the full original
reference is a navigation-polish follow-up under #154, not a change delivered or
a human acceptance verdict in this resource increment.

## Source, checks and continuation

Only developer receiving tools change. Inspected Sabueso runtime/SOURCE hashes
still match the earlier received diagnostic wheel, SHA256
`f106458434dd30169218085e31d9f3b292427d5c2390da0916bc26f704fda400`.
The noneditable wheel is received outside the checkout, with local editable
Viewer `0dcdd6ce` and MolSysMT `6deb0200` verified separately from stale version
metadata. No new package build or provider adoption is implied.

Five memory-observer cases protect unavailable data, PID reuse, disclosure and
real OS sampling; twelve existing molecular admission/lifetime cases and four
synthetic owned-child Node controls pass. Python gates use the isolated published
receptor. The two short lightweight regression runs overlap the first idle
window; these shared-host observations are not an isolated CPU benchmark.

Larger-model rendering remains unqualified pending #763 and subsequent receiving
of the reviewed provider fix. Supported model/index mapping, nonempty selection,
pending callbacks/background/shared-session contracts and human acceptance retain
their existing owners under Viewer #368 and Sabueso #154. S5.5/S6.2 remain partial;
the main ledger remains 20 done / 10 partial / 3 todo. Exact-final-source
full/candidate/hosted recovery stays under #154/#153/#112; no workflow, release,
public package or new supported platform is selected.
