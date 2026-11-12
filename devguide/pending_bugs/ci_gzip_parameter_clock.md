---
summary: Make collection-time gzip parameters deterministic across workers and supported Python minors.
issue: uibcdf/sabueso#112
status: open
opened: 2026-11-12
verification: reproduced
area: [testing, ci, public-fixtures]
---

# Gzip timestamps change collected parameter identifiers

The manual source CI at `14a3d1a` / SDK266 fails its Linux Python 3.12 collection
in [job 131309790775](https://github.com/uibcdf/sabueso/actions/runs/43254731665/job/131309790775).
Workers evaluate `gzip.compress(b"original")[:-4]` at different seconds and
collect different byte-valued parameter identifiers. The failure precedes test
execution and is neither a memory/scratch stop nor a scientific reader failure.
The other jobs retain their own outcomes; governance passes separately.

On Python 3.11–3.13, the omitted compression timestamp can use wall-clock time.
Routine Python 3.14 uses a deterministic default, so earlier local gates did not
expose the older-minor dependency. The workers correctly refuse different test
collections; no pytest-xdist or receptor defect is demonstrated by this failure.

A bounded AST audit finds eight affected parameter decorators: shared snapshot
reading, TCDB, HPO, PDBTM, 3did, MEROPS, Interactome3D and ProBiS. Each now passes
`mtime=0` explicitly. The same malformed/truncated payload and every scientific
assertion remain in place. Only synthetic parameter construction changes; no
production source, original input, provider, schema or execution limit changes.

A fresh two-worker control simulates the older default with different fixed
seconds per worker while honoring explicit `mtime`. Before correction, the actual
44-case selection fails collection with zero calls executed. After correction,
the complete eight-module selection passes **574 cases**, including all 44
affected controls, under different worker clocks and `--local-source-inputs`.
The first narrower green control passes nine cases and explicitly skips 35
local-original cases; it is not counted as complete original receiving.

The [local receipt](../evidence/gzip_collection_checkpoint_20261112.json) records
exact source/node maps, red/green accounting, unchanged test-body ASTs, all 52
protected originals and the current PyUnitWizard 0.29.5 environment epoch. The
legacy-clock control on Python 3.14 is not native Python 3.12 qualification.
A new exact-head CI/governance recovery remains required after the checked fix.
Do not retry the unchanged failing source or infer qualification from an older
job, a cancelled run or collection-only discovery.

Retain original hosted logs, complete receptor artifacts, source/provider maps
and the local clock instrument under #112/#148 in
`recovered_work/checkpoint_recovery_20261106/b7-hosted-recovery-sdk266-1/` and
`b7-ci-gzip-collection-1/`, for CI recovery and candidate review. No new public
issue comment is authorized by this local correction. B7 acceptance and the
installed/candidate release route remain separate.
