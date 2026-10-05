---
summary: External Codecov TLS incident blocks required coverage publication.
issue: uibcdf/sabueso#119
status: open
opened: 2026-10-05
closed:
verification: observed
area: [ci, coverage]
blocked_by: [codecov/codecov-action#1975]
supersedes: []
---

# Required coverage upload blocked by external TLS incident

## What

The final Codecov upload fails before uploader execution. The provider owns the
HTTPS incident in [codecov-action#1975](https://github.com/codecov/codecov-action/issues/1975);
Sabueso's [upstream receipt](https://github.com/codecov/codecov-action/issues/1975#issuecomment-5989530840)
and consumer [#119](https://github.com/uibcdf/sabueso/issues/119) preserve the evidence.

## How / evidence

Exact code SHA `7f980c02b7e335b8904b0a9021211d846ed378a0` has 14 successful
scientific/test/quality jobs in [CI 37272400000](https://github.com/uibcdf/sabueso/actions/runs/37272400000),
and successful [governance 37272400114](https://github.com/uibcdf/sabueso/actions/runs/37272400114).
The final `Publish default-branch coverage` job fails in both the initial attempt
and failed-only retry. The measured `coverage-xml` artifact remains available.

The pinned action is v7.1.1 (`303a32d7a59b442fa8d48b6a1cc6825c09c847a5`),
Wrapper 0.3.1, Ubuntu, CLI `latest`, OIDC and `fail_ci_if_error: true`.
At 2026-10-05 06:33 UTC downloading `cli.codecov.io/latest/linux/codecov` fails
with curl error 35 / OpenSSL TLS handshake failure. The absent signature file
then produces a secondary GPG error. Whole-workflow CI is failed, not green.
Local 1,834 offline/523 installed integration cases, the public workflow and
applicable source/schema/docs gates pass; #92/#108/#112 retain that distinction.

## Why

An external service incident must remain visible rather than be counted as passing
CI or release evidence. Coverage publication remains a required gate.

## Alternatives

The failed-only retry on the same SHA reproduces the incident. The provider issue
includes a consumer report that installing through PyPI still fails at the ingest
endpoint; the pinned action also documents that route as bypassing binary integrity
checking. No ineffective route change is adopted. TLS/integrity verification and
the required failing upload gate remain enabled.

## Acceptance criteria

- The provider restores its HTTPS download/upload endpoints.
- Repeat only the failed coverage job for the original code SHA:
  `gh run rerun 37272400000 --failed --repo uibcdf/sabueso`.
- Verify actual upload and whole-workflow success, preserve the exact-SHA receipt
  and update #92/#108/#112/#119 and the checkpoint.

## Resolution

Pending provider recovery. No scientific/runtime/package/fixture or CI-policy
change is made for this external incident.
