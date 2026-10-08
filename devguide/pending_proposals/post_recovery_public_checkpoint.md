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

The candidate's final staged file boundary, gates and exact-SHA CI are recorded
below when qualification completes. Earlier CI cannot qualify this candidate.

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
prove acceptance of this recovered checkpoint. This turn schedules revalidation;
it does not execute private science or close MOLI #3/#22/#36 consumer contracts.
