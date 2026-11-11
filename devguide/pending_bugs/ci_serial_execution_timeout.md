---
summary: Preserve the full public CI scope while avoiding the observed installed-lane execution timeout.
issue: uibcdf/sabueso#112
status: open
opened: 2026-11-11
area: [testing, ci, resources]
---

# Bounded CI pytest execution

## Observed failure and separate unknown

At source `3c26790`, CI run
[43072436424](https://github.com/uibcdf/sabueso/actions/runs/43072436424)
reports that the installed public-provider Python 3.13 job exceeded its four-hour
execution limit. The complete downloaded log ends with cancellation, without a
successful pytest summary. Python 3.12 completes the same 107-module selection:
4,103 passed in 13,140.39 s, with four expected negative-acquisition warnings.
The job's authoritative annotation and the complete original logs are retained in
`recovered_work/checkpoint_recovery_20261106/b7-ci-bounded-execution-1/`.

The Python 3.14 job separately loses runner/server communication. Its underlying
host, network or resource cause is unknown. That failure does not establish a
pytest assertion failure, a memory problem or the same timeout. Preserve the
failed/cancelled outcomes and investigate complete exact-run logs; neither a
passing older minor nor later local checks supplies the missing hosted result.

## Local correction

`devtools/run_ci_pytest.py` wraps the original three CI pytest command branches.
Their literal case/marker/coverage/warning/receptor arguments and job matrices
remain intact. It requests at most three outer workers with `loadfile`, leaving
nested copied pytest clients serial. No case filter, automatic worker restart,
new scientific rule, runtime dependency or increased hosted timeout is introduced.
The existing pytest 9.2/xdist 3.8 `loadgroup` issue is avoided by using `loadfile`.

The launcher checks exposed CPU slots, CPU activity, available/physical RAM and
scratch disk space. It reduces workers for a small CPU allocation or insufficient RAM headroom;
high observed launch CPU activity selects one worker. Each worker budgets
2 GiB aggregate owned-tree RSS, including the launcher, workers and nested readers.
It keeps at least 20% physical RAM available, with a minimum 1 GiB reserve; an
explicit larger reserve supports responsible local qualification on this machine.
One worker is refused if its budget plus reserve does not fit. A detected Slurm
allocation is refused because this hosted profile does not interpret that scheduler.

Native/numerical pools remain one. Where supported, the owned process affinity
uses only the selected one/two/three slots and its priority is reduced. Every quarter
second the monitor samples owned-tree RSS, host available RAM, elapsed time and
filesystem free space; it also checks the owned pytest/TMP tree size. Linux owned
swap is measured and causes a stop; on other platforms that measure is explicitly
unknown. The default scratch limit is 6 GiB with a 2 GiB host disk margin. Files
created outside that owned tree are not claimed as measured scratch; free-space
checks also cover the working filesystem. These are sampled safeguards, not a
reservation or infrastructure-enforced hard memory/storage limits.

A resource stop returns nonzero and preserves the original failure/scratch.
An exact `<report>.stop` file requests an orderly stop without addressing process
IDs from another session. Finished/PID-reused entries are retired before sampling;
an owned reader surviving its successful parent beyond a short drain interval
also prevents PASS.
Only observed own descendants may be stopped. A successful command removes only
its disposable scratch; caller inputs and report paths are protected. Reports
include actual limits, peaks, duration, source SHA and tool/runtime identity,
stream into the job log and are retained as CI artifacts even when pytest fails.
Installed lanes use a 210-minute supervised limit within their unchanged
240-minute job limit; the source matrix keeps its existing outer timeout and a
five-and-a-half-hour supervised limit. This is a bounded attempt, not a hosted speed claim.

## Qualification and remaining work

The owning tests exercise actual nested readers, inherited-option isolation,
CPU/RAM refusal, original command arguments, successful and failing outcomes,
caller output protection and stopping an owned reader while a sibling survives.
A separate representative source gate covers original archives, copied receiving,
complete codec/chemical modules and combined branch coverage through the launcher.
The maintained checkpoint records actual counts and resource measurements only
after those gates complete. Earlier full-runtime qualification keeps its original
scope; it is not a repeated full suite for this development launcher.

Recover the applicable full exact-head CI/governance and original OS/Python,
public-installed, twelve backend-report and coverage responsibilities before
qualification. The original old-head batch authorizes no new head or retry.
Prepare one concrete request after local checks and record actual approval/run
identity before dispatch. B7 human/scientific/actual-agent/consumer acceptance and
B8 candidate/schema/staging/publication remain separate.
