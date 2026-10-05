---
summary: Required coverage uploads recovered after the external Codecov incident.
issue: uibcdf/sabueso#119
status: resolved
opened: 2026-10-05
closed: 2026-10-05
verification: observed
area: [ci, coverage]
blocked_by: []
supersedes: []
---

# Required coverage upload blocked by external TLS incident

Archived on 2026-10-05 after verified consumer recovery: all four exact-SHA
workflows pass, and their logs confirm accepted uploads. The current state is
recorded in [CHECKPOINT.md](../CHECKPOINT.md); the observations below preserve
the incident history and do not describe a current Sabueso blockage.

## What

The initial Codecov attempts failed before uploader execution. The last failed
attempt downloaded and verified the CLI but failed at coverage ingestion. The provider owns
the HTTPS incident in [codecov-action#1975](https://github.com/codecov/codecov-action/issues/1975);
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

The next ordinary code SHA `1a49a5c73f0893cd5c2ae55958851647ead71244` reproduces
the incident in [CI 37279215592](https://github.com/uibcdf/sabueso/actions/runs/37279215592):
all 14 scientific/test/integration/quality jobs pass, and
[governance 37279215549](https://github.com/uibcdf/sabueso/actions/runs/37279215549) passes.
At 07:52:55 UTC the same CLI download fails with curl 35 / TLS handshake error;
at 07:53:05 the absent signature produces the downstream GPG error. The XML
artifact is retained, and whole-workflow CI remains failed. Local 1,847 offline/
536 installed-public-provider cases and applicable quality/docs gates pass. The
[updated consumer receipt](https://github.com/uibcdf/sabueso/issues/119#issuecomment-5990468852)
retains exact code/result boundaries; no additional retry is attempted during
the unrecovered incident.

Both public GH Run Receptor 1.1.1 and editable 1.2.0+3 replay prioritize the
secondary GPG line as the sole root cause. The original logs establish the
download-first sequence; the actionable diagnostic-ranking improvement is
[gh-run-receptor#59](https://github.com/uibcdf/gh-run-receptor/issues/59).
That reporting defect does not cause the TLS failure or change GitHub's conclusion.

The oligomer checkpoint `b5bd5f0484188cd29bd13cc585cda11c44173fdc` passes all
14 scientific/test/integration/quality jobs in
[CI 37285490631](https://github.com/uibcdf/sabueso/actions/runs/37285490631), and
[governance 37285490470](https://github.com/uibcdf/sabueso/actions/runs/37285490470) passes.
Local 1,888 offline/577 installed-public-provider cases and applicable gates pass.
At 08:54:13 UTC the CLI download completes (v11.3.1), its GPG signature is good,
and integrity verification passes. Upload execution starts at 08:54:14; three
request retries end at 08:54:18 with
`Request failed after too many retries` at
`ingest.codecov.io/upload/github/uibcdf::::sabueso/upload-coverage`.
The log does not expose the underlying request/TLS reason. This is partial
download recovery, not successful ingestion; the provider thread independently
reports an [unresolved ingestion endpoint](https://github.com/codecov/codecov-action/issues/1975#issuecomment-5991102836).
The [consumer receipt](https://github.com/uibcdf/sabueso/issues/119#issuecomment-5991281399)
and [upstream update](https://github.com/codecov/codecov-action/issues/1975#issuecomment-5991281807)
retain the changed symptom. The XML artifact remains retained and
whole-workflow CI remains failed. No integrity/TLS bypass or extra failed-only
retry is introduced while ingestion remains unavailable.

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
- Recover the later code checkpoint independently, preserving its SHA:
  `gh run rerun 37279215592 --failed --repo uibcdf/sabueso`.
- Recover the oligomer checkpoint separately after ingestion is available:
  `gh run rerun 37285490631 --failed --repo uibcdf/sabueso`.
- Verify actual upload and whole-workflow success, preserve the exact-SHA receipt
  and update #92/#108/#112/#119 and the checkpoint.

## Resolution

Consumer recovery was verified on 2026-10-05. The versioned agreement code SHA
`30331f26418db8b4774f6f9736581976ea838e8f` passes all 15 jobs in
[CI 37290854247](https://github.com/uibcdf/sabueso/actions/runs/37290854247) and
[governance 37290854288](https://github.com/uibcdf/sabueso/actions/runs/37290854288).
The coverage job verifies CLI integrity, sends 103,749 bytes and records
`Upload queued for processing complete` at 09:44:06 UTC. This confirms accepted
upload, not completion of downstream dashboard processing.

Only the failed coverage jobs were rerun for the three earlier checkpoints:

| Code SHA | Run / attempt | Accepted upload (UTC) | Bytes | Workflow |
| --- | --- | --- | --- | --- |
| `7f980c02b7e335b8904b0a9021211d846ed378a0` | [37272400000](https://github.com/uibcdf/sabueso/actions/runs/37272400000/attempts/3) / 3 | 09:45:27 | 103,009 | 15/15 success |
| `1a49a5c73f0893cd5c2ae55958851647ead71244` | [37279215592](https://github.com/uibcdf/sabueso/actions/runs/37279215592/attempts/2) / 2 | 09:45:33 | 103,181 | 15/15 success |
| `b5bd5f0484188cd29bd13cc585cda11c44173fdc` | [37285490631](https://github.com/uibcdf/sabueso/actions/runs/37285490631/attempts/2) / 2 | 09:45:34 | 103,468 | 15/15 success |

Each log confirms the exact-SHA Codecov commit URL, bytes sent and completed
queue acceptance. The original scientific jobs, SHAs and measured XML artifacts
remain unchanged. No scientific/runtime/package/fixture or CI-policy change,
TLS bypass or integrity bypass was made for this incident. Consumer #119 is
resolved; this receipt does not assert closure of the provider's broader incident.
The independent diagnostic-ranking report gh-run-receptor#59 remains open.

Final receipts: [consumer resolution](https://github.com/uibcdf/sabueso/issues/119#issuecomment-5992255236)
and [provider feedback](https://github.com/codecov/codecov-action/issues/1975#issuecomment-5992257742).
Related gate boundaries were updated in [#92](https://github.com/uibcdf/sabueso/issues/92#issuecomment-5992255961),
[#108](https://github.com/uibcdf/sabueso/issues/108#issuecomment-5992256565) and
[#112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-5992256973).
