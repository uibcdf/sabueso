# Deferred development CI (#112, #108)

The maintainer approved batching locally checked development commits on
2026-10-13, allowing `[skip ci]` on intermediate authorized direct pushes and
recovering remote gates once per completed block. The rule and exact-head recovery
commands live in [TESTS.md](../TESTS.md#recovering-deferred-ci). This changes
Sabueso's local practice within the existing MOLI policy; it changes no shared
contract or release gate.

## Exploration route and recovered code checkpoints (#148)

### Bounded CI timeout correction (2026-11-11, #112/#148)

The old `3c26790` installed Python 3.13 job exceeds its four-hour execution limit;
Python 3.12 completes the identical 4,103-case public scope in 13,140.39 s. The
separate Python 3.14 runner/server loss is not assigned the same cause. Original
full logs and authoritative check annotations remain retained, without converting
cancelled or failed work into PASS.

The [local correction](../pending_bugs/ci_serial_execution_timeout.md) preserves
all original pytest case/marker/coverage/receptor arguments and job matrices,
using at most three monitored outer workers and serial nested clients. Its
[receipt](../evidence/ci_bounded_execution_checkpoint_20261111.json) qualifies only
its declared local gates; it is not a repeated full suite, public installed matrix,
new hosted result or release candidate. Production modules, source rules and all
52 protected originals stay unchanged. Only development/test dependencies change.

Record the exact committed/pushed head and editable metadata under
`recovered_work/checkpoint_recovery_20261106/b7-ci-bounded-execution-1/`.
The authorized intermediate `[skip ci]` route retains #112/#148 ownership and
mandatory final exact-head recovery. The prior concrete authorization covers
only old `3c26790` CI43072436424/governance43072515668. A new corrected-head batch
needs its own explicit scope; do not repeat the old batch, overlap another batch
without approval, silently retry or publish a new issue body. Preserve all eighteen
CI and separate governance responsibilities, including twelve original backend
reports and actual installed public-dependency receiving. B7 acceptance and B8
resumption remain separate.

### Full packing-source qualification (2026-11-11, #167/#148/#112)

The [full current-source receipt](../evidence/packing_full_checkpoint_20261111.json)
accounts for all 11,432 current normal offline IDs at unchanged runtime
`5ae3b1e` / SDK252. Initial full execution has one stale receiving-count failure;
only that test function is corrected and repeated, with actual external client
and scratch placement. The other 1,348 inputs and all runtime/original bytes stay
fixed. Preserve the original 418-pass/one-failure gate and the exact correction
certificate; coverage combines the unchanged passing cases and corrected repeat.
Documentation and the test-only correction change no tested runtime.
Record the exact resulting committed/pushed SHA and metadata under
`recovered_work/checkpoint_recovery_20261106/b7-packing-full-checkpoint-1/`.

The intermediate `[skip ci]` route remains authorized. Recover applicable CI and
governance on the exact final authorized head before admission/release under
#167/#148/#112. The older one-batch `3c26790` recovery below retains its original
scope and actual outcomes, including observation failures. Do not count it as
qualification of the changed packer, silently retry it or dispatch a new head.
B7 independent acceptance and B8 resumption remain separate.

### Exact packing cache (2026-11-11, #167/#148/#112)

The [selected local receipt](../evidence/exact_packing_cache_checkpoint_20261111.json)
binds the two changed source/test files against `3c26790`, all **181 distinct
source cases**, both **96-case** copied/installed diagnostic receiving scopes,
original codec bytes and all 52 protected resources. It also records the bounded
ABBA workload improvement and maintainer-approved provisional targets. These
results do not qualify the entire changed source or a final candidate matrix.
The previous full integration result remains bound to its earlier source.

Publish this tested increment through the authorized intermediate `[skip ci]`
route. Record its exact committed/pushed SHA, editable metadata and resource
cleanup in `recovered_work/checkpoint_recovery_20261106/b7-persistence-final-candidate-1/`.
The owning issues are #167/#148/#112; recover applicable CI and governance on the
exact final authorized head through gh-run-receptor before admission or release.

The separately authorized one-batch recovery at **`3c26790a13903d857c548886126d0c8111550704`**
created CI **43072436424** and governance **43072515668**. Governance passes with
full captured verification; no complete CI result is claimed here. Preserve the
existing watcher and receipt under `b7-ci-recovery-3c26790-1/`; do not redispatch
this batch. Its source differs from this increment and cannot qualify it. New
dispatches require their own authorization scope. B7 independent acceptance and
B8 resumption remain separate.

### Combined local integration and workload handoff (2026-11-11, #148/#167/#112)

Implementation source `89bdb0a96348b9eb07a2ecbd3415f902367834a3`, SDK250, passes
the [11,392-case local integration](../evidence/card_integration_checkpoint_20261111.json)
and both 223-case outside-checkout receiving scopes. The following
[public workload observations](../evidence/public_session_workload_checkpoint_20261111.json)
add seven separate-process saved readings without changing that implementation.
Documentation-only handoff commits retain the same tested runtime. Record their
exact pushed SHA and retained resource cleanup under
`recovered_work/checkpoint_recovery_20261106/b7-whole-session-workload-1/`.

The intermediate `[skip ci]` route remains in effect. Cumulative exact-head
CI/governance recovery is due under #148/#112; follow the complete eighteen-job
CI and separate governance accounting in [TESTS](../TESTS.md#recovering-deferred-ci),
including all twelve Zstandard backend reports. Those observations alone
authorized no dispatch. The later concrete one-batch approval and its actual
run IDs are recorded above. B7 human,
scientific, actual-agent/workload and consumer acceptance and B8 delivery remain
separate; this is not candidate selection or a release claim.

### Exact-origin molecule LIVE return (2026-11-07, #148/#112)

The [selected 515-case local receipt](../evidence/molecule_activity_root_exact_live_checkpoint_20261107.json)
qualifies the corrected initiating-instance and typed-request return, affected
global saved/access/navigation paths and genuine SDK205/208/211/216 compatibility.
New LIVE molecule saving explicitly waits for the new independent original
binding; older @21/@22 files keep their original policy and reading/resaving.
The pre-fix control checkpoint is `190c291`, locally committed with `[skip ci]`.
The corrected producer is `b1bbfaa1fde03c1148a5150a047098ecfcc93fbf` / SDK218.
Record source equivalence, editable metadata and the batched direct push under
`recovered_work/checkpoint_recovery_20261106/b5-root-exact-commit-1/`.
This remains the authorized intermediate `[skip ci]` route: recover cumulative CI
and governance on the exact final SHA through gh-run-receptor under #148/#112.
No hosted workflow, new installed-platform admission or release is authorized
or claimed by this local increment. The
[two clean SDK218 originals](../evidence/molecule_activity_root_exact_original_20261107.json)
are retained and byte-verified before the new independent reader. The following
data/documentation checkpoint changes no tested runtime; its exact pushed head
is retained with the same owner and final-head recovery route.

### Molecule original saved reader and package-data checkpoint (2026-11-07, #148/#112)

The [complete local receipt](../evidence/molecule_activity_full_checkpoint_20261107.json)
qualifies 9,786 distinct offline cases with exact discovery/phase accounting.
New @21/@22 saving retains actual operation histories, original typed requests,
cross-focal/source/native/back navigation and all three immutable originals.
The 54-case outside-checkout payload passes. The package-data correction is
qualified by the existing regression, actual wheel/sdist membership/bytes and
separate installed diagnostic imports; it changes no build/runtime requirement.
Earlier failed, incomplete and stopped attempts supply no passing coverage.

Use the authorized intermediate `[skip ci]` route. Record the exact committed/
pushed head, source maps, generated/editable metadata and clean-head repeats in
`recovered_work/checkpoint_recovery_20261106/b5-molecule-reader-commit-1/`.
The actual code head is **`92d149180ea0c3196bbebc3a670e1d0a96111adb`**, pushed to
`main` with `[skip ci]`; no Actions run is returned for that SHA. Clean SDK215
metadata agrees outside checkout and all 60 LIVE cases repeat successfully.
Only the generated version label differs from the full working-source epoch;
the [receipt](../evidence/molecule_activity_full_checkpoint_20261107.json) records
that exact distinction. Following documentation-only handoff heads retain the
same tested implementation and do not become remote passing evidence.
Cumulative exact-final-head CI and governance recovery through gh-run-receptor
remain owned by #148/#112; no remote workflow is dispatched here. Actual installed
public-dependency/OS/Python receiving, typed root-return follow-up, the remaining
rich panels and B7 acceptance stay open; B8 and release remain unresumed.

### Corrected quantity-display original (2026-11-07, #148/#112)

The [SDK211 original](../evidence/molecule_activity_quantity_original_20261107.json)
captures clean `af5180b` after its 60-case repeated LIVE gate. This increment adds
only immutable public control/provenance bytes and maintained documentation;
runtime/test code and the SDK205/SDK208 originals stay fixed. Byte/graph audits
cover every member, observed instance, typed quantity binding and parent/back
identity. Record the exact published head and editable metadata under
`recovered_work/checkpoint_recovery_20261106/b5-molecule-quantity-original-commit-1/`.
The authorized intermediate `[skip ci]` route retains cumulative exact-final-head
CI/governance recovery through gh-run-receptor under #148/#112. No saved-reader,
new pytest or installed-artifact qualification is claimed by this data increment.

### Molecule quantity-display navigation (2026-11-07, #148/#112)

The [735-case selected receipt](../evidence/molecule_activity_quantity_display_checkpoint_20261107.json)
qualifies PyUnitWizard display-operand serialization and original source/back/
publication/native navigation. All 60 LIVE cases pass, with affected shared/native/
profile and copied receiving. Existing JSON requests, scientific defaults,
frozen predicates, controls and formats @1–@20 stay fixed. The defect's approved
preparation-time report is published under #148. Record the exact committed/pushed
head, editable metadata and clean-head repeats under
`recovered_work/checkpoint_recovery_20261106/b5-molecule-quantity-display-commit-1/`.
This is another authorized intermediate `[skip ci]` increment. Recover cumulative
exact-final-head CI/governance through gh-run-receptor before code-block closeout.
No remote workflow, full offline, installed-artifact or full saved-reader gate is
claimed. Preserve positive clean-producer controls and finish new saved admission.

### Retained molecule-result restoration (2026-11-07, #148/#112)

The [75-case selected receipt](../evidence/molecule_activity_retained_checkpoint_20261107.json)
qualifies private retained-result restoration over all SDK205/SDK208 original
wires and typed machine pages, with recalculation blocked during restoration.
It changes one private helper and its tests; frozen predicates, controls, public
saving and formats @1–@20 stay fixed. Record the exact committed/pushed head,
editable metadata and clean-head repeats in
`recovered_work/checkpoint_recovery_20261106/b5-molecule-retained-commit-1/`.
Use the authorized intermediate `[skip ci]` route and batch a remote checkpoint
when useful. Cumulative exact-final-head CI/governance recovery through
gh-run-receptor remains under #148/#112. No new saved reader or full offline,
installed-artifact or researcher gate is claimed.

### Corrected multi-focal original (2026-11-07, #148/#112)

The [SDK208 supplement](../evidence/molecule_activity_multifocal_original_20261107.json)
captures the corrected clean `142618d` producer before new saved admission and
preserves all SDK205 original bytes. The expanded private predicate module passes
39 cases, including the three new multi-focal controls. This increment changes
test/control/documentation bytes only; runtime and frozen predicates stay fixed.
Record its exact committed/pushed head, editable refresh and clean-head repeats
under `recovered_work/checkpoint_recovery_20261106/b5-molecule-multifocal-commit-1/`.
It uses the authorized intermediate `[skip ci]` route; cumulative exact-final-head
CI/governance recovery through gh-run-receptor remains under #148/#112. No remote
workflow is dispatched and no full saved-reader or installed-artifact gate is
claimed. Finish independently versioned admission and full original receiving next.

### Exact-focal molecule crossing cache (2026-11-07, #148/#112)

The [selected correction receipt](../evidence/molecule_activity_cross_focal_checkpoint_20261107.json)
binds the one-line LIVE cache correction and its three public-route regressions
to 765 distinct local passes, including all 54 LIVE cases, 36 private originals
and isolated copied receiving. It preserves the SDK205 original, scientific
defaults and formats @1–@20. The pre-commit editable label is SDK207; exact changed
source is hashed separately. Record the actual committed/pushed SHA, refreshed
editable metadata and clean-head repeats in
`recovered_work/checkpoint_recovery_20261106/b5-molecule-cross-focal-commit-1/`.
This is another authorized intermediate `[skip ci]` increment. No hosted run is
claimed; recover cumulative exact-final-head CI and governance through
gh-run-receptor before code-block closeout. Owners remain #148/#112. Supplemental
clean-producer multi-focal capture and independent saved admission are next.

### Current intermediate activity reader (2026-11-06, #148/#112)

The clean live checkpoint `2eb611463c0f8ab990039ec017833f5b33ae2711`
was pushed with `[skip ci]`; no Actions run was created for that head. Its genuine
SDK200 live control precedes the independent original reader. The subsequent
[saved-reader receipt](../evidence/bioactivity_saved_checkpoint_20261106.json)
owns the changed source hashes, actual selected local outcomes and remaining
receiving, without reusing older hosted results as current qualification.

The maintainer reconfirmed `[skip ci]` for intermediate commits. Batch remote
CI/governance at a later substantial checkpoint through the authorized exact-head
recovery route; do not dispatch a new matrix for each small change. Record the
actual published head and post-install metadata in the local postcommit receipt
and owning #148/#112 handoff. The source/installed OS/Python matrix, independent
scientific/researcher acceptance and release gates remain open. This block does
not authorize publication of third-party reports or a release.

### Completed accumulated runtime receiving (2026-11-05, #188/#186)

Source `c5b8af1` /SDK `0.14.0+167.gc5b8af1` now passes
[full exact-source receiving](../evidence/bioactivity_target_scope_checkpoint_20261105.json):
CI 18/18 and governance 1/1, thirteen source/installed summaries, all manifest
hashes/ZIP CRC/job steps, twelve codec routes and 36 installed codec cases.
This closes the current accumulated code checkpoint's technical recovery. Earlier
runs are not relabelled; later docs/research-only heads add no runtime qualification.
Scientific/default, consumer/researcher/workload and paused release gates remain
open. The next changed code block still needs its own unskipped final-source gates.

### B3 source-scope review (2026-11-04, #173/#148/#112)

The 2026-11-05 UTC MolSysMT review adds concrete provider capability/limit receipts
and [molsysmt#563](https://github.com/uibcdf/molsysmt/issues/563), with 62 selected
provider cases and a separately verified synthetic importer reproducer. Provider
source, local environments, library runtime and historical inputs remain unchanged.
The following docs/evidence checkpoint uses the same authorized `[skip ci]` route;
it does not qualify a modeling bridge or replace provider fix/receiving. Exact
local head, SDK, checks, report links and cleanup live under
`recovered_work/molsysmt_capability_review_20261104/INDEX.json` (owner #173/#148/#112;
review at provider receiving/B3 disposition). Existing runtime checkpoint recovery
and the next changed code block's unskipped final-source obligation remain below.

The [review](structural_journey_acceptance_20261104.md) adds a dated reproduction
script, public observations and acceptance questions only; no package/native/schema/
fixture/verifier bytes change. Selected receiving passes 106 cases and the audit
checks four public human/agent/saved journeys plus six synthetic counterexamples.
A documentation/research checkpoint may use `[skip ci]` after local links/snippets,
Python 3.11, lint/format and governance checks. This supplies no new hosted code
qualification. Runtime source `c5b8af1` has now completed exact-source CI
`41932333464` and governance `41932333524`, with full gh-run-receptor qualification under
`recovered_work/target_scope_188_20261104/INDEX.json`. The next changed code block
needs its own unskipped final source checkpoint. Owner #173/#148/#112; receipts and
cleanup under `recovered_work/structural_scope_173_20261104/`. Assembly-scope,
scientific/consumer/researcher acceptance and paused 0.15.0 remain open.

### Copy target-scope prerequisite (2026-11-04, #188/#186)

The [opt-in correction](../pending_bugs/bioactivity_target_scope.md) changes new
explicit @2 activity/ligand selection, explanations and tables while preserving
@1/defaults and original packet mappings. Qualify its accumulated code through an
unskipped exact-source CI/governance push with source/installed/codec receiving.
The prior ca9e0f3 checkpoint cannot qualify these later bytes. Local gates,
original controls and public same-input comparisons are retained in
`recovered_work/target_scope_188_20261104/` under #188/#186/#148/#112. Scientific
review is maintainer-owned and explicitly deferred; release consolidation paused.

### Opt-in measurement correspondence and pinned explanation context (2026-11-04, #186/#182)

The [candidate](assay_aware_measurement_correspondence.md) adds explicit measurement
@2 across direct activity/ligand answers, explanations and tables. Original @1 and
defaults remain unchanged; mappings @6–@15 explicitly retain @1. The bounded #182
prerequisite enumerates actual pinned glossary identity entries without changing
glossary reconstruction or Card serialization/pins. New scientific data are not
added to Cards or SourceAssertions. No new packet or saved explorer is introduced.
Local selected gates, four exact public input comparisons, original/copy receiving,
quantity/argument checks and warning-fatal Sphinx are recorded in the
[receipt](../evidence/measurement_correspondence_candidate_20261104.json).
Finish this code block with an unskipped exact-source CI/governance push and full
source/installed/codec receiving. The older qualified 1290201 or pending 7667754
cannot qualify these changed bytes. Owner #186/#182/#148/#112; recovery and original
evidence are retained under `recovered_work/measurement_policy_186_20261104/`.
Scientific/default/consumer and researcher acceptance stay pending, release
consolidation paused.

### Conservative default and packet @15 adoption (2026-11-04, #184/#185)

The [adoption](../pending_bugs/bioactivity_interpretation.md) changes new activity,
ligand and table defaults to existing @4 and uses packet mapping @15, inheriting
@14 outside bioactivities. Explicit @3 and mappings @6–@14 remain original.
The genuine pre-adoption control from `1290201` is immutable; current and original
public examples have distinct declared formats and inert receiving. Qualify this
completed block with an unskipped exact-source CI/governance push, including full
source/installed summaries and codec receiving. The preceding
[qualified opt-in source](../evidence/bioactivity_opt_in_checkpoint_20261104.json)
has CI 18/18 and governance 1/1 at `1290201`; it does not qualify later changed
defaults or @15. Independent scientific/researcher and consumer acceptance remain open.

Final source `7667754837ec6dc04565f625ca94a3f45ebd24ce` /SDK
`0.14.0+164.g7667754` is published unskipped with 77 post-editable cases passing.
CI `41908832887` and governance `41908832884` are pending full exact-source
receiving under `recovered_work/bioactivity_adoption_184_20261104/INDEX.json`.
Intermediate `7853039` keeps its failed producer-stamp comparison and premature
push record; original stored reading remains exact after the test correction.
The following documentation/evidence-only B2 preparation may use `[skip ci]`
after link/snippet/format/lint/governance and receipt checks. It changes no code
or default and supplies no additional remote qualification; the code recovery
owner and route remain #184/#185/#148/#112 and those recorded final-source runs.

### Explicit conservative activity policy (2026-11-04, #184/#185)

The [first activity slice](../pending_bugs/bioactivity_interpretation.md) adds
opt-in class @4 and explanation @2, retaining omitted @3, original classifier/parser
functions, Card/schema data, historical verifiers and fixtures. Local gates pass
62 independent cases, 232 affected cases and copied-payload receiving; CI/staged
installed scopes now include the new standalone file. Its
[receipt](../evidence/bioactivity_interpretation_20261104.json) records exact file
hashes, scope, resource checks and public-input comparisons. Qualify the accumulated
code with one unskipped exact-source checkpoint, including B0's renderer and UTF-8
test recovery. An intermediate queued/cancelled source is not passing evidence.
New default/consumer adoption and broad scientific/human acceptance remain open.

### Post-audit presentation and UTF-8 test recovery (2026-11-04)

The source `3413559` failed all four Windows source lanes in one new direct-restore
test (7,043 passed /1 failed each); three macOS lanes were cancelled. The test
decoded UTF-8 JSON using the platform default. An explicit cp1252 reproduction
fails the retained digest while UTF-8 restores correctly; production decoding and
historical verification are unchanged. The correction specifies UTF-8 throughout
that test module. All six cases, the preserved preview continuation's 440 selected
cases, three public same-capture comparisons and warning-fatal Sphinx pass locally.
The [receipt](../evidence/continuation_resumption_20261104.json) retains separate
scopes and verified original failed CI/governance manifests. Qualify the next
committed source through an unskipped CI/governance push; never relabel the failed
original or restore its paused success-only comment updater.

### Private decoded exploration ownership (2026-11-04, #167/#148)

The [owned-state continuation](exploration_owned_state.md) changes mutable storage
construction only: private Cell support reuse and transfer of exclusively owned
fresh decoded/prepared state. Public values/support and quantities remain defensive;
direct internal caller restoration still copies state. No scientific/native rule,
logical format, source fixture, schema, dependency or request limit changes.
Original verifiers remain byte-identical. Local affected gates, exact wire/public
isolation/resealed-negative cases and controlled unprofiled comparisons precede
one unskipped exact-source CI/governance checkpoint. Record its actual SHA/SDK,
all source/installed summaries and full manifests/jobs/steps/codec receiving under
`recovered_work/exploration_profile_167_20261104/` and #167/#148/#112. The earlier
qualified runtime and diagnostic sources do not qualify these changed bytes.
Broad researcher/workload/physical closure and 0.15.0 remain open/paused.

### Exact structure and declared-component navigation (2026-11-04, #173/#148)

The [new navigation](card_assembly_component_navigation.md) has three short local
producer/fixture checkpoints (`b0f1a8a`, `63f3200`, `017bcbf`) before independent
format @8 receiving. They remain local until the completed block passes selected
gates. Selected local qualification passes 1,250 unique offline cases /35 files,
serial through the receptor, with zero test-group swap. Three actual public guide
blocks pass on four controls. Genuine original @6/@7 files from source `31593fd`/SDK154 and the live
capsule from `63f3200`/SDK156 must remain immutable. Preserve native @1–@5, original
adapters/readers and direct @4 defaults. Qualify the final block through an
unskipped exact-source CI/governance push, including copied installed payloads,
all lanes/steps/manifests and codec receiving. Retain actual counts and source/SDK
receipts under `recovered_work/assembly_component_navigation_173_20261104/` and
#173/#148/#112. Earlier pending runs do not qualify later bytes. Broad physical,
researcher/workload acceptance and 0.15.0 consolidation remain open/paused.

### Independent nonpolymer assembly reading (2026-11-03, #173/#148)

The [explicit @5 human/agent and original @7 reader](card_saved_assembly.md)
retains producer `7084894`/SDK152 and its genuine four-case fixture before frozen
receiving is implemented. Those short producer/fixture checkpoints stay local
until the completed producer/reader block is ready. Existing scientific/default
and historical bytes stay unchanged; a new closed explanation-request @2 route
applies only to format @7. Applicable local native/reader/human/agent/history,
argument/quantity/transport, documentation and static checks precede an unskipped
exact-source CI/governance push. Record actual source/SDK/counts, full manifests,
all jobs/steps/pytest summaries and codec/installed receiving in #173/#148/#112 and
`recovered_work/assembly_nonpolymer_reading_173_20261103/`. This final checkpoint
also receives the accumulated native/source and #183 scratch-retention correction;
pending older runs cannot qualify its new code. Full physical reconciliation,
researcher acceptance and 0.15.0 consolidation remain separate/open/paused.

The completed source `7882f66` /SDK `0.14.0+158.g7882f66` is now
[fully qualified](../evidence/assembly_component_checkpoint_20261104.json): CI 18/18,
governance 1/1, all manifests/jobs/steps and thirteen source/installed pytest
summaries, twelve producer routes/24 fresh frames and 36 installed codec cases.
This receives the accumulated source/native/original-reader/scratch block at its
own source. #183 is closed; no older failing run is relabeled. Later changed
runtime bytes need a new checkpoint; broader acceptance and 0.15.0 remain open/paused.

### Passed-case scratch recovery (2026-11-03, #183)

[Source-capture CI 41714274360](https://github.com/uibcdf/sabueso/actions/runs/41714274360)
reports quota/write failures in source 3.12 and installed 3.11. It is not passing
evidence. Repository and copied installed-consumer pytest now release successful
per-case scratch while retaining failed-call evidence. The configuration correction
uses an unskipped exact-source CI/governance checkpoint before the original @5
saved reader proceeds. That checkpoint also receives the accumulated opt-in native
code at `850f4ee`; it qualifies that code only if all applicable gates actually pass.
Owner #183/#167/#112; local lifecycle/bundle checks and hosted recovery evidence
belong under `recovered_work/pytest_scratch_retention_183_20261103/`. This changes
test-resource lifetime, not the scientific rules, fixture bytes or saved formats.

### Opt-in native nonpolymer key interpretation (2026-11-03, #173)

The [native @5/component-key @2 continuation](assembly_nonpolymer_binding.md)
uses already committed source inputs, keeping original @1–@4, the default and
existing human/compact/saved adapters unchanged. It is an intermediate step of
#173's native/original-reader/adapter block. After owning and broader local
native/receiving/original-reader checks, the maintainer-approved tested-code
batching route permits an intermediate `[skip ci]` push. This adds no source,
Card schema, dependency, packaging, migration or cross-component integration
boundary; those immediate gates are not deferred. Existing source-capture CI
continues independently and cannot qualify the new scientific rule.

Owner #173/#148/#112. Record the actual deferred head/SDK, tested scope and
missing matrix/governance in the issues and owned phase
`recovered_work/assembly_nonpolymer_binding_173_20261103/`. Recover the accumulated
block with an **unskipped exact-source CI/governance checkpoint** when original
saved interpretation and adapter adoption are ready, or earlier if the new native
rule is considered for adoption or the reader is deferred. Inspect full receptor
manifests, all jobs/steps, actual pytest summaries and backend/installed receiving
before claiming completed-code qualification. No skipped/older/pending run is
passing evidence for the new head.

Independent original @5 saved interpretation precedes adapter/default adoption;
full physical reconciliation, broad acceptance and paused 0.15.0 consolidation
remain separate. Earlier #181 and nonpolymer source captures retain their
independent source scope and active receiving.

### Original nonpolymer source inputs (2026-11-03, #173)

The [source continuation](rcsb_nonpolymer_inputs.md) adds an explicit query alias
and an optional original assertion input in unpublished schema 0.3.14. Original
ligand qualifiers, native generation @1–@4 and frozen saved rules are unchanged.
Three bounded public-control captures qualify the actual provider fields; no
private pilot material is used. This source/schema integration change uses an
**unskipped** exact-source CI/governance checkpoint after selected local gates,
with full gh-run-receptor manifests, actual lane summaries and backend/installed
receiving review. No skip marker substitutes for its immediate integration gate.

Owner #173/#148/#112; exact source/SDK, local resource receipts, capture hashes,
hosted IDs and recovery scripts belong under
`recovered_work/rcsb_nonpolymer_inputs_173_20261103/`. The preceding qualifier-parent
checkpoint keeps its own active capture and source scope. Pending runs qualify
neither changed runtime nor #173's future scientific reconciliation; broad
researcher/workload acceptance and paused 0.15.0 consolidation remain separate.

### Final qualifier-parent receiving checkpoint and source batching (2026-11-03, #181)

The [parent correction](../pending_bugs/entity_qualifier_parents.md) retains raw
context and introduces controlled current structural refusal. The final source
will use an **unskipped** CI/governance checkpoint after all selected local gates.
Owner #181/#148/#180/#112, with exact head/SDK/runs, full receptor capture, actual
pytest summaries and recovery proof under
`recovered_work/entity_qualifier_parents_181_20261103/`.

This final head includes the locally checked literal delivery `090c4ed` and native
field guard `1052e5a`. After its replacement runs exist, pending owned intermediate
scientific executions may be stopped to avoid redundant runner work, retaining
complete cancellation/source evidence. Completed or coverage-only near-finished
checkpoints may finish. Such intermediate runs are never relabeled as passing;
their accumulated runtime is recovered only after the actual final source passes
every applicable gate. No skipped push or reduced matrix substitutes for that
checkpoint. Strict nested glossary reinterpretation is separately deferred to #182.

The intermediate literal run `41693588616` has an observed Ubuntu 3.14 failure:
job `126118166640` stops during environment creation on HTTP 503 from
`conda.anaconda.org/uibcdf/noarch/repodata.json`, before pytest. Its original job
log is retained with #148/#112. This is an observed channel availability failure,
not evidence of a scientific test failure; it remains unqualified. Final-head
recovery must still pass that actual lane rather than inherit other lanes' results.

Transport source `5f4ab15` is already independently qualified: CI 18/18, governance
1/1, all thirteen actual lane summaries, twelve backend producers/24 frames and
twelve installed routes/36 codec cases, with full manifest/CRC/step review.
[The public receipt](../evidence/transport_checkpoint_20261103.json) and #178/#179
closeouts recover that earlier scope. #167 workload/researcher acceptance remains
open, and this does not qualify newer runtime automatically.

### Current native ligand input validation (2026-11-03, #180)

The [input contract](../pending_bugs/structure_ligand_inputs.md) adds current-only
preflight before native Card/Deck structural interpretation. Malformed list,
entry, component identifier or investigation flag causes a catalog SchemaError
with safe problem context and detailed exact inspection locations. Accepted
scientific rules/results and original saved verifiers stay unchanged. Publish
through an unskipped exact-source CI/governance checkpoint after applicable local
gates, with full gh-run-receptor captures and actual summaries reviewed before
qualification. Owner #180/#148/#112; scripts and useful proof are retained in
`recovered_work/structure_ligand_inputs_180_20261103/`. The earlier transport and
literal delivery runs keep their independent source scope/active captures.
This does not close #181, #173, broad researcher acceptance or the paused 0.15.0 route.

### Original literal ligand reading checkpoint (2026-11-03, #148)

The [TcTIM ligand continuation](card_ligand_reading.md) changes only current
literal delivery: readable exact component/instance nodes and complete typed
destinations, display selection/order, original support and inert saved reading.
Original science, navigation rules and @1–@6 verifiers remain unchanged. The
final thirteen-file local gate passes 381 cases /209.44 s, serial and guarded;
public guide execution, warning-fatal Sphinx and applicable static gates pass.
Publish through an **unskipped** exact-source checkpoint, then verify all eighteen
CI jobs, governance, thirteen actual pytest summaries, twelve backend producers
and twelve installed transport routes through full gh-run-receptor captures.
Owner #148/#112, with head/SDK/runs and recovery scripts retained in
`recovered_work/tctim_journey_148_20261103/`. Preceding transport receipts retain
their own source scope and active captures. Pending runs do not qualify this
source or close #180, #173, broad researcher acceptance or the paused 0.15.0 route.

### Large-original test admission and measured API follow-up (2026-11-03, #178/#167)

**Recovered at `5f4ab15`, SDK145**, as detailed in the public receipt above. The
following records the original failed attempt and recovery route; #178 and #179
are now closed. Later code checkpoints retain their own obligation.

Transport source `92af2c6`, SDK `0.14.0+144.g92af2c6`, has verified governance
1/1 but fails CI in two historical tests above the new default file budget.
Linux 3.12–3.14 each report 6,751 passed /2 failed. Original failed job logs and
full-receptor observation are retained; this is not a qualified code checkpoint.
The correction streams the original fixture and its hash and passes exact-size
positive budgets after asserting default refusal. All 653 package files and
frozen scientific rules stay unchanged. The [public workload study](public_transport_workload.md)
adds 45 actual saves/45 fresh reads with original content/history parity.

Publish the tested correction through a **new unskipped** exact-source checkpoint;
verify CI 18/18, governance, thirteen actual pytest summaries, twelve backend
cross-readers and twelve installed transport smokes. Once replacement is prepared,
retain the failed source's evidence and stop only its owned superseded execution
if needed. No skipped/pending/failed run closes this obligation. Owners #178/#167/
#179/#112; broader workload/researcher acceptance and 0.15.0 remain separate.

### Production exploration transport checkpoint (2026-11-03, #178/#167)

The [transport implementation](exploration_file_transport.md) changes package
runtime, public arguments, optional dependency metadata and installed receiving.
It uses an **unskipped** exact-source CI/governance checkpoint after applicable
local gates. No new intermediate runtime debt is authorized or claimed recovered
by the earlier helper checkpoint. Verify eighteen CI jobs, thirteen actual pytest
summaries, twelve installed smokes and twelve cross-read backend producers through
full gh-run-receptor evidence. Include the separately reported #179 test-isolation
correction and its fresh-process/order regressions. Owner #178/#167/#179/#112;
source/SDK, actual gates and receipts belong in those issues and the owned phase.

### Zstandard backend recovery checkpoint (2026-11-03, #178)

The [backend continuation](zstd_backend_qualification.md) changes qualification
CI and introduces a pinned test-only older-Python backend. It therefore uses an
**unskipped** checkpoint after selected local gates. Verify exact-head expanded
CI (18 jobs), governance and all twelve cross-read producer reports through full
gh-run-receptor evidence before declaring recovery of `f6b6c6c` and `11bfd62`.
Owner #178/#167/#112; source/SDK and actual receipts belong in those issues and
the owned qualification directory. Until verified, the earlier debt remains open.
No package runtime or public transport is changed.

Recovered at `1fdb771ce4f0c572a0cb5957c9eb40178f7876c6`, SDK
`0.14.0+143.g1fdb771`: [CI 18/18](https://github.com/uibcdf/sabueso/actions/runs/41585285748)
and [governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/41585285886).
Every full-capture member/step, thirteen actual summaries (nine × 6,599 public
source cases; four × 1,470 installed-provider cases) and all 24 fresh frames from
twelve platform/minor producers are verified, with zero unqualified steps.
The [closeout](https://github.com/uibcdf/sabueso/issues/178#issuecomment-6609265892)
closes the earlier helper debt, not production transport or broad acceptance.

### Intermediate compressor comparison (2026-11-03, #178)

The [repeated codec comparison](card_compressor_comparison.md) adds a stdlib-only
engineering helper/tests and technical documentation, with no package/runtime,
source, schema, dependency, migration, security-fix or production integration
change. It extends #167's locally tested intermediate batching block after
`f6b6c6c701c5b30f2b01afe1991c9167e738d424`, SDK `0.14.0+140.gf6b6c6c`.
After applicable local gates, publish through the approved `[skip ci]` route and
record the actual comparison source/SDK and receipts in #178/#167/#112. No hosted
qualification of new helper/test bytes is claimed; all 648 tracked package files
and 52 protected originals remain equal to qualified `baac143`.

Owner #178/#167/#112; recover the accumulated layout/comparison/transport scope
with final unskipped exact-SHA CI/governance through full gh-run-receptor evidence
before adoption, release or declaring the code block complete. If production
transport is deferred, recover an unskipped helper checkpoint instead. Native
3.14 measurements and mocked unavailable-backend cases are not qualification of
3.11–3.13 optional bindings or all supported platforms. Release consolidation
and broad human/workload acceptance remain paused/open as previously recorded.

### Intermediate physical-storage experiment (2026-11-03, #167)

The [engineering experiment](card_persistence_layout_experiment.md) adds only a
stdlib helper, its regression tests and technical documentation. It changes no
package runtime, Card schema, source, dependency, migration, security fix or
production integration. This is an intermediate step of the authorized #167
persistence block: after its owning local gates, use the approved `[skip ci]`
route, recording its actual source/SDK and local receipts in #167/#112. No hosted
qualification of newer helper/test bytes is claimed. The last package-runtime
checkpoint remains qualified `baac1438810eb3ef4af8a98f14116a2d0c8e547b`.

Owner #167/#112; recovery trigger is the bounded compression implementation's
final checkpoint, or earlier adoption/release consideration. Recover all
accumulated helper/receiving/runtime work with an unskipped exact-head CI and
governance run, full gh-run-receptor captures, all applicable jobs/steps and actual
summaries before closing the persistence code block or claiming release admission.
If the proposed transport is deferred, an unskipped helper checkpoint must recover
this scope before its completed-code qualification is claimed. Experimental
measurements do not close broad #148 delivery or researcher/workload acceptance.

### Intermediate component keys and declared occurrences (2026-10-30, #173)

The native component-key continuation after `6f94043` uses the maintainer-approved
intermediate `[skip ci]` route after applicable local tests and contract/docs
checks. Generation `@3` adds source-bound polymer-instance and
ligand-neighbor-reference lookup with explicit unknown/ambiguous scope; original
`@1`/`@2` stay unchanged. No source acquisition, Card schema/migration, packaging,
dependency, security or cross-component admission change is included. Local
integration is required before publication; this defers hosted qualification,
not its local integration gate. Its published intermediate is
`5c060cea3417cd0724b9f5f57316c0e7d1774560`, SDK `0.14.0+133.g5c060ce`.
The following generation `@4` continuation plans and optionally expands declared
component/operation occurrences, with exact original contexts, separate physical
scope and all-request count/text preflight. It belongs to this same intermediate
recovery block; original `@1`–`@3` remain unchanged. Its exact source/SDK and
selected local gates are recorded in #173/#148/#112 and its owned checkpoint.
That occurrence checkpoint is `a1a54360d0073f5b690da760dddc16ec98daf010`,
SDK `0.14.0+134.ga1a5436`. The following live human/agent adapter is intermediate
`77fd770e4d2a8fa94eea3fbd723a84fc90875efb`, SDK `0.14.0+135.g77fd770`.
The [independent original saved reader](card_saved_assembly.md), exact requests
and navigation complete that persistence block, including shared explanation-request
admission (#176). Its final `9aa6d68f20ed3a978f0fa177480051f516565266`, SDK
`0.14.0+137.g9aa6d68`, is qualified through an unskipped
[CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/41142089967) and
[governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/41142089964).
Full gh-run-receptor manifests/member hashes, every terminal job/step and thirteen
actual pytest summaries were verified, with zero unqualified steps. Nine repository-
input lanes each pass 6,483 cases; four installed public-Ackredit lanes each pass
1,470. This closes the component/occurrence/live/saved runtime debt through that
source, not the full #173 scientific scope. The
[owning receipt](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6536161282)
retains local scopes and original evidence. Superseded cancelled CI 41141632107 is
not qualification; #177 tracks its missing-artifact coverage-publisher failure.

### Exact structure-to-assembly navigation (2026-10-31, #148/#173)

The [new question/navigation policy](card_structure_assembly_navigation.md) changes
live exact structure links to @2 and freezes independent saved format @6. Prior
@1–@5 verifiers and scientific rules remain unchanged. Applicable local navigation,
original-reader, human/agent, documentation and integration gates precede any push.
Source-bound SHA/SDK, selected checks and hosted qualification belong to #148/#112.
The preceding `9aa6d68` green result does not qualify these new runtime bytes.
Finish the block with unskipped exact-head CI/governance through gh-run-receptor;
a pending or skipped run never establishes hosted qualification. Full physical/
contact reconciliation and researcher acceptance remain separate; 0.15.0
consolidation remains paused.

That navigation checkpoint is now qualified at
`f2732011c027be0ed65e7c17fb353e0c925bd50a`, SDK `0.14.0+138.gf273201`:
[CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/41151846182) and
[governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/41151846186).
Full receptor captures, all member hashes, archive CRC, exact source/job/step
states and thirteen actual test summaries were checked, with zero unqualified
steps. Nine repository-input lanes each pass 6,504 cases; four installed public
Ackredit lanes each pass 1,470. The
[delivered closeout](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6593649612)
retains the precise scope. The following
[preview continuation](card_navigation_preview.md) requires its own selected local
and final unskipped exact-source CI/governance qualification; f273's receipts
cannot qualify newer presentation runtime. Its source/SDK and run receipts belong
to #148/#112. No new deferred runtime debt is claimed recovered before those checks.

The `6f94043` CI finished with workflow/job success 15/15; governance has verified
1/1 evidence. Its original and fresh full captures retain nonterminal/null step
metadata inside completed successful jobs, also reproduced through the native
GitHub job API. Passing test-log summaries and terminal job conclusions are
separate from complete terminal step observations; do not mark the latter
verified. Provider diagnostic follow-up is
[gh-run-receptor #78](https://github.com/uibcdf/gh-run-receptor/issues/78), with
owner-local source/capture observations in #173/#112. This does not indicate a
failed scientific test and does not recover the newer intermediate runtime.

The [relationship-scope correction #168](../pending_bugs/structure_relationship_scope.md)
uses an **unskipped** code checkpoint because it changes named scientific
explanation admission. Its full local-original test and exact-source CI/governance
receipts are recorded in #168/#148/#112 and the owned source evidence. Once every
applicable remote gate is verified through full gh-run-receptor captures, that
exact head recovers the accumulated parent/context runtime described below.
A pending, skipped or failed run does not recover it; read the actual source/run
receipts rather than attributing an earlier green result to new runtime bytes.

At `f89df0a`, the preceding intermediate runtime block included
[original ligand-parent navigation](card_ligand_parent_navigation.md) and
[original structure context](card_structure_context_navigation.md), after the
qualified code checkpoint below. It changes only local exploration/navigation
and its historical verification, with no new source acquisition, dependency,
packaging, Card-schema/migration or shared-component admission. Its exact checked
head and local gates are recorded in #148/#112. Hosted OS/Python/installed,
coverage and governance qualification was deferred under the existing intermediate
`[skip ci]` route, owner #148/#112, until the next unskipped structural checkpoint
or authorized exact-head manual recovery. Do not apply the earlier exact-head
green result to this new runtime source. Only the verified unskipped #168 source recovers this preceding backlog.
The parent-navigation selected local gate passes 1,178 cases /577.68s serially with local-source
inputs; the changed public example, warning-fatal Sphinx and applicable static,
fixture and local governance checks pass. This is not a new full-local-suite or
hosted result.
The subsequent original structure-context gate passes **1,198 cases /590.53s**
across 40 files, including 20 new owning cases, with the same serial receptor,
local-original and fatal-warning scope. Sampled owned RSS is 773 MiB with at least
7.2 GiB genuinely free host RAM. Its new public example executes without source
queries or input mutation; applicable documentation/static/fixture/governance
checks pass. Exact-head hosted qualification remains deferred for the accumulated
parent/context runtime block, including the final editable-label source checkpoint.

**Preceding recovered code checkpoint, 2026-10-27:** `50ce8e7f228096040babbb0a05d2c69b7315c59c`,
actual tested SDK `0.14.0+115.g50ce8e7`, passes
[CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/40603174636) and
[governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/40603174661).
All full-capture members, job steps and thirteen actual summaries are checked:
nine repository-input lanes pass 5,951 cases each and four installed public-
Ackredit lanes pass 1,452 each. This recovers the accumulated code through that
SHA; it does not complete #148's broad implementation or researcher acceptance.
See the [bounded persistence review](card_persistence_cost.md) and #112/#148/#167
for source-bound receipts. The route below records the preceding implementation
history; it is not an assertion that those earlier runtime bytes still lack CI.

The first partial exploration slice A adds detached capture, literal field/topic
discovery and read, typed locations, record/byte-bounded pages, retained cursors,
quantity context and atomic raw export. Its [human continuation](card_exploration_literal.md)
adds labeled discovery, complete literal inspection, original support, local search,
selection/navigation and bounded text/HTML over the same capture. The
[structural adapter](card_structures_exploration.md) extends the same block with
original inventory/explanation/source scope, typed human columns and projected
byte/record-bounded machine selection. The [human protein journey](card_protein_exploration.md)
adds the opening, function fields and question-to-original-support/return routes,
with explicit canonical region scope over the shared inventory. The
[nature/coverage continuation](card_nature_exploration.md) adds distinct molecule
and disease routes plus original source-state views/explanations, without new
scientific rules, schema or dependencies. The
[contextual navigation continuation](card_context_navigation.md) adds source/endpoint
links, explicit supplied-capture transitions and missing/ambiguous destinations,
with exact origin/selection preservation. The
[first saved-reading continuation](card_saved_exploration.md) adds supported
literal/field persistence, recorded navigation and exact literal machine selections,
with inert input/support verification. The
[scientific continuation](card_saved_science.md) adds original structures/regions,
coverage and exact structural machine requests with frozen historical checks;
format @1 reading remains supported. No dependency/schema/shared contract changes
are introduced. The same exact-head recovery route applies.
The [structural selection continuation](card_agent_selection.md) adds typed
machine filters, exact membership and scalar order with original saved requests;
its checked intermediate head belongs to the same #148 recovery block.
The [cell-support continuation](card_cell_support.md) adds explicit per-cell
identity and complete shared assertion membership, atomic typed deferral and
bounded public cost observations. It retains this same recovery route.
The [human support/ontology continuation](card_human_support_labels.md) refines
original source roles and readable ontology basis/scopes, preserving scientific
cells and recorded saved labels. Its checked intermediate head has the same #148
exact-head recovery route.
The selected-method reference correction in that continuation guards malformed
and mixed reference declarations, missing support and partial method previews;
its targeted local gates and exact intermediate head stay in this same #148 block.
The bounded first-version audit and executable public walkthrough change only
documentation/example code; their source and checks are recorded in #148 under
this same recovery route. They do not qualify new SDK runtime bytes.
The subsequent readable structural support continuation changes human source-row
presentation and its exact saved-membership verification. It shares this #148
recovery route; the maintainer's full-design-before-0.15.0 requirement keeps the
implementation block open beyond the initial A–D audit.
The protein source-context continuation adds three source-oriented field/relationship
routes and versioned original-membership bindings. Its exact source and local
qualification remain in this same #148 block; derived/cross-topic adapters and
the full pre-0.15.0 acceptance remain open.
Original structure-local ligand-instance selection, scoped contact previews and
inert saved membership now extend that continuation. Its small entity-glossary
guard preserves malformed original declarations without inventing entity candidates.
Applicable local exploration/entity/quantity checks and the exact source receipt
belong to this same #148 deferred block; contact mapping basis and derived
navigation remain explicitly open.
The subsequent [RCSB contact integrity correction](card_contact_mapping_integrity.md)
adds scoped stored lineage/migration handling and changes conservative native
instance interpretation. Its migration/scientific checkpoint uses an unskipped
push and exact-SHA CI/governance through gh-run-receptor, rather than extending
the skip marker to immediate gates. Those receipts recover the preceding code
scope only on that actual new head; installed-artifact and broad human acceptance
remain separate requirements.
Exact heads and qualification are recorded
in #148; the recovery route below applies to each intermediate source. Its implementation scope and local
qualification are recorded in [the report](card_access_literal.md); the published
head and exact source fingerprint/receipt are recorded in the owning #148 update.
The original intermediate pushes used the existing `[skip ci]` authorization;
their historical local receipts alone did not establish remote qualification.
Subsequent unskipped checkpoints recover only their exact recorded code/input
scope. The qualified checkpoint above includes OS/Python, installed-provider,
coverage-publication and hosted-governance checks. Coverage processing percentages
are not inferred from a successful queued upload.

The documentation-only closure following `50ce8e7` uses `[skip ci]` after local
Markdown/snippet/syntax and governance checks. Tracked runtime source, scientific inputs,
schemas and installed dependency requirements are unchanged. Owner #112; the next
unskipped runtime checkpoint or authorized exact-head manual CI/governance route
recovers hosted administrative checks. No new runtime CI backlog is introduced,
and the documentation SHA is not claimed to have the code checkpoint's exact-head
remote result. Record any later intermediate code head, changed/tested scope and
missing gates separately. Preserve previous qualified-source receipts; never
label a skipped run as passing CI. Release admission retains its independent
installed-artifact route.

## Recovered block: comparative execution observation

Owners: Sabueso #108/#112. Scientific observation `31b6255`, persisted journey
`8857190` and verified bibliography `25f6163` were published through the final
implementation `25f6163b306a1a863e7ceb5b8e660bdbd2cef432`. Documentation-only
`071029f` preserves the original publication/pending-gate snapshot.

Explicitly authorized manual [CI](https://github.com/uibcdf/sabueso/actions/runs/38440535048)
passes 15/15 and [governance](https://github.com/uibcdf/sabueso/actions/runs/38440538037)
passes 1/1 on the exact implementation SHA. The
[block receipt](comparative_block_checkpoint.json) verifies complete full receptor
captures, every hash and all test summaries: nine public lanes pass 4,709 cases
with ten native skips/26 online deselections, and four installed public-Ackredit
lanes pass 1,367 cases. Ruff and default-branch coverage publication pass;
external Codecov visibility is not independently qualified. The macOS queue is
resolved; earlier pending snapshots and source/release receipts remain original.

The final local block passes 278 selected, 6,262 full local-original and 74
post-editable cases with twelve pytest-receptor workers. Source qualification
is separate from staged installed artifacts, human acceptance and release.
No scientific provider query or private content enters this receipt. #108/#112/
#132 remain open for broader scope; MOLI #36 owns the receiving boundary.

## Published integration correction

[Compact comparative credit](comparative_credit_compaction.md) emits component
operation `@2`, replacing repeated complete input lists with a versioned/hash-bound
reference to the same host operation's retained input scope. Historical `@1`
records remain readable with their original contexts. The correction is published
at `792bd0da45245ad0fca08e4b431e5e49e4d76ae8` with explicit maintainer authorization
and no skip marker. Its automatic [governance](https://github.com/uibcdf/sabueso/actions/runs/38456975421)
passes 1/1, and [CI](https://github.com/uibcdf/sabueso/actions/runs/38456975623)
passes 15/15. The [compaction receipt](comparative_credit_compaction_checkpoint.json)
independently verifies complete receptor captures, all hashes and every applicable
job summary: nine public lanes pass 4,713 cases each and four installed
public-Ackredit lanes pass 1,371 cases each. The earlier block's receipt remains
original. The [publication snapshot](comparative_credit_compaction_publication.json)
retains the originally pending state. See [TESTS.md](../TESTS.md#recovering-deferred-ci).

The platform-side [receiving PR #67](https://github.com/uibcdf/moli/pull/67) stays
with MOLI #36 for owner review. At `9c6f856`, its 19 public receiving cases and
applicable governance pass using independently qualified Sabueso `792bd0d`;
the PR is ready for review. The earlier 18-case/`25f6163` receipt stays original.
Receiving gates remain separate from Sabueso's own source qualification. Its
public fixture acceptance does not accept a ProjectRecord wire format, distributed
commit protocol, Nextia Evidence interpretation or release. Private pilot results
remain private, with installed/human acceptance separate.
