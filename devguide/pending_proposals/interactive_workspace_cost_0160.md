---
summary: Reproducible workspace costs and guarded in-memory composition of unchanged original native packets.
issue: uibcdf/sabueso#153
status: open
opened: 2026-11-15
verification: implementation_receiving
area: [human-exploration, persistence, performance]
---

# Original workspace cost and guarded composition

## In-memory composition increment (2026-11-15)

Native Card packet preparation now has an internal in-memory boundary, reused by
Deck and application workspace composition. These packets remain unverified.
Every public save still independently restores its complete containing envelope
before creating the destination's temporary file. The final native verifiers,
logical/byte admission and atomic publication remain mandatory. No validation
cache or public validation-bypass flag is introduced.

Composition retains the former canonical JSON boundaries, including exact scalar
types and capture order, without intermediate Card/Deck files or nested gzip
round trips. Deck application state is shared by independent Deck saving and
workspace composition. Existing original formats and scientific reader rules
remain unchanged.

The paired unprofiled public workload observes **94.28 → 57.93 seconds** to save
(38.6% less elapsed time) and **29.73 → 29.66 seconds** to read and verify, using
the same inputs, two CPU-affinity slots and native-thread limits. Complete native
publication/context digests and exact original Deck return match. Peak sampled
RSS rises from about 0.39 to 0.45 GiB; the declared ceiling remains 4 GiB. These
are individual workload observations, not a general scaling or budget claim.

The [composition receipt](../evidence/interactive_workspace_composition_checkpoint_20261115.json)
owns final selected regression, original-producer, artifact and actual Qt receiving,
failed controls, exact source hashes and resource/cleanup records. S6.2 remains
partial: broader workloads, agreed targets and human acceptance stay open.

## Initial diagnostic checkpoint (7278d77)

Sabueso continues workspace/navigation work while the separate MolSysSketcher
team develops the supported 2D surface. The initial increment added a reproducible
developer diagnostic, not a runtime optimization. The [living plan](interactive_implementation_0160.md)
retains **20 done, 10 partial and 3 todo**; S6.2 and chemical depiction remain open.
The [source-bound receipt](../evidence/interactive_workspace_cost_checkpoint_20261115.json)
owns the observations, failed receiver, exact hashes and retained raw evidence.

## Workload and result

`devtools/measure_explorer_workspace.py` consumes the existing prepared public
five-occurrence Deck: P52270, source-bound BTS, a compound, a disease and the
repeated protein. It follows protein → BTS → native activity quantity → original
target assay/publication and saves the whole workspace. Setup is excluded from
the save/reopen timings; no source is queried.

The corrected unprofiled observation uses Python 3.14.10, two CPU-affinity slots,
single-thread native libraries and a monitored 4 GiB owned-RSS ceiling:

| Observation | Result |
| --- | --- |
| Save workspace | 98.92 s |
| Read and verify workspace | 26.88 s |
| Peak sampled owned RSS, complete execution | 438,214,656 bytes (about 0.41 GiB) |
| Minimum host available RAM | 49,195,986,944 bytes (about 45.8 GiB) |
| Saved gzip / decoded size | 8,301,578 / 31,652,045 bytes |

The process constructs no Card/Deck and reacquires no source while reopening.
Exact node/result references, pages, complete native publication/context digests,
the repeated entry, filtered Deck items and original Back survive. Input and saved
bytes stay unchanged. The owning 16-case workspace regression also passes through
published pytest-receptor 1.2.0 with a complete, integrity-verified artifact.

One observation does not establish an accepted budget, latency distribution or
regression against the earlier 84/25 s installed Qt cohort. Environment and
execution scope are recorded separately. No new Qt, independent-process, installed
artifact, platform, thermal, candidate or full-suite qualification is claimed.

## Profile and next optimization target

A preliminary cProfile execution observes **five native Card saves and fourteen
Card `_restore` calls**, plus two enclosing Deck `_restore` calls. Nested native
serialization, packing and verification dominate that instrumented run. Its
199.39 s save includes substantial instrumentation overhead and briefly overlaps
the baseline regression; do not compare it with unprofiled latency. Cumulative
function times overlap and must not be added.

This identified redundant-work investigation as the next step under
#153/#154. It does not prove that all calls admit equivalent components or may
be omitted. Any composition optimization must preserve independent native
verification, exact focal/capture/navigation binding, per-admission byte/logical
limits, caller isolation, atomic failure and historical meanings. A global cache
or a digest alone is not a substitute for those checks. Compare the same explicit
public workload before/after, then receive affected original-reader regressions
and actual Qt/installed behavior before claiming a product improvement.

## Failed control and reproduction

The first unprofiled receiver compared live and saved presentation text verbatim.
Saved text deliberately adds its original-reading banner, so that assertion
failed despite equal original view/result references. The corrected receiver
compares exact native content and navigation independently of the banner. The
failed execution and diagnosis remain separate from the passing observation.

Prepare inputs with `devtools/prepare_explorer_walkthrough.py`, then run
`devtools/measure_explorer_workspace.py --inputs <prepared-public-inputs>
--output-directory <new-owned-directory>` through the existing bounded observer.
Use a finite elapsed limit and check shared resources first. Optional
`--profile-save` writes profiling artifacts; that later command option has not
received a separate profiled execution in this checkpoint. Timings survive a
later failed content check, but only `observation.json` records a completed
passing journey. Resource logs and partial outputs are not qualification alone.

Useful public evidence has an owner and a review trigger in the receipt. Retire
only task-owned scratch and the isolated receptor overlay after their final use;
the shared environment is not modified.
