---
summary: Publish and qualify the recovered knowledge checkpoint before real-consumer revalidation.
issue: uibcdf/sabueso#112
status: active
opened: 2026-10-08
closed:
verification: inspected
area: [delivery, testing, consumer-acceptance]
blocked_by: []
supersedes: []
---

# Public code checkpoint after recovery and consolidation

Qualified code SHA: `dc4642414c46744f39d85cb666094b0d52dd705a`.
Exact-SHA CI passes 15/15 jobs and governance passes 1/1; the full local-original
suite passes 5,576 cases. Real private-consumer revalidation remains #132, and
SQLite warning cleanup remains #133. This is not a new release.

## Authorized scope

The maintainer authorized committing and publishing the previously validated
recovery/consolidation, then inspecting CI at its exact SHA. Implementation/input
contracts and guide/history changes are batched locally and pushed together.
This is a development code checkpoint, not a new release or installed-artifact
qualification. Published 0.13.0 and frozen schema 0.3.12 remain unchanged.

The reviewed input boundary is 49 repository-delivery files and 37 local-only
originals. No private consumer notebook or execution output is included. Original
local data and verified historical backups remain intact and ignored.

## Local evidence

The [consolidation receipt](post_recovery_consolidation_checkpoint.json) records
4,021 passing public-input tests with ten native skips and 5,574 passing full
local-input tests, pytest-receptor, 12 workers and editable Python 3.14.7.
All Python files still matched that tested set before the publication-only
regression described below. Those historical counts precede the new regression.

Publication review found that Git's Windows line-ending conversion could change
native fixture bytes. `.gitattributes` now marks `temp_data/**` as `-text`, without
changing original responses or runtime behavior. Original native whitespace is
exempt from Git whitespace checks; code, guides and the maintained notice retain
their checks, while response digests verify the wire inputs. A synthetic Git checkout under
`core.autocrlf=true` verifies unchanged native bytes. The delivery/licensing gate
passed **15 tests / 3.32 s**; lint/format checks passed for the new regression.
The original tested Python set is unchanged after excluding that added test.

The final file boundary, gates and exact-SHA CI are recorded below and in the
[machine-readable publication receipt](post_recovery_public_checkpoint.json).
Earlier CI cannot qualify this candidate.

## First published checkpoint and portability correction

Implementation/contracts/inputs were committed as
`e6fd384ec106253f4876f761d5a1262498148d6c`; guidance/history as
`4d771f38c709b4496139af43f2c4a6ac7ef38e6e`. Both were pushed together to main.
All 49 published fixture blobs retain their original hashes; all 37 protected
originals remain outside Git. The private pilot checkout remained clean.

Exact-head [governance](https://github.com/uibcdf/sabueso/actions/runs/37834575279)
passed through gh-run-receptor. The
[first CI run](https://github.com/uibcdf/sabueso/actions/runs/37834575148)
exposed two qualification gaps: Windows default decoding changed five UTF-8
source-term digests, and notebook validation lacked its `nbformat` test dependency.
Neither is a provider term change or altered original response.

A synthetic CP1252-default regression reproduces the false term rejection before
the fix. Delivery/catalog/test-collection metadata now uses explicit UTF-8.
Recovered fixture tests also read/write their declared UTF-8 inputs explicitly,
without host newline conversion; native bytes and parser/runtime semantics are
unchanged. Fifteen delivered UTF-8 public inputs would be misdecoded or rejected
under CP1252; fixture tests cannot borrow a host's default codec.
`nbformat>=5` is added to the CI environment and `test` extra solely for notebook
validation. The selected metadata/delivery/enricher gate passed 64 tests / 5.04 s
before the broader fixture-test portability adjustment. Final qualification uses
the correction's own gates and SHA; the first run is not a passing checkpoint.

The complete corrected local-input suite passed **5,576 tests / 179.55 s** with
pytest-receptor, 12 workers and Python 3.14.7. Its ten warnings exercise fixture
failure/truncation reporting. Registry, protected-input hashes, dependency
preflight, governance and Ruff checks also passed. Remote qualification was still
pending for that correction's exact SHA at this point.

The correction `434e43f78b6af8e1c075d64792b55768489f54b6` passed Linux/macOS
offline validation and all four installed public Ackredit consumer lanes. Windows
then exposed two test-setup errors: default pytest parameter IDs embedded complete
FDA/iPTMnet HTML responses and exceeded its 32,767-character environment-variable
limit. Explicit case names preserve all native input bytes and rejection assertions.
The two affected modules pass **93 tests / 2.76 s**; collection of all 4,033 public
cases confirms a longest node ID of 1,172 characters, including the ten native
cases that are intentionally skipped at execution. Full remote qualification
still required the corrected test-ID commit's own exact-SHA CI at that point.

The passing Linux Python 3.14.8 suite reports 66 unclosed SQLite connection
warnings, separately from six source-fixture warnings. The allocation/lifetime
owner is unconfirmed; [#133](https://github.com/uibcdf/sabueso/issues/133) records
bounded investigation rather than warning suppression. This is a remaining
cleanup item, not a failing functional test or private-consumer acceptance.

## Qualified public code checkpoint

The final corrected code SHA is
`dc4642414c46744f39d85cb666094b0d52dd705a`, committed and pushed to main.
Exact-head [CI](https://github.com/uibcdf/sabueso/actions/runs/37838441204)
passed **15/15 jobs**; exact-head
[governance](https://github.com/uibcdf/sabueso/actions/runs/37838441190)
passed **1/1**. Both were inspected with gh-run-receptor.

- Nine offline lanes passed **4,023 tests**, with ten native-only skips and 26
  online tests deselected: Linux/Windows on Python 3.11–3.14 and macOS-arm64 on
  Python 3.14. CI uses repository inputs, without the 37 local-only originals.
- Four installed public Ackredit receiving lanes passed **965 tests** each and
  the public workflow on Python 3.11–3.14, outside both provider/consumer checkouts.
- Ruff and measured coverage publication passed. Linux Python 3.14 reports the
  66 SQLite lifetime warnings tracked in #133, plus six source-fixture warnings;
  the other offline lanes report six source-fixture warnings.
- Final local-original qualification at this SHA passed **5,576 tests / 175.56 s**,
  with ten source-fixture warnings and no skips, using 12 workers and pytest-receptor.

All 49 delivered blobs and 37 protected originals retain their recorded hashes.
The 87 historical originals and backup were verified again; the stash is empty.
The private pilot checkout remains clean. Published release/schema versions remain
unchanged; CI-installed checkout tests do not qualify a staged Conda release.

This final receipt and maintained guide updates are documentation-only. Their
locally checked direct-push commit may use `[skip ci]` under `TESTS.md`; it does not
change the validated executable, packaging or test-input tree. The next code
checkpoint uses unskipped exact-SHA CI; release retains its staged recovery route.

## Return to consumer workflows

The maintainer explicitly requests a return to MOLI vertical-pilot use.
[#132](https://github.com/uibcdf/sabueso/issues/132) records acceptance after this
checkpoint's exact-SHA CI, before broadening sources or APIs. Existing private
Python/Jupyter workflows must retain original identity/support, unknowns, units,
sequence/residue axes, named rules, saved readers and acquisition/bibliography
sidecars; their scientific usefulness and measured cost need real use.

Keep the private checkout read-only and execution receipts/content/results in
a private workspace. Public findings contain only generic SDK/provider/shared
contract needs. Older private receipts and bounded public SDK examples do not
prove acceptance of this recovered checkpoint. This checkpoint schedules revalidation;
it does not execute private science or close MOLI #3/#22/#36 consumer contracts.
