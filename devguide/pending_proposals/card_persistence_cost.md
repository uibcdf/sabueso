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

## Component navigation continuation

The [bounded component-list study](component_navigation_workload.md) measures the
following qualified native @5 / saved @8 route on synthetic repeated declarations.
It separates interactive navigation, a complete bounded agent page, human-first
saving, accumulated explicit agent saving and independent inert reading. It does
not change the existing cost observations, original contracts or accepted budgets.

## Following private ownership change

The [owned-state continuation](exploration_owned_state.md) separately profiles the
current component task and removes repeated private support copies and redundant
copies of decoder-owned view state. It keeps public defensive/quantity boundaries,
direct-caller state isolation and all frozen predicates. Its unprofiled observations
have their own control/source/input hashes; the earlier copy reduction above still
has no demonstrated speedup and is not relabeled by these different-task results.

## Current combined public sessions

The [2026-11-11 workload receipt](../evidence/public_session_workload_checkpoint_20261111.json)
observes three existing public walkthroughs at clean source `89bdb0a96348b9eb07a2ecbd3415f902367834a3`,
SDK `0.14.0+250.g89bdb0a`. Each producer has its own fresh-process reader;
all seven complete saved sessions pass their original digest, selection/source
and return-route controls. Reading forbids network access, resolution and Card
construction. Structural and protein-context walkthroughs also retain their
complete finite agent reads. Seventeen immediate repeated public questions keep
their original result/view bindings.

| Walkthrough | Produce / separate read (s) | Save calls, inclusive total (s) | Maximum sampled owned RSS (MiB) | Complete saved-session encoded bytes |
| --- | ---: | ---: | ---: | ---: |
| Three Cards: protein, molecule and disease | 15.59 / 9.57 | 3 / 13.80 | 208.43 | 29,668,764, plain JSON |
| Current and historical structural context | 69.01 / 22.66 | 2 / 66.82 | 502.34 | 10,528,660, gzip |
| Supplied comparison and HsTIM context | 32.22 / 10.83 | 2 / 29.67 | 245.02 | 4,273,503, gzip |

These are single instrumented observations with uncontrolled warm OS caches and
no randomized control. Different inputs, histories and storage representations
prevent interpreting the table as a compression comparison or regression claim.
Operation timings are inclusive and may overlap. Saving includes original
verification and transport; it is not an isolated encoding measurement. Fixture
loading/mapping is included in process totals but not separately timed.
The original three-Card protein uses schema 0.3.9; the separate structural task
includes current and historical inputs. Text response and agent-page byte
observations are retained; notebook/HTML timing is unmeasured.

One owned invocation runs at a time, with one CPU, native pools one and nice 10.
Its stop guards are 10 GiB combined owned-tree RSS, 16 GiB host-available RAM,
zero owned swap, 2 GiB owned scratch and 600 s. All six phases finish without a
resource stop or owned swap, retaining at least 54.87 GiB host-available RAM.
These engineering guards are not researcher-agreed performance targets.

Saving remains the dominant observed producer cost under the existing #167
question. This supplies current combined-session evidence, not a new correctness
defect or accepted workload budget. Obtain actual task feedback and agree useful
latency, memory and storage scales before closing B7's workload dimension;
independent scientific/researcher, actual-agent usefulness and real-consumer
acceptance remain separate. No runtime, scientific predicate, historical original
or production workload ceiling changes in this measurement increment.

Raw observer/controller code, complete logs, preflights, per-call/resource
receipts and exact output hashes are retained under the directory declared in
the receipt. Sabueso maintainers own review under #167/#148/#112 at B7 workload
review or before candidate preparation. Generated measurement sessions are
disposable after their independent reading and hash capture; original scientific
capsules remain protected. These local observations are retained for a
consolidated #167 review; no new issue publication is claimed.

## Current exact-record packing cache

The current structural profile at clean `3c26790` / SDK251 spends 75.53 of
154.62 profiled save seconds in shared packing, including 4.85 million canonical
JSON calls. Preparation, packing and original verification are nested; do not add
their cumulative times. Profiling overhead is substantial: the ordinary save
takes about 56 s. The original producer and separate reader both pass.

Two bounded caches now avoid repeated physical encoding work in the current
@35/@36 writer. Exact native strings reuse their canonical UTF-8 sizes; small
records reuse their existing digests through exact typed token keys. Boolean,
integer and float kinds, signed zero, native strings and internal reference
tokens remain distinct. Non-native string subclasses and records with more than
32 members take the original path. Both caches have at most 4,096 entries, live
only within one packing call and are cleared after encoding. All logical
positions are retained, collision equality still runs, and original logical
budget and scientific checks remain mandatory. Stored bytes, formats, named
rules, source support and public API/defaults stay fixed.

Same-session ABBA packing calibration first measures only string-size caching:
control 26.167/27.073 s versus 23.042/22.996 s, about 13.5% for that phase.
Adding typed record caching measures control 26.608/26.435 s versus
16.133/16.086 s, about 39.3%. Each comparison has identical complete canonical
physical bytes. These are isolated packing observations, not whole-save results.

The separate whole-session benchmark uses the **same fixed input files and
pins**, fresh writer processes and control/candidate/candidate/control order:

| Session | Control save wall seconds | Cached save wall seconds |
| --- | ---: | ---: |
| Current public structural context | 55.923 /56.228 | 45.092 /44.442 |
| Historical source context | 9.834 /10.083 | 10.003 /9.800 |

