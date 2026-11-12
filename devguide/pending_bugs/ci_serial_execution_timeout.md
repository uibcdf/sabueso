---
summary: Preserve the full public CI scope while avoiding the observed installed-lane execution timeout.
issue: uibcdf/sabueso#112
status: open
opened: 2026-11-11
area: [testing, ci, resources]
---

# Bounded CI pytest execution

## SDK266 memory stops and exact phase selection — 2026-11-12 UTC

The [SDK266 batch](https://github.com/uibcdf/sabueso/actions/runs/43254731665)
exposes overlapping large original readers under three outer workers. Linux
Python 3.11 and 3.14 stop at the original 6 GiB aggregate owned-tree ceiling;
their sampled RSS peaks are 6,509,154,304 and 6,546,112,512 bytes respectively.
No owned swap is observed. These are failed resource outcomes, not passing
scientific results. Linux Python 3.13 separately exposes the external child-ID
accounting problem documented in the [portability report](ci_windows_original_portability.md)
and delivered to [pytest-receptor #54](https://github.com/uibcdf/pytest-receptor/issues/54).

The source workflow now requests the launcher's explicit `--staged` execution.
An original discovery supplies exact node IDs. Ordinary modules retain the
requested outer concurrency; saved/history/original and the explicitly listed
large receiving modules run with one outer worker afterwards. Every case remains
in exactly one phase. Original options, native assertion failures, warning policy,
coverage and receptor arguments remain intact, with combined branch coverage.
Worker collection is checked against the plan before calls; incomplete, changed
or duplicate selections cannot pass. The original aggregate memory, scratch,
elapsed and host-reserve criteria remain unchanged. This is CI scheduling, not
B8 package staging or a new routine local execution default.

Four actual small phased receiver controls pass, including a native failing case,
combined coverage, collection drift before calls and caller-output protection.
The first resource/dependency/platform gate passes 69 cases. A real interrupted
representative attempt then exposes an empty-plan decoding error that loses the
original terminal reason. That attempt remains incomplete, with only its ordinary
105-case phase complete. The report-only follow-up initializes valid RUNNING
JSON, preserves actual stop identity/metrics when the plan is unavailable and
rejects a zero exit without a passing plan. All 73 final resource/dependency/
platform cases pass, including four new interrupted/missing-plan controls.
The original red stop control now reports the requested stop correctly.
The separately disclosed 253-case actual core stops at its 900 s elapsed ceiling
while receiving variants. Its ordinary 105-case phase completes, but the heavy
phase remains incomplete. Peak owned RSS is 2,633,617,408 bytes with zero owned
swap. The corrected supervisor retains `elapsed_limit` and metrics; neither this
stop nor the earlier 288-case interruption supplies complete integration PASS.
Representative real original reading remains separately recorded; these
controls do not establish full hosted completion or a new full-suite baseline.
Raw exact-source, provider and resource records are owned by #112/#148 under
`recovered_work/checkpoint_recovery_20261106/b7-ci-portability-resource-1/`.

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
At that initial observation other jobs continued; the terminal disposition below
now accounts for the complete batch. No source assertion failure is inferred.

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
scope. Actual successful macOS source receiving, complete failed-matrix recovery and
any later authorized exact-head recovery remain open. Keep the issue open and
consolidate observations before another remote request or public update.

## Terminal hosted outcome and bounded capacity diagnosis

The completed `74308ba` batch has four successful and fourteen failed jobs.
Twelve distinct resource reports stop at `owned_scratch_limit`; macOS separately
refuses RAM headroom before pytest. Coverage publication fails on the absent
`coverage-xml` artifact after the source gate stops. This is a downstream missing
input, not evidence of a separate upload-provider defect. All six full-capture
members, their bytes/hashes and ZIP integrity are verified. The twelve fresh
backend reports nevertheless cover all OS/Python producers and decode both
original payloads byte-exact at their recorded head. Failed full CI stays failed.

The newer lifetime fix remains locally tested; no successful full hosted recovery
is inferred. The macOS report still lacks actual available/physical RAM, so a
full-matrix repeat would leave that capacity uncertainty unresolved in advance.
The manual-only capacity workflow reproduces its ordinary source setup and then
uses `--preflight-only`. The same limits must fit; `PREFLIGHT_READY` means only
observed headroom, with no scratch, pytest, reservation or scientific acceptance.
RAM/disk/owned-stop refusal remains nonpassing and an explicit command is refused.
One 15-minute diagnostic job and retained capacity JSON provide a bounded next
scope; no run, retry or full-matrix dispatch is authorized by preparing it.

The [capacity-mode receipt](../evidence/ci_capacity_probe_checkpoint_20261112.json)
owns local tests, source/fixture integrity and exact hosted-observation limits.
Review actual macOS capacity before a consolidated final-head recovery. B7
independent acceptance and B8 remain separate.

## Measured macOS headroom and deferred validation

The single approved diagnostic at `d4f0171`,
[run 43154091218](https://github.com/uibcdf/sabueso/actions/runs/43154091218),
completes in one attempt with `REFUSED`. Setup, installed smoke/transport and
artifact retention succeed. No pytest or owned scratch is created. The full
six-member capture and actual artifact bytes/digest are verified, and the report
matches the logged JSON. The [receipt](../evidence/macos_capacity_observation_20261112.json)
retains the measured scope.

Physical RAM is 7 GiB. All seven samples over 30.078 s show 2.923–2.949 GiB
available; the final value is 2.929 GiB. One worker needs 2 GiB plus the 20%
host reserve of 1.400 GiB, or 3.400 GiB. The final shortfall is 505,944,474 bytes.
This confirms the configured admission mismatch during this observation only;
it measures neither scientific peak RSS nor another machine's capacity. The
cumulative swap counters alone establish no current swap activity.

The maintainer explicitly defers further macOS validation under
[#194](https://github.com/uibcdf/sabueso/issues/194). Identify an available Mac
and approve its resource scope, or explicitly review an alternative qualification
route. GitHub documents an arm64 M2 `macos-26-xlarge` configuration with 14 GB RAM
in its [runner reference](https://docs.github.com/en/actions/reference/runners/larger-runners);
eligibility and cost require a separate decision using the
[pricing reference](https://docs.github.com/en/billing/reference/actions-runner-pricing).
No larger runner has been configured or tested here.

Do not convert the deferral into a passing Mac result. Required source and
installed-artifact receiving and the CI/release consequences remain owned by #194
and #112. Existing workflows, safety reserves and scientific selections remain
unchanged. Independent Linux/Windows and B7 work can continue; B8 remains open.

## Extracted original archives outlive their modules — 2026-11-12 UTC

Initial observations cover nine completed source/installed jobs in the `74308ba`
batch reporting `STOPPED` with `owned_scratch_limit`: four Linux source lanes, Windows
3.13/3.14 and installed 3.11/3.12/3.14. Their actual logs and reports are retained
with the run. These are stops at the fixed 6 GiB temporary-file safeguard, not
passing pytest outcomes; RAM remained above the configured host reserve. This
does not establish that every scientific assertion before interruption passed.
The terminal accounting above now includes all twelve distinct scratch stops.

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

## Extracted member directories and clinical archive lifetime — 2026-11-12 UTC

The fresh local `f772e25` / SDK262 modern-history cohort stops at
6,486,823,024 sampled scratch bytes against its unchanged 6 GiB ceiling, with
4.898 GiB peak RSS and at least 49.265 GiB available RAM. Its incomplete stream
also contains the separate [test-guard isolation failures](history_guard_isolation.md);
neither the partial calls nor the resource stop qualify the complete source.

The stopped tree contains 335,032 files and 6,485,062,324 bytes. Repeated SDK243
member directories account for about 517 MB each, SDK230 about 406 MB each,
with smaller disease/protein/sequence directories and clinical tar copies.
These factory-created inputs outlive their final module consumer. The SDK243
fixture additionally has session scope, keeping imported fixture copies alive.
This is a further local accumulation mechanism, not a measured complete account
of the earlier hosted stops or a pytest/provider defect.

The five directory readers now release their own extracted directory and decoded
cache after module use; SDK243 also uses module scope. The clinical reader closes
its archive and unlinks its derived tar. Explicit `tmp_path_retention_policy=all`
preserves all six copies. Setup failures, failed per-case outputs, immutable
compressed inputs and caller outputs remain available. The lifecycle regression
uses all six real fixtures in both normal and deliberate-debugging modes.

The stopped run's logs, events, inventory and failure records remain under
`recovered_work/checkpoint_recovery_20261106/b7-current-full-checkpoint-1/`
and `b7-current-modern-1/`. Twenty-five known derived input directories were
removed after the owned run terminated and diagnosis finished; symlinks and
failed per-case outputs were preserved. The first cleanup stopped on a symlink
assertion; the corrected cleanup skips symlinks and completes. Original compressed
inputs remain unchanged. Complete corrected-source and hosted recovery are
separate pending checks; no resource ceiling or scientific predicate is relaxed.
