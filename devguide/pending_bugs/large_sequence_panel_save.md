---
summary: Shared complete source support removes the reproduced titin save-preparation duplication; qualification remains scoped.
issue: uibcdf/sabueso#167
status: locally_corrected_hosted_receiving_pending
opened: 2026-11-05
area: [exploration-persistence, workload, human-exploration]
---

# Full public titin sequence-panel saving

The original failure below is retained unchanged in its receipt. The current
candidate factors complete support under `retained_link_support@1` and generic
navigation `retained_context_links@7`, with independent saved format @11. The
same complete public workload now finishes under the original 512 MiB/60-second
guard, without changing byte budgets or replacing the full Card with a subset.
Historical/mixed/copied receiving and final-source qualification are recorded in
the [correction receipt](../evidence/shared_link_support_20261105.json).

## Original observation

**Observed limitation**, source `7c3ecff`, actual shared editable SDK
`0.14.0+178.g7c3ecff`: saving a fresh full Q8WZ42 sequence panel crosses the
owned 1 GiB RSS ceiling before producing a file or a decoded-byte refusal.
This is not a proven regression from the range-alias change and does not imply
that Card construction or ordinary navigation needs that memory.

The complete native public UniProt record is 486,890 bytes: 1,317 features produce
26 mapped fields, 1,489 source assertions and 215 relationships. In the diagnostic
worker, mapping and full Card construction finish in 0.619 seconds; capture,
the 17-item sequence panel and a 2,546-byte compact length frame finish in
0.990 seconds, at 118,054,912 bytes RSS. These are one-worker observations, not
accepted general performance budgets.

The following full same-snapshot save is stopped by the external supervisor
after 17.97 seconds, sampled peak 1,079,951,360 bytes; the initial pytest attempt
also stops at its1 GiB ceiling. Neither process uses swap. A third instrumentation
run uses a stricter512 MiB guard and stops after 8.11 seconds at 552,669,184 bytes.
It logs entry into `_prepare` and no return, with no `_seal` or `_restore`
entry. This localizes growth to preparation of retained views/support/navigation;
the specific dominant allocation is not profiled yet. Sampled guards can observe
a small overshoot before terminating only their owned process group.

`save_exploration` calls `_prepare` before sealing, original verification, JSON
encoding, decoded-byte admission and compression/write. The observed stop is
therefore not evidence that changing a compressor would correct preparation.
Default file-size budgets are not an independent RSS guarantee. No budget is
raised, disabled or silently applied to discard retained content.

The [archive control](../pending_proposals/alphafold_archive_fragment_control.md)
retains this original public input. Its passing four-field sequence-only Card
is explicitly a reference-correspondence control; it does **not** make the full
save workload passing. The complete source record, failed guards, stage logs and
bounded diagnostic producers remain under
`recovered_work/alphafold_archive_control_20261105/`, owner #167/#148/#112,
review at the capacity correction and before 0.15.0 workload acceptance.

The original next step was to profile bounded preparation, identify repeated materialization and
ownership costs, and correct them while preserving original support, complete
inspection and frozen file meanings. Retain visible size-limit refusal and
explicit caller overrides. Recheck the full public case under a declared guard,
genuine historical files, human/agent parity and the ordinary supported workloads
before accepting the correction. Broader workload and researcher acceptance
remain pending.

The [standalone guarded reproducer](../evidence/check_large_sequence_save_20261105.py)
uses the original public record, disables source queries and monitors only its
fresh worker process group. On Linux, with the existing psutil development
dependency, run:

```bash
python devguide/evidence/check_large_sequence_save_20261105.py --output NEW_DIRECTORY --rss-limit-mib 512 --seconds 60
```

Its `resource_stop`/exit2 is the retained failing observation, not a passing save.
The output directory contains stage logs, exact source/SDK/input hashes, resource
ceilings and actual measurements. A later correction must turn this into a
qualified full-workload result, rather than raising the guard or replacing it
with the smaller reference control.

The [published guard receipt](../evidence/public_large_sequence_save_20261105.json)
retains source/SDK/input hashes, the 512 MiB controller result and its original
worker stage log. The measured archive/reference scientific control is separate.
