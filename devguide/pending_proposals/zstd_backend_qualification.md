---
summary: Qualify native and backported Zstandard without changing Card persistence.
issue: uibcdf/sabueso#178
status: living
---

# Zstandard backend qualification (#178)

The [codec comparison](card_compressor_comparison.md) favors Zstandard as a
balanced candidate. `devtools/probe_zstd_backend.py` qualifies native
`compression.zstd` on Python 3.14 and pinned `backports.zstd==1.8.0` on 3.11–3.13.
The backport has the same API and explicitly excludes 3.14; missing native support
on 3.14 remains unavailable rather than selecting an incompatible distribution.
See the [backport metadata](https://pypi.org/project/backports.zstd/1.8.0/).
This standalone engineering tooling changes no package dependency or runtime.
Future production optional binding must go through DepDigest.

Two genuine producer fixtures retain native 3.14 and backport 3.11 frames for
fixed synthetic typed values and the unchanged original literal reading. Their
[provenance and byte hashes](../../tests/tools/data/README.md) are pinned.
Every probe reads both originals, then emits fresh frames with backend/library,
Python/platform, source and tool identities. Decoding checks exact original
bytes, checksum, frame completeness, trailing/concatenated data and expansion,
with a 1 MiB window and known payload lengths. These fixed-payload guards qualify
the binding; they are not a general compressed Card reader or its public policy.
Future codec versions need not emit identical compressed bytes.

Actual Linux 3.11.11/3.12.12/3.13.15 probes pass with verified PyPI wheels,
backports.zstd 1.8.0 and libzstd 1.5.7. Existing interpreters ran with `-I -S -B`,
loading only the extracted owned wheel and helper; no environment was modified.
This establishes isolated backend behavior, not installed-Sabueso or platform
qualification. At the helper checkpoint, CI runs probes in all nine source lanes
and three standalone older-Python macOS ARM64 lanes. Its twelve fresh producer reports must be read
through the native consumer after full exact-head receptor verification. The
expanded CI has 18 jobs, retaining all thirteen pytest lanes. At `1fdb771`,
[CI 18/18](https://github.com/uibcdf/sabueso/actions/runs/41585285748) and
[governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/41585285886) pass.
All full-capture hashes/steps and thirteen actual summaries are verified; native
reading of all 24 fresh frames succeeds. Nine source lanes each pass 6,599 cases;
four installed public-provider lanes each pass 1,470. See the
[verified closeout](https://github.com/uibcdf/sabueso/issues/178#issuecomment-6609265892).

The unskipped checkpoint recovers both preceding experimental-helper commits
through [the deferred-CI ledger](deferred_ci.md), after all applicable gates pass.
Owned local reports, original producer snapshots, wheel hashes and resource logs
live in `recovered_work/zstd_backend_178_20261103/`; owner #178/#167/#112, review at
production codec adoption. Remove only owned extracted wheels/build scratch after
use, retaining provenance and results. No provider queries or private data occur.

At this helper checkpoint public compression remained unimplemented. The following
[production transport](exploration_file_transport.md) needs separate qualification.
Keep plain JSON, original @1–@6 bytes,
trusted digests, complete history/support and frozen readers. Production work
still needs an explicit codec surface, DepDigest, bounded complete-frame decoding
with deliberate overrides, atomic saving and receiving/quantity/source regression
gates. #178/#167 stay open and 0.15.0 consolidation remains paused.
