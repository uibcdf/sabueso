---
summary: Public CI observed stable micromamba binary lookup failures before tests; provider report needs maintainer handoff.
issue: uibcdf/sabueso#112
status: open
opened: 2026-11-05
verification: completed_failed_job_logs_and_current_public_release_metadata
area: [ci, provider-access, coordination]
---

# Intermittent micromamba binary lookup before environment creation

Public Sabueso [CI 42047120046](https://github.com/uibcdf/sabueso/actions/runs/42047120046),
attempt 1, source `2be4358d12a5f38ffccdf0cb85fd36750802a95d`, has three observed
setup failures. The workflow is still running at this observation; no final run
or successful retry is inferred. This is separate from `0881d8a`'s stale catalog.

Two completed failed logs were inspected through gh-run-receptor:

- [Linux installed consumer, Python 3.11](https://github.com/uibcdf/sabueso/actions/runs/42047120046/job/127312995193):
  setup reports no micromamba binary for release `2.10.0-0`, platform `linux-64`,
  at 14:39:37.717 UTC. Cleanup later reports `Unexpected end of JSON input`.
- [macOS arm64 codec, Python 3.12](https://github.com/uibcdf/sabueso/actions/runs/42047120046/job/127312995207):
  the analogous `osx-arm64` binary lookup fails at 14:39:51.557 UTC, followed by
  the cleanup parse error. The Python 3.11 codec job also fails during setup;
  its individual log is not yet inspected.

All use `mamba-org/setup-micromamba@v3.2.1`, without an explicit binary version.
The [action documentation](https://github.com/mamba-org/setup-micromamba#micromamba-version)
states that the default selects the latest stable release. A later GitHub API read
of [release 2.10.0-0](https://github.com/mamba-org/micromamba-releases/releases/tag/2.10.0-0)
shows both named assets exist; this does not recover the response seen by the
failed action. A transient API/download/asset lookup is a hypothesis. Missing
packages, a broken solver or a generally absent release are not established.

## Provider handoff

**External publication is not authorized.** The maintainer explicitly requires
prior approval of the destination, action and concrete material before any
third-party publication, including comments and remote drafts. This applies
regardless of credential availability. The attempted issue should have awaited
that approval; the API rejection is not a substitute for the human permission.
Keep this report internal for review or a human-owned submission decision.
See [MolI #80](https://github.com/uibcdf/moli/issues/80) and
[Sabueso #187](https://github.com/uibcdf/sabueso/issues/187).

An attempted report in `mamba-org/setup-micromamba` was rejected with GitHub API
403, `Resource not accessible by integration`; no provider issue was created.
The Sabueso #112 handoff retains these public links and a proposed request to
review bounded lookup recovery/diagnostics and cleanup after failed setup.
External delivery awaits explicit permission or the human's submission decision.
No provider source, local environment or workflow pin is changed here.
Review actual retry/new-source results before treating the blocker as recovered.

The compact receptor reported only the later cleanup error. That independently
actionable diagnostic shape is delivered to the existing provider issue
[gh-run-receptor#81](https://github.com/uibcdf/gh-run-receptor/issues/81#issuecomment-6661075657).
Its owner controls further triage and implementation. A provider report or a
passing unrelated job does not qualify the Sabueso run.

Owned evidence: `recovered_work/component_row_reading_148_20261105/`, owner
#112/#148/#173, review on CI recovery or the next source checkpoint. Protect active
captures and the preceding source's original failed-attempt records.