Current saving averages 56.076 versus 44.767 s, a **20.2% observed reduction** in
this bounded task. Historical saving remains around 10 s. All eight sessions
reopen through the unmodified original reader with network access, resolution
and Card construction forbidden; original native/source/return and finite agent
observations match. Reader processes take about 22–23 s for each current/historical
pair. Writer RSS stays below 482 million bytes and owned swap is zero. These
two-sample, warm, nonrandomized observations make no general speed, cold-cache,
file-size or RAM-reduction claim. Independent sessions have different local
lookup namespaces; whole-file hashes are compared only within the same session.

Before changing production, the clean SDK251 original writer captured ten
synthetic codec vectors with their complete original physical outputs. Forty
deterministic controls in the existing complete shared-values module bind their
original hashes, typed reconstruction, eviction, unsupported values, digest
collision refusal, entities/units/positions, budgets and cycles. The control
corpus is engineering data, not SourceAssertions or a Card schema freeze.
Existing test bodies, all seven SOURCE resources and all original capsules remain
unchanged. The complete module is already copied/selected in both installed CI
routes, so its new controls need no new payload or workflow.

The maintainer [accepted scoped provisional targets](../DECISIONS.md#agree-a-scoped-provisional-structural-workload-budget-2026-11-11)
of 60 s saving, 30 s reopening and 1 GiB RSS for this workload on this machine.
The cached combined producer completes in about 56–57 s, with combined saves
around 54–55 s; the measured receiving also fits. This is a bounded provisional
workload decision, not independent researcher usefulness or complete B7 acceptance.
Keep original large-ensemble tests' explicitly raised allowances separate.

The diagnostic code, original vectors, profiles, complete logs, byte comparisons,
ABBA observations and original-reading records are retained under
`recovered_work/checkpoint_recovery_20261106/b7-persistence-current-profile-1/`,
`b7-persistence-record-cache-1/` and `b7-persistence-final-candidate-1/`.
Sabueso maintainers own them under #167/#148/#112, reviewed at adoption/B7 or
before candidate preparation. CHECKPOINT owns final source/receiving qualification
and exact-head CI scope. A passing older code head never qualifies this change.

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

## Current format @6 public observation (2026-11-02)

The original public 2V5B structure/assembly guide reading from source
`f2732011c027be0ed65e7c17fb353e0c925bd50a`, actual SDK
`0.14.0+138.gf273201`, contains 11,009,687 canonical bytes. Its SHA-256 is
`e5d8c9592d354367cafeaf1527d60105f3551f852875c74f7ebc9e85b932fc11`.
Current working-tree presentation changes do not backfill this old file's policy.
Three serial fresh-process reads observe 2.490, 2.456 and 2.472 wall seconds
(CPU 2.490, 2.456 and 2.472 seconds), excluding setup/imports before the timed
call. OS cache and background load are uncontrolled; these are diagnostics, not
a cold-cache benchmark, accepted budget, scaling curve or achieved improvement.

Separate instrumented reading takes 5.939 seconds: 2,316,461 `deepcopy` calls
account for 3.082 cumulative seconds and `verify_views` for 3.014 cumulative
seconds. These costs overlap. The fresh profiled process also includes imports;
timings are not interchangeable with the unprofiled read samples. Source queries
are forbidden, current Card/native assembly generation is forbidden, original
frozen scientific verification remains active and the input hash stays unchanged.
Sampled owned RSS is below 177 MB, with zero owned swap and no resource stop.

Canonical accounting identifies 111 views, 81 objects and 108 locations. Views
occupy 10,150,995 bytes (92.2%). Exact repeated occurrences within the four
disjoint selection/state/native-payload/flags parts total 5,202,520 bytes before
reference/index overhead. This is potential physical reuse, not an achieved
reduction or permission to drop navigation/support. Inspection takes 2.01 seconds
including worker startup, with about 64 MB sampled owned RSS.

The next bounded #167 design should compare explicit retained-session scope with
a versioned shared view-part layout, measuring necessary support preparation
separately from duplicate physical representation. Preserve every occurrence,
request, original location, selection, unit and independent old verifier; refuse
implicit pruning and do not weaken defensive public copies. Prove original-wire
and inert-reader parity before adopting a representation. Then measure fresh and
accumulated public protein/molecule/disease workloads and agree researcher budgets.
This observation does not close #167 or the 0.15.0 workload gate.

Inputs, profile, unprofiled samples, accounting and resource receipts live under
`recovered_work/navigation_preview_148_20261102/`, owned by #167/#148. Review at
the next persistence change or before workload acceptance. Keep useful originals
and receipts; clean only finished owned temporary resources.

The [follow-up physical-layout experiment](card_persistence_layout_experiment.md)
now separates automatic support preparation from exact physical repetition and
compares shared parts with gzip of unchanged originals across five public files.
Gzip alone removes 93.36–96.58% of stored bytes here; sharing first makes four
gzip files larger. Prioritize optional bounded original-byte compression before
adopting a new reference-based public format. The
[follow-up compressor comparison](card_compressor_comparison.md) (#178) now
measures gzip/Zstandard/XZ before a production codec/default is selected.
Verification CPU/RSS, representative
workload budgets and original-reader compatibility remain separate requirements.


## Actual public transport API measurements (2026-11-03)

The [five-reading API study](public_transport_workload.md) runs the implemented
plain/gzip/Zstandard `save` and public original reader in 45 fresh producer/reader
pairs. It verifies all captured content/history and original hashes, records
complete call times separately from import/setup and post-check memory, and
confirms large storage savings with similar full-read latency. This completes the
bounded local transport measurement, not accepted large-workload or researcher
budgets. The measured source CI also exposed two older large-fixture calls that
need explicit admission; preserve the production ceilings and qualify the
test-only correction on a new exact-source unskipped checkpoint before admission.
Then resume the agreed broader scientific exploration route.
