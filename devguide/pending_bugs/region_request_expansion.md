# Region request expansion before allocation (#171)

Owner: [#171](https://github.com/uibcdf/sabueso/issues/171), coordinated with #148
human/agent acceptance and #167 workload costs. Development implementation,
2026-10-29. Source-bound qualification and publication receipts belong to #171;
selected local checks are not a full-local-suite or release receipt.

## Observation and correction

The former argument normalizers and structural options expanded inclusive ranges
before checking original reference bounds. Code inspection established the missing
allocation guard; no host-memory exhaustion experiment was performed.

`core/region_requests.py` now validates compact terms, counts their exact interval
union, checks original admitted canonical endpoints, and only then expands.
Public `region_budget` is a positive non-boolean integer or explicit `None` for no
application ceiling. Both raw terms and distinct requested positions across
recipient protein Cards are bounded. A refusal reports the applicable budget,
size and override route; a raw-complexity refusal explicitly says distinct
positions were not counted. No truncation or sampling is permitted.

Restrictive SMonitor capture scopes omit request-derived sizes/budgets from
diagnostics while preserving the stable error identity/reason. Detailed receiving
retains actionable budget/override information.

The scope covers Card structures/tables, Deck inventories/structural explanations,
human topics/region questions, agent selection, native backend calls and skipped
digestion. A scoped receiving wrapper establishes the effective budget before
ArgDigest and propagates it to nested readers. It resets after success/failure.
Workload overrides preserve argument/scientific validation and original support.
Unavailable reference support remains unknown, never a negative finding.

Scientific result identity, cache reuse, source records and frozen historical
readers remain unchanged. New saved lookup receiving is separate from opening
the original artifact. Native dictionary results and human views expose a defensive
`.workload` receipt; agent access exposes `last_workload` separately from its cached
selection. Receipts retain the complete caller region and effective policy. Existing
saved formats/flat table lists do not serialize these live receipts; saved science
never acquires an invented original workload record. No stored schema change.

## Default and bounded measurements

The default 100,000 is an operating budget, not a biological maximum. A bounded
Python 3.14 `tracemalloc` observation of request normalization at that boundary
gave 3,993,432 peak traced bytes /0.0464s for one inclusive range, 7,998,008 bytes
/0.2635s for individual positions and 7,873,296 bytes /0.1411s for duplicate terms.
Caller input construction was outside tracing. These local observations motivate
a finite normalization default; they do not establish full-process, scientific
materialization or researcher latency/memory guarantees. #167 and actual #148
workloads retain their separate acceptance routes.

## Verification status

The initial implementation passed 1,247 cases across 47 files /724.27s, serial
through pytest-receptor with fatal runtime/unclosed-SQLite/unraisable warning
guards. Sampled owned RSS peaked at 886,398,976 bytes (845.3 MiB), available host
RAM stayed at least 16,452,972,544 bytes, and owned swap remained zero. One
expected public STRING truncation warning remained visible. An earlier attempt
stopped at 227 passes with EDQUOT in a temporary-file write; it is not qualification.
The same failing test passed with an owned repository basetemp, then the complete
selected gate passed there. The sandbox's intermittent temporary mount EDQUOT
also required narrowly scoped execution fallback; its root cause is unconfirmed.

Final refinements centralize the default, preserve required capture attributes,
exclude nonproteins from mixed-Deck receiving counts and respect restrictive
SMonitor diagnostics. The final owning/diagnostic/argument/Deck/explanation gate
passes 135 cases /37.00s, including all 50 owning regressions and actual requests
above the 100,000 default under both finite and unlimited overrides. The earlier
1,247-case receipt belongs to its retained initial source; it is not relabeled as
a full or final-source local run. Frozen reader/mapper hashes (11 files) are
unchanged. Both added public guide blocks execute offline; warning-fatal Sphinx,
Ruff, Python 3.11 syntax, local Markdown links and MOLI governance checks pass.

The first hosted source `7a97f18` is unqualified: Ruff rejected the wrapping of
one Python example in Markdown. Local checks had covered Python paths rather than
the whole-repository format gate. Both the installed Ruff 0.16.10 and pinned
0.16.5 identify the same difference; version drift was observed but was not the
cause of this failure. The remaining CI work was cancelled after preserving that
failure. A documentation-only follow-up formats the example with the existing
cached Ruff 0.16.5 binary and runs both whole-repository Ruff gates; no separate
test environment or scientific/runtime code change is needed. Exact final-source
qualification belongs to #171 and never inherits the cancelled run as passing.

Tests use small refusal budgets and a forbidden expander; enormous endpoints are
inspected arithmetically without allocating their positions. The moderate
100,001-position success cases verify nested override propagation rather than
attempting exhaustion. Local evidence is owned by #171/#148 in
`recovered_work/region_requests_171_20261029/`, reviewed at the next code checkpoint
or before 0.15.0; disposable build/test scratch is removed after use. Read #171 for
exact-head CI/governance receipts. These technical checks do not establish
researcher acceptance or 0.15.0 readiness.
