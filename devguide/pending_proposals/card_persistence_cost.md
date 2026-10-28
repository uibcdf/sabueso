---
summary: Measure accumulated saved exploration and remove redundant private copies while retaining every original binding.
issue: uibcdf/sabueso#167
status: open
opened: 2026-10-27
verification: bounded_public_observations
area: [human-exploration, persistence, performance, historical-reading]
---

# Accumulated exploration storage and verification cost

The maintainer authorized a bounded persistence review before continuing #148's
structural expansion. The complete broad profile and researcher acceptance remain
required before 0.15.0; release consolidation stays paused.

## Declared baseline

At qualified source `75579df`, actual SDK `0.14.0+114.g75579df`, two public
artifacts retain the same P52270 Card pin and root view reference. The input is
`temp_data/frozen_cards/schema_0.3.9__P52270.json`; it remains unchanged and no
source is queried.

| Scope | Fresh source question | Accumulated public guide, blocks 1–26 |
| --- | ---: | ---: |
| Format | `sabueso.card_exploration@1` | `sabueso.card_exploration@3` with scientific results |
| Cards / inputs | 1 / 1 | 1 / 1 |
| Objects | 78 | 2,760 |
| Views | 99 | 4,031 |
| Locations | 94 | 3,392 |
| File size | 3,517,944 bytes | 125,453,803 bytes |

The fresh-process/fresh-explorer sample observed capture 0.040 s, source-question
materialization 0.004 s, save 1.236 s and immediate same-process read/verify
0.829 s. The accumulated guide's combined save/read took at least 62.4 s while
still running and subsequently passed. These are scoped single observations;
OS caches/background load are uncontrolled. Formats and retained scientific
history differ. They do not establish a regression, an independent cold-reader
time, a scaling guarantee or an accepted performance budget.

## Read profile and bounded first change

An isolated cProfile reading of the original accumulated artifact took 69.62 s
with profiling overhead. `verify_views` accounts for 45.77 s cumulatively;
`deepcopy` has 29,940,438 total calls /39.40 s cumulative. These timings overlap
and must not be added. The sampled owned RSS peaked at about 854 MiB, with no
resource stop and more than 7.9 GiB genuinely free host RAM throughout.

Code inspection identifies redundant copies at private serialization/verification
boundaries: `Cell.to_dict()` already detaches the public value; `native_payload`
already returns a defensive copy; JSON cell comparison only reads nested data
while removing top-level presentation wording. The first change reuses those
owned copies. Quantity conversion retains its independent conversion copy.
Every predicate, original input/output/request, source reference, unit, unknown,
selection, ordering and navigation occurrence remains checked and retained.

Same-session control/current comparisons produce identical canonical bytes and
digests for the public protein source question (3,517,944 bytes) and molecule
quantity properties (1,448,115 bytes); both original readers verify them.
Independent sessions intentionally have different random `XL_` lookup namespaces,
so independent whole-file hashes are not a valid equality test. An initial
independent-file comparison failed for that reason; it is not a compatibility
receipt. The stored formats and public API remain unchanged.
This first change makes no file-size reduction claim. Required
history/support is preserved; physical layout/retention changes require separate
design, explicit versioning where needed and original-reader compatibility.

The exploratory candidate profile reduces total `deepcopy` calls to 24,206,708
(19.2% fewer), but profiled wall time is essentially unchanged at 69.41 s.
The first unprofiled exploratory batch observes means of 34.022/32.515 s; that
apparent 4.4% improvement does **not** reproduce in the final guarded source.
Four final **unprofiled** fresh-process reads in
control/candidate/candidate/control order observe:

| Sample | Control wall / CPU seconds | Candidate wall / CPU seconds |
| --- | ---: | ---: |
| A | 32.456 / 32.451 | 32.556 / 32.537 |
| B | 30.494 / 30.490 | 30.719 / 30.713 |

Mean wall time is 31.475 versus 31.637 s (candidate 0.5% higher in these two
samples per version). This establishes **no reliable end-to-end speedup**.
Qualified-control source is re-executed only inside disposable workers;
receipts record all three actual loaded-module hashes. The shared environment and
artifact are unchanged. OS caches/background load remain uncontrolled; these
measurements do not establish a scaling curve, RAM reduction or accepted workload
budget. The changes remove proven redundant copies, not measured user latency.
Sampled owned RSS stays below 853 MiB and genuinely free host RAM above 6.0 GiB
across the four final unprofiled runs. No memory-headroom or owned-swap stop
occurs; the owned-swap stop threshold is 32 MiB. One heavy worker runs at a time;
nearly full host swap is not treated as
free capacity.

## Reproducible storage inspection

`devtools/inspect_exploration_storage.py INPUT OUTPUT_DIRECTORY` reports canonical
bytes by top-level member and exact repeated view-part values. It encodes chunks
instead of constructing another complete JSON string. The full parsed JSON tree
is still held in memory: large cases run in one owned, memory-limited process.
Duplicate JSON members and nonfinite values are refused; the input hash is checked
before/after. The output directory must be new.

The diagnostic inspects structure, not scientific validity. It never replaces
`read_exploration`. Identical serialized bytes indicate physical storage reuse
candidates, not molecular identity or permission to remove history. Repeated-byte
counts exclude reference/index overhead and do not represent achieved savings.

