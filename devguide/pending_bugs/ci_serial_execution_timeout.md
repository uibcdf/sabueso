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

## macOS startup refusal and capacity reporting — 2026-11-12 UTC

The authorized `74308ba` batch has verified successful governance, but its
macOS26/Python3.14 source job `130906598267` refuses before pytest with
`Insufficient available RAM for one worker plus the host reserve`. The old
launcher assigns actual RAM and CPU fields after that decision, so its refused
report cannot establish actual capacity or transient versus persistent pressure.
Other jobs in the same batch continue; no source assertion failure is inferred.

GitHub lists the standard ARM macOS runner as three M1 CPUs and 7 GB RAM in its
[hosted-runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
That is a documented machine specification, not the unavailable live-RAM value
at this refusal. Preserve the actual raw report and log in
`recovered_work/checkpoint_recovery_20261106/b7-ci-recovery-74308ba-1/`.

The local correction records capacity before the budget decision and adds a
bounded first-launch settling interval: default 30 s, configurable 0–60 s, at
most five seconds between observations. Zero disables waiting. An impossible
physical budget refuses immediately; persistent shortage refuses at the deadline.
Owned stop files and interruption preserve refusal before pytest. The same
2 GiB per-worker and host-reserve criteria must fit before launching; no safety
margin, selected case or scientific predicate is relaxed. This wait is not a
repeat of pytest or a new remote execution.

The [new receipt](../evidence/ci_preflight_capacity_checkpoint_20261112.json)
qualifies all 36 current guard controls and three existing wiring/copied-receiving
controls locally. Synthetic pressure sequences establish behavior, not recovery
of the actual macOS runner. The complete 96-case copied child retains its own
scope. Actual successful macOS source receiving, the remaining current jobs and
any later authorized exact-head recovery remain open. Keep the issue open and
consolidate observations before another remote request or public update.

## Extracted original archives outlive their modules — 2026-11-12 UTC

Nine subsequently completed source/installed jobs in the same `74308ba` batch
report `STOPPED` with `owned_scratch_limit`: four Linux source lanes, Windows
3.13/3.14 and installed 3.11/3.12/3.14. Their actual logs and reports are retained
with the run. These are stops at the fixed 6 GiB temporary-file safeguard, not
passing pytest outcomes; RAM remained above the configured host reserve. This
does not establish that every scientific assertion before interruption passed.
Other jobs still require their actual outcomes.

A separate real-reader lifecycle regression reproduces five stale extracted
archives after their owning modules finish: SDK202/205/208/211/218 public inputs,
2,612,336,640 bytes in total. Module fixtures previously closed their readers but
left these reproducible plain tar copies until the whole pytest session ended.
Per-case `tmp_path_retention_policy=failed` cannot reclaim factory-created module
archives. This is an observed accumulation mechanism; the hosted resource report
does not identify its complete directory composition or establish this as its
only contributor.

Those five fixtures now close their readers and unlink only their own generated
tar after the final dependent consumer finishes. Their existing wrapper fixtures
forward the real pytest request. `tmp_path_retention_policy=all` retains the
copies for deliberate debugging. Original compressed inputs, failed-case outputs,
caller files, other shared/session fixtures and all scientific assertions remain
unchanged. No guard limit, concurrency policy, timeout or selected case changes.

The complete five-case lifecycle module passes, including genuine complete
reader/member checks, an intentionally failing child consumer, preserved failure
diagnostics and the explicit debugging route. Its initial sampled scratch peak is
1,720,372,496 bytes. The initial negative run remains failed; its five verified
derived archives were removed after review while its diagnostic records remain.
The final lifecycle control also exercises all three changed consumer wrappers.
The broader seven-module exploratory selection is deliberately stopped through
its own exact stop file after 1,521.541 s: long unchanged full-saving cases dominate
it. Its actual `STOPPED` disposition and partial event stream remain retained;
it adds no passing qualification. The complete targeted lifecycle and copied
payload wiring checks qualify the fixture change, with unchanged scientific
predicates verified separately by AST. No complete seven-module or full scientific
suite is claimed for this increment.
Actual hosted recovery and complete B7/B8 acceptance remain open under #112/#148;
retain one consolidated update rather than publishing another per-job report.
