---
summary: Separate interactive component navigation from full saved-session costs.
issue: uibcdf/sabueso#167
status: open
opened: 2026-11-04
verification: bounded_synthetic_original_parity
area: [human-exploration, agent-access, persistence, performance]
---

# Declared-component workload observations

The structure/component runtime is qualified at `7882f66`, SDK
`0.14.0+158.g7882f66`, through the [complete hosted checkpoint](../evidence/assembly_component_checkpoint_20261104.json).
This following bounded study addresses #167/#148 without changing scientific
rules, default limits, original saved formats, source inputs or dependencies.
It does not close researcher/workload acceptance or admit 0.15.0.

## Declared workload

`devtools/measure_component_navigation.py` uses the immutable public live capsule
`tests/core/data/assembly_nonpolymer_live_v2.json.gz`, with its fixed SHA-256 and
existing RCSB/UniProt terms. In an in-memory copy of its public 1HTI Card, one
generator receives 3, 12 or 48 repeated native `C` labels. These are **synthetic
diagnostic declarations**, not provider observations or distinct physical molecules.
They are never source fixtures or production knowledge. No provider is contacted.

Each fresh producer captures the synthetic Card, follows the exact native
structure question, inspects the complete position list, opens the last position
and its first original record/source, previews the list and requests a bounded
two-field agent page for the same generator/result. Every index is retained in
original order, including repeated labels. The complete human session is saved
first as plain JSON. The exact agent selection is then saved explicitly from the
same accumulated session. That second save has prepared support/history and is
**not a fresh agent workload**.

Two other fresh processes read the human and agent exports separately. Current
Card construction, scientific evaluators and navigation producers are forbidden.
The original root, scientific wire, all ordered positions, original record/source
content and last-position navigation are checked against producer hashes; the
explicit retained agent request reopens with the same count and result reference.
An initial pilot incorrectly expected a paged projection to have been saved;
its `not_saved` assertion failure is excluded from the comparative samples.
The corrected human read checks `not_saved` for the machine projection that was
only paged before that file was exported. This is the existing exact-request
contract, not loss of its underlying original findings. The public guide now
explains the need to call the selection's `save()` explicitly.

Operation wall/CPU time excludes imports, input loading and setup. Preview and
cached agent-page delivery are measured separately. Parent-sampled RSS describes
the whole worker, including setup/validation, not allocation during one operation.
Fresh processes do not imply a cold filesystem; OS caches and host load are
uncontrolled. No tracemalloc instrumented timings or timing pass/fail thresholds
are used. A supervisor stops a worker above 1 GiB RSS, any owned swap, below 4 GiB
host MemAvailable, above 2 GiB owned scratch or after 300 seconds. These are
experiment resource stops, not accepted product budgets or a memory estimate
derived from MemFree. No product byte/operation limit is disabled or raised.

## Reproduction

Use the installed editable checkout and a serial external RSS/swap/scratch
supervisor. Every producer directory must be new:

```bash
python devtools/measure_component_navigation.py produce /tmp/component-case --positions 48
python devtools/measure_component_navigation.py read /tmp/component-case
python devtools/measure_component_navigation.py read-agent /tmp/component-case
```

Keep the producer/read/resource receipts with an owner and review trigger. Remove
only that invocation's two synthetic JSON exports after both independent reads
pass and the receipts are retained. Never import those exports as source knowledge
or replace the genuine capsule. The bounded study keeps its receipts under
`recovered_work/assembly_component_workload_167_20261104/`, owner #167/#148/#173,
reviewed at the next storage change or before 0.15.0.

## Measured bounded observations

The [machine-readable receipt](../evidence/component_navigation_workload_20261104.json) records six producers and twelve independent inert readers,
in count order 3, 12, 48, 48, 12, 3. All original-binding checks pass; no worker
uses swap or reaches a stop. No product receiving limit is raised or disabled.
The table reports median wall seconds from two samples per count.

| Synthetic positions | Navigate | Human save | Accumulated agent save | Human read/verify | Agent read/verify | Human JSON bytes | Complete page bytes | Peak worker MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 0.207 | 12.439 | 12.418 | 8.680 | 8.650 | 42,434,469 | 5,560 | 291.8 |
| 12 | 0.222 | 13.227 | 13.550 | 9.498 | 9.524 | 43,274,444 | 5,561 | 296.1 |
| 48 | 0.255 | 14.828 | 14.875 | 10.851 | 10.865 | 46,636,376 | 5,561 | 312.8 |

Median cached page delivery is 1.4–2.0 ms; preview is 1.3–2.0 ms. The page
contains two requested scalar fields with mandatory interpretation/support and
one complete selected generator. It is not the full Card, native wire or history.
Full original component-list payloads contain 9,700 /30,081 /111,657 bytes.
Accumulated agent artifacts contain 42,514,006 /43,370,186 /46,797,062 bytes.
Those files intentionally retain earlier human exploration; they do not measure
a separate fresh agent-only export.

The observed cost lies chiefly in whole-session saving/verification, with
interactive navigation and bounded page delivery much smaller in this task.
This is an operation breakdown, not a profile-based attribution or speedup.
Two samples and one repeated key cannot establish general scaling or a product
SLA. Random file-local lookup namespaces also prevent whole-file digest equality
from being a cross-session identity test. Each original is instead verified
against its own trusted producer digest and complete semantic checks.

## Exact physical storage accounting

The existing storage inspector independently accounts for the 48-position human
artifact, with unchanged input SHA-256 and exact canonical total 46,636,376 bytes.
It retains one Card/input, 443 objects, 610 views and 588 locations. Views occupy
43,733,792 bytes (93.8%); their stored state occupies 34,056,820 bytes.
Exact repeated occurrences within the disjoint selection/state/native-payload/
flags parts total 28,231,134 bytes before any shared-reference/index overhead.
These are storage candidates, not achieved savings or molecular equivalence.
The 48 component links repeat only 78,000 bytes of their direct source support;
that small repetition alone does not explain the complete-session size.

This accounts for bytes rather than attributing CPU. The separate scientific
reader already verifies the original; the inspector does not replace it. Its
sampled RSS stays below 208 MiB and it uses no swap. The next bounded optimization
should profile session preparation and verification, then evaluate exact sharing
of retained view parts against the plain/gzip/Zstandard baseline. Preserve source,
request and navigation meaning; do not discard histories or invent a latency win.

## Interpretation and next acceptance

Separate the cost of a complete saved session from interactive reading and a
small agent response. Compact page delivery cannot replace original source,
history or scientific interpretation. Larger component counts, distinct native
keys, multiple generators/operations, other Card natures and actual researcher
budgets still need their own receiving. These observations cannot establish a
scaling law, a reliable speedup, a universal resource ceiling or an exceptional
human experience. Profile and account for retained content before changing its
physical representation; preserve all original outputs, requests, pins, sources,
units, uncertainty and navigation origins.

## Qualification and retained resources

The six measured producers and twelve readers share one exact diagnostic tool
hash over the unchanged qualified runtime. Counts and semantic originals match
within each producer/reader pair; both repeats use the same synthetic Card per
count. The separate accounting step preserves the original file hash. Selected
existing human/agent/save/projection/catalog checks pass 19 cases over two files
through pytest-receptor, serial, with zero worker swap. This does not replace a
full offline checkpoint or claim that the diagnostic runs on every supported OS.
Ruff, Python 3.11 syntax, Markdown links/snippets and warning-fatal Sphinx qualify
the developer tool and guide. Final publication records its own source/SDK and
remote-gate scope; the measured runtime remains the qualified `7882f66` baseline.