On the original 125,453,803-byte accumulated artifact, canonical accounting sums
exactly to the input size: views contain 115,226,673 bytes (91.9%), objects
8,777,045, locations 876,394, cards 319,625 and navigation 251,826. Repeated
occurrences within selection/state/native-payload/flags total 46,721,128 bytes
(44.6 MiB) before reference/index overhead. These are disjoint physical parts;
cross-part duplication is not counted. Inspection takes 24.05 s including worker
startup and samples about 702 MiB owned RSS; its input hash remains unchanged.
This supports investigating a versioned shared physical layout. It does not
justify removing scientific/navigation history or silently changing old formats.

Next, use the measurements to separate necessary history, automatically prepared
support and avoidable duplication. Agree workload-specific budgets with researchers
and measure fresh/accumulated source and scientific routes across Card natures.
Keep independent inert receiving and original genuine capsules as constraints.

## Qualification and resource ownership

Owning gates cover complete original-wire immutability for literal and quantity
records, defensive cell values, all supported saved formats/requests and adversarial
resealed changes. Adversarial review reproduced a candidate-only type-admission
regression: `dict(cell)` could accept a resealed array of pairs. An explicit object
requirement preserves the original boundary; both literal and quantity cases
fail before the fix and pass after it. This was corrected before publication.
Storage-accounting cases independently check canonical UTF-8
byte totals, exact repetition versus typed Boolean/integer differences and unchanged
inputs. Timing observations remain diagnostic; tests have no speed threshold.

The first broader run has 1,156 passed /1 failed, not qualification. It exposed
an existing model-test isolation leak: patching AlphaFold's interpreter before
first importing its consumer retained the forbidden alias after teardown.
Fresh-process control/fixed probes reproduce and eliminate that leak. The test
helper now imports consumers before patching providers; its inert-reading
prohibitions remain intact. This changes no production model interpretation.

The four-worker final rerun stops after 5.03 s when genuinely free host RAM drops
below its 4 GiB floor, with only 373 MiB sampled owned RSS. It is not qualification.
The next gate uses serial pytest (`-n 0`), a 1.25 GiB owned RSS ceiling, at least
3 GiB genuinely free /12 GiB available host RAM and the same 32 MiB owned-swap
stop. Other owners' processes and host cache/swap policy remain untouched.

The final selected gate passes **1,159 cases /568.32 s**, serial through
pytest-receptor with local-source qualification and fatal runtime/SQLite/unraisable
guards. It samples **822 MiB owned RSS**, at least **5.9 GiB genuinely free host
RAM**, and no resource stop. The three declared warnings are two fixture UniChem
failures and the public STRING row cut. This covers all 38 selected Card/native/
history/argument/quantity/accounting files; it is not a new full-local-suite receipt.
The final guarded same-session wire comparison passes again for both public
protein and molecule routes. Ruff format/lint (1,182 files), warning-fatal Sphinx,
324 local Markdown targets/anchors, syntax for 53 guide snippets and Python 3.11
parsing of seven changed source/test files pass. Fixture delivery preserves
51 reviewed public inputs and 37 protected local originals. Exact-source remote
CI/governance and installed-package qualification retain their separate receipts.

The final code checkpoint `50ce8e7f228096040babbb0a05d2c69b7315c59c`, actual tested
SDK `0.14.0+115.g50ce8e7`, passes [CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/40603174636)
and [governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/40603174661).
Both six-member full captures, archive integrity, exact source/job steps and all
thirteen actual summaries are independently checked: nine repository-input lanes
5,951 each, four installed public-Ackredit lanes 1,452 each. Coverage upload
succeeds with processing queued; no percentage is inferred. After the final
editable reinstall, 52 owning cases pass /66.92s, with 364 MiB sampled owned RSS.
The documentation-only closure retains that exact code qualification and records
its own [administrative recovery scope](deferred_ci.md); it changes no tracked runtime,
scientific-input, schema or dependency requirement bytes.

Baseline artifacts/proof remain under
`recovered_work/source_observations_166_20261027/final-75579df/`; current profiles,
accounting and qualification receipts live under
`recovered_work/persistence_cost_167_20261027/`. Owner #167/#148; review at the next
persistence optimization or before 0.15.0 workload acceptance. Preserve original
inputs/capsules and useful receipts, clean completed owned scratch and protect
active captures. Heavy gates never overlap. Four receptor workers are reduced to
serial execution as host headroom changes; successful-function temporary cleanup
continues under the current host-memory constraint.


## Repeat machine-save root correction (#168 checkpoint)

Qualification of #168 observed that repeated `AccessSelection.save()` calls made
another synthetic root despite unchanged exploration. The synthetic case grew from
10 to 11 view records and changed the digest. The correction reuses only the same
selection object's original root with matching machine reference, summary
presentation, no origin and no display request. It does not deduplicate source or
scientific records/history. Literal/scientific live and original saved selections
now have byte-stable repeat-save regression cases. No general size or speedup is
claimed; physical layout, scaling and researcher budgets remain open. Source-bound
full/remote qualification belongs to the #168/#148/#112 checkpoint.
