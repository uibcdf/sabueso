# Sabueso — Engineering and scientific audit, 2026-11-04

Kind: dated assessment and proposed follow-up protocol. Owner: Sabueso maintainers;
coordination: [#112](https://github.com/uibcdf/sabueso/issues/112).
Baseline: `34135591642ae378705343449a037f8a4469c968`, with the existing,
uncommitted component-preview continuation present in the working tree.

This records the maintainer-requested review of correctness, engineering quality,
scientific usefulness and growth. It is a directed audit, not an exhaustive
certification or an implementation decision. Implementation and publication were
paused for the review. Recording this report does not resume them or consolidate
0.15.0. Follow-up status belongs in the checkpoint and owning issues; preserve
the observations below as the dated baseline.

Document expanded on 2026-11-04 at the maintainer's request to make coverage,
impact assessment, independent validation and closure criteria explicit. This
extension improves the audit record and plan; it does not represent additional
completed scientific experiments or a comprehensive certification.

Follow-up scheduling now lives in the
[integrated continuation plan](CONTINUATION_PLAN_20261104.md). It reconciles the
recommendations here with the accepted full 0.15.0 scope and preserved prior work.
In particular, the maintenance-release suggestion below remains unadopted: the
existing maintainer decision directs ongoing corrections to 0.15.0. Preparing the
continuation plan does not resume implementation or publication.

Execution update: the maintainer subsequently resumed implementation on
2026-11-04. Reports #184/#185/#186 are delivered; correction and acceptance status
belong to the continuation plan, checkpoint and owning issues. The audit's
pause-time observations and reproduction scope remain unchanged.

## Overall assessment

Sabueso has a strong architectural foundation and a credible path to becoming a
powerful scientific Knowledge component. Its explicit source support, uncertainty,
versioned derivations and historical reading are substantial strengths. Recovery
and subsequent development have added useful capabilities without requiring a
change to its purpose: **Sabueso knows; it does not discover.**

Scientific maturity is uneven. Two reproduced bioactivity defects prevent a
blanket statement that the library is scientifically correct. A known measurement
grouping limitation also deserves renewed attention. Structural exploration is
more developed than several other scientific journeys. Engineering tests and
traceable answers are necessary, but they do not establish that every scientific
rule or human workflow is adequate.

The recommended next investment is scientific correctness and independently
reviewed usefulness, followed by completion and homogenization of the human/agent
experience. More sources or more panels alone would not close these gaps.

## Scope and limits

The review covered the developer guide, MOLI's public Sabueso architecture,
selected core scientific implementations, exploration profiles/rendering/storage,
historical receiving contracts and existing acceptance plans. In-memory synthetic
probes exercised classification, the public `Card.bioactivities()` route and
measurement grouping. No private vertical-pilot content was read or reproduced;
no molecular-provider requests were made.

No new full-suite run was performed for this audit. The previously running
component-preview gates finished with 440 unique selected cases across 13 files;
that is evidence for their selected behavior, not validation of the audit findings
or of the whole library. No scientific fix was applied during the review.

The reproduced cases do not measure prevalence in real source data or demonstrate
an affected real molecule. Four affected function bodies were compared by AST
against tag `0.14.0`; they match that tagged source. The installed 0.14.0 artifact
was not executed. Release impact therefore needs its own qualification.

## Coverage and evidence map

Coverage here describes **this audit**, not the existence or quality of tests
elsewhere in the repository. `Directed inspection` means selected documentation
and implementation paths were inspected; `synthetic reproduction` means a stated
case was exercised. `Document review` is not runtime validation. `Not assessed`
is an open coverage gap, not a defect. No row is exhaustively qualified.

| Area | Evidence in this audit | Remaining review and completion evidence |
| --- | --- | --- |
| Purpose and MOLI boundaries | Document review of architecture and developer guidance | Trace representative public workflows across component boundaries; obtain consumer-owned acceptance where applicable |
| Acquisition, mappings and enrichers | Directed inspection of registry contracts and selected HTTP paths | Sample every supported provider family; verify original response → mapping → Card support, pagination, incomplete responses, failure/refresh and declared rights |
| Entity identity and aggregation | Document review of source-stated identity and observation preservation | Challenge stereo/charge/parent forms, isoforms/constructs, aliases, taxon and conflicting cross-references; inspect alternative-value preservation |
| Quantities and scientific qualifiers | Directed inspection of quantity boundaries and bioactivity conversion | Check dimensions, unit policies, censored/range/uncertainty values and source mislabelling across mappings, derived outputs and serialization |
| Bioactivity interpretation | Directed inspection and synthetic reproduction, including public Card path | A1/A2 corrections, public-fixture impact, full relation/threshold cases and independently reviewed assay assumptions |
| Measurement correspondence | Directed inspection and synthetic reproduction | A3 context-aware comparison, source copies versus independent records, counting/voting effects and missing-context behavior |
| Structural and residue knowledge | Review of existing structural contracts and receiving reports | Independently review reference/author numbering, constructs, predicted/experimental distinction and assembly/contact scope; do not inherit acceptance from prior receipts |
| Variants, tissue, disease and clinical knowledge | Document review of existing capabilities and limitations | Review coordinate/isoform scope, hierarchy versus equivalence, association direction, trial status and unsupported efficacy/pathogenicity interpretations |
| Literature and curation | Document review of assertion, mention and scientist-review boundaries | Validate located support, extraction attribution, correction/retraction handling and source terms; review statements against the actual source |
| Human and agent Card access | Directed inspection of profiles, rendering and shared captured access | Question-by-question parity and completeness; uncoached human navigation; machine projection/pagination/cost; all promised nature-specific panels |
| Deck and collection workflows | Not systematically assessed | Membership/order/duplicate and revision semantics; expand/filter/compare/support routes; collection usability. Distinguish current scope from the separately requested future Deck navigation API |
| Persistence, history and interoperability | Directed inspection of storage and frozen-reader design, review of existing receipts | Version/schema compatibility matrix, malformed/tampered/truncated inputs, atomic writes and actual installed consumer receiving |
| Performance and resource lifetime | Review of bounded workload reports and selected HTTP code | Representative input/history sizes, retained memory, scratch, connection/file lifetime, cancellation and explicit refusal/override behavior |
| Maintainability and API consistency | Directed inspection of mutable orchestration and frozen compatibility separation | Trace change propagation, argument/diagnostic/dependency conventions, public documentation and repeated mutable logic; justify refactoring with concrete maintenance cases |
| Security, packaging and delivery | Not systematically assessed; existing qualification routes reviewed | Input/decompression and rendering boundaries, dependency/security checks, clean installed artifacts and exact-candidate CI; no security certification is implied |

The map deliberately exposes gaps rather than assigning an unsupported percentage
or a single quality score. Later audits should identify exact files/rules/providers
sampled and retain the unreviewed remainder. Full provider coverage and exhaustive
scientific correctness cannot be inferred from a representative sample.

## Method and evidence requirements for the next audit pass

Use the same trace for each selected question:
**source record → mapping → stored assertion/value → derived rule → public answer
→ explanation → human/agent delivery → saved/consumer reading**. Identify where a
claim changes meaning or loses context. A failing layer should not be hidden by
agreement between downstream views that all reuse it.

For each reproduction or acceptance result, record:

- Exact source revision, relevant working-tree differences, Python/package versions,
  selected rule and parameters, fixture/input identity and public-data rights.
- The question, original input, independent expected answer or permitted outcomes,
  observed result, reproduction command and relevant output location/digest.
- The scientific reason for the expectation and reviewer status. If source methods
  are unavailable or experts disagree, retain that uncertainty rather than inventing
  a reference answer.
- Scope exclusions, affected public paths, historical compatibility and the
  distinction between source correctness, software interpretation and usability.
- Owning issue, accountable component, disposition and explicit next review trigger.

Keep **observation**, **inferred impact**, **unverified hypothesis** and **proposed
improvement** separate. Prioritize by scientific consequence, plausible reach,
detectability and recovery cost; test counts and code size are not severity measures.
A1/A2 are high priority because they can change categorical scientific answers.
A3 is a known limitation with a potential effect on counts and votes; its prevalence
and downstream magnitude remain unknown. No security severity is assigned here.

## Foundations worth preserving

- [Architecture](ARCHITECTURE.md) separates SourceAssertions, derived knowledge,
  Evidence and project conclusions. An interpreted class is not a new source fact.
- Molecular identity requires source statements. Ambiguity, incompatible context,
  failed acquisition and unasked questions remain distinguishable from absence.
- Physical quantities retain units and explicit conversion boundaries; source
  observations and pinned snapshots make answers inspectable and reproducible.
- Independent historical readers preserve original scientific meanings. A new
  rule must not silently reinterpret an old saved result.
- Declared source clients, mappings and enrichers make provider coverage and
  source-to-card contributions inspectable. Raw access, card enrichment, licensing
  and successful live availability remain distinct claims.
- Human views and compact agent access share captured knowledge, original support
  and navigation. This is the right basis for accessible and economical use.

## Scientific findings

### A1. Censored bioactivity values can receive unsupported classes

**Status: reproduced correctness defect; high priority.**
Implementation: [`bioactivities.py`](../sabueso/core/bioactivities.py),
`_band`, `_bounded` and `classify_measurement`; rule `bioactivity_class@3`.

Under default thresholds:

| Synthetic input | Observed result | Problem |
| --- | --- | --- |
| IC50 = 100 µM | `weak` | Reference boundary under the existing policy |
| IC50 ≥ 100 µM | `inactive` | Includes the exact boundary classified as `weak` by the same policy |
| Inhibition > 40% at 200 µM | `inactive`, basis `single_point` | A lower bound of 40% does not establish inhibition below the 50% threshold |

The third result was also reproduced through public `Card.bioactivities()` with
an explicitly synthetic SourceAssertion, supported activity relationship and direct
target assignment. The source relation and value remained present, but the derived
measurement and molecule classes were `inactive`.

Minimal classifier reproduction at the audited baseline:

```python
from sabueso.core.bioactivities import classify_measurement

for relation in ("=", ">="):
    result = classify_measurement(
        {"type": "IC50", "value": 100, "units": "uM", "relation": relation}
    )
    print(relation, result["class"])

result = classify_measurement(
    {"type": "Inhibition", "value": 40, "units": "%", "relation": ">"},
    assay_description="Inhibition at 200 uM",
)
print(result["class"], result["basis"])
```

Observed output: `= weak`, `>= inactive`, then `inactive single_point`.
These are observations of the old behavior, not assertions of desired science.

A correction should reason over the permitted interval, including open/closed
endpoints, before assigning a categorical class. When the interval permits
different outcomes, preserve uncertainty. Review all relation/threshold pairs,
ranges and the assumptions behind interpreting single-point inhibition as an
IC50 bound. The library should disclose those assumptions rather than equating
an assay result with a general claim of molecular activity.

### A2. Assay text can supply the wrong concentration role

**Status: reproduced defect on synthetic ambiguous text; high priority.**
Implementation: `single_point_concentration` in
[`bioactivities.py`](../sabueso/core/bioactivities.py).

For `Assay at 1 uM substrate; inhibition measured at 100 uM compound`, the parser
selects 1 µM, the first matching concentration. With exact 70% inhibition the
classifier returns `active` using that substrate concentration as the tested
compound concentration. The pattern is not bound to the chemical role.

```python
from sabueso.core.bioactivities import (
    classify_measurement,
    single_point_concentration,
)

description = "Assay at 1 uM substrate; inhibition measured at 100 uM compound"
print(single_point_concentration(description))
result = classify_measurement(
    {"type": "Inhibition", "value": 70, "units": "%", "relation": "="},
    assay_description=description,
)
print(result["class"])
```

The first result represents 1 µM; the second is `active`. This establishes a
failure mode, not its frequency in ChEMBL or any other source. Prefer explicit
source fields where available. Text extraction needs a defensible role binding,
retained source location and an explicit ambiguous/unknown result when the role
cannot be established. Missing role information must not become an assumed dose.

### A3. Measurement correspondence lacks sufficient assay context

**Status: known scientific limitation reproduced; not a new regression.**
Implementation: [`measurements.py`](../sabueso/core/measurements.py),
`measurement_identity@1`. The
[original design](archive/measurement_identity.md#risks-and-future-problems)
already identifies assay-description refinement as future `@2` work.

Two synthetic supported records from different sources, with the same publication,
molecule, measurement type, relation and IC50 of 100 nM, were grouped with basis
`statement` and no ambiguity despite these descriptions:

- `Synthetic wild-type, pH7`
- `Synthetic mutant construct, pH5`

The matching rule considers publication, molecular correspondence, relation and
numeric agreement at the coarser precision. These descriptions do not constrain
the statement match. Original records remain intact: this is a derived judgement
of measurement correspondence, not a destructive merge of molecular identities.

Distinct experimental contexts can therefore be counted as one measurement.
Review construct/isoform/variant, assay endpoint, conditions and explicit source
copy declarations separately. Missing context is not proof of equal context.
An explicit source-declared copy and a tentative cross-source correspondence
should have distinguishable bases and consequences for counting and voting.

## Correction and reporting requirements

The ASTs of `_band`, `_bounded`, `classify_measurement` and
`single_point_concentration` match their 0.14.0 tagged definitions. This is not a
claim that the entire module is identical. Assess whether a separately qualified
integrity maintenance release is warranted before the broader 0.15.0 work finishes.
No release decision is made here.

Corrections need new named/versioned rules, explicit default-adoption decisions,
downstream class/count/explanation checks, human/agent agreement and genuine
historical receiving controls. Preserve `bioactivity_class@3` and
`measurement_identity@1` meanings when explicitly replaying historical results.
Do not rewrite stored source assertions or silently repair an old interpretation.

| Finding | Owning follow-up | Status at this report |
| --- | --- | --- |
| A1: censoring and boundaries | [#184](https://github.com/uibcdf/sabueso/issues/184), coordinate with #112; cross-link historical [#37](https://github.com/uibcdf/sabueso/issues/37) | Reported on resumption, 2026-11-04; correction pending |
| A2: concentration role | [#185](https://github.com/uibcdf/sabueso/issues/185), coordinated with #184 and #112 | Reported on resumption, 2026-11-04; correction pending |
| A3: assay-aware grouping | [#186](https://github.com/uibcdf/sabueso/issues/186); cross-link closed [#66](https://github.com/uibcdf/sabueso/issues/66) and #112 | Proposal reported on resumption, 2026-11-04; review pending |

This document preserves the maintainer handoff requested during the pause. The
owning reports above were delivered when implementation resumed; this does not
close their scientific or delivery acceptance. Existing closed issues are
historical context, not evidence that these findings have been fixed.

## Impact assessment and finding closure

First assess the frozen public corpus already available, without refreshing it or
changing its original answers. Inventory the source records eligible for each
affected rule, then distinguish records that exercise the suspicious path from
records whose scientific interpretation is independently confirmed to be wrong.
Report both numerators and denominators, exclusions and unavailable assay context.
No matching case in a limited corpus would establish only that bounded result.

For affected records, trace measurement class → molecule aggregation/voting →
counts/decks/comparisons → explanations and exported/saved answers, wherever those
consumers actually use the result. This is a proposed dependency investigation,
not a claim that all of these paths are affected. Compare old and proposed new
rules on the same original inputs, preserving every source record and recording
why each output changes. Review the 0.14.0 installed artifact separately before
claiming verified released behavior or a released fix.

| Finding | Owner and proposed priority | Required correction/decision evidence | Historical and delivery acceptance |
| --- | --- | --- | --- |
| A1 | Sabueso scientific rules; high, before broader activity presentation | All supported relations at/below/above thresholds; open/closed and crossing intervals; missing/invalid values; justified single-point assumptions; public Card and aggregation regressions with independently justified outcomes | New named rule and explicit default decision; unchanged original records; legacy interpretation available; explanation/human/agent consistency; exact-candidate local and applicable installed/CI qualification |
| A2 | Sabueso assay interpretation; high, coordinated with A1 | Distinguish compound/substrate/cofactor and multiple concentrations; explicit-role positives plus ambiguous/missing-role abstention; preserve original text/location and extraction basis; evaluate affected public records | Version the interpretation and its consumers; demonstrate that unsupported dose selection cannot silently change a class; preserve genuine old saved results |
| A3 | Sabueso measurement identity; next scientific design review | Explicit copies, independent sources, conflicting constructs/conditions, equal rounded values and missing context; justify group splits/joins and effects on counts/votes; scientist-reviewed correspondence criteria | Retain original records and `@1`; adopt the new policy explicitly with coherent explanations and original saved compatibility |

Closure requires an observable owning report, a scientifically justified correction
or explicit documented disposition, reproducible validation and a clear delivery
status. Distinguish **reported**, **reproduced**, **fixed locally**, **source-qualified**,
**installed-qualified** and **released**. A merged change or closed issue alone
does not establish that users have received a verified fix. For A3, documenting an
accepted limitation can close a design question but does not implement `@2`.

## Systematic review of scientific rules

Build the rule inventory from the implementation and its declared consumers, then
reconcile it with the guide. For each named/versioned rule record its scientific
question, input eligibility, source/identity/coordinate scope, units, assumptions,
thresholds, treatment of uncertainty, refusal/abstention conditions and supported
interpretation. Include explanations, aggregation and historical readers as
consumers. Select current high-consequence rules first; do not silently revise
frozen historical meanings.

For each family, challenge at least these applicable boundaries:

| Rule family | Independent scientific challenge |
| --- | --- |
| Activity and physicochemical interpretation | Endpoint comparability, censored data, assay role/conditions, units, measured versus predicted values, uncertainty and threshold sensitivity |
| Identity, correspondence and grouping | Same label versus stated identity; stereo/charge/parent distinctions; equal rounded values in different experiments; explicit copies versus independent observations |
| Structures, regions, sites and assemblies | Reference/author numbering, construct and isoform differences, missing residues, ambiguous mappings, source declarations versus calculated physical contacts, model uncertainty |
| Variants, expression and comparative context | Assembly/transcript/tissue scope, missing coverage, supplied correspondence, association versus functional or pathogenic interpretation |
| Disease, clinical and literature context | Hierarchy versus equivalence, direction of association, trial/indication versus outcome, accession mention versus supported biological statement |

Useful cross-cutting checks include equivalent-unit invariance, preservation of
conflicting support, order dependence only where explicitly defined, and loss of
certainty when required context is removed. Apply such properties only where the
scientific contract justifies them. A new source statement may legitimately alter
an answer; an unrelated record must not silently supply its missing basis.

## Independent scientific and user benchmark

Extend the [existing acceptance plan](pending_proposals/consumer_scientific_acceptance.md)
and [public HK2 system](HK2_TEST_SYSTEM.md), alongside the public TcTIM/HsTIM
fixtures. Add public small-molecule and disease cases for their distinct profiles;
protein examples cannot qualify those experiences. This is a proposed benchmark,
not a completed dataset or a new authorization for provider acquisition.

| Question family | Required counter-case or limit |
| --- | --- |
| Which entity and molecular form am I reading? | Similar name, different taxon/isoform/stereochemistry, conflicting source identity |
| What does this activity measurement establish? | Censored endpoint, wrong concentration role, unknown method or non-comparable assay |
| How many independent measurements support this summary? | Declared copy, rounded agreement, conflicting construct and missing context |
| Which structure supports this region or site? | Unmapped numbering, missing residues, different construct, predicted-only support |
| What is declared about assembly or contacts? | Generator declaration without established physical membership/contact geometry |
| What can I infer from this variant or tissue entry? | Unresolved coordinates/isoform or absent coverage; no automatic pathogenicity claim |
| What clinical or disease association is actually stated? | Trial citation without outcome, hierarchy without identity, unqueried source |
| Where does this statement come from? | Mere mention, incomplete locator, conflicting statements or unsupported attribution |
| Can I recover the same supported answer later? | Source refresh, original rule/version, missing saved destination and absent sidecar |
| Can I inspect a collection without losing member context? | Duplicate/revised members, partial support and heterogeneous entity natures |

For every case, specify the question and source-grounded expected answer or range
of permitted answers **before using current implementation output as an oracle**.
Separate scientific reviewer judgement from implementation author judgement;
record unresolved disagreement. Include positive, conflicting, absent, unasked,
failed, partial and non-applicable cases where meaningful. Synthetic adversarial
inputs supplement public source examples; they do not establish real-world prevalence.

Run the same supported question through native science, human exploration, compact
agent access and original saved reading wherever each route is implemented.
Require agreement on scientific content, scope, quantities, uncertainty and support,
not identical formatting. Mark a missing route as a capability gap; literal export
does not count as a completed scientific panel. Agent projections/pages must expose
omissions and retain an actionable route to complete content and original support.

Human review should include researchers unfamiliar with Card internals. Give them
scientific tasks, not a rehearsed sequence of API calls, and observe whether they
can find the answer, explain its limitations, inspect support and return to context.
Record completion, assistance, wrong turns, misunderstood labels and unsupported
conclusions separately from elapsed time and perceived usefulness. Choose workload
and usability targets before evaluating the candidate; this audit invents no
unvalidated universal latency or satisfaction threshold.

Agent evaluation additionally records completeness, number of calls and delivered
bytes (and tokens under a named tokenizer if measured). A smaller payload is not
a success if it omits uncertainty or forces unsupported inference. Successful task
completion must not depend on reading all raw Card content when an exact supported
selection exists.

## Engineering and experience improvements

The current exploration surface is substantial. Mutable orchestration spans
question dispatch, options, scientific adapters, explanation, rendering, agent
selection and saved reading. Growth across those paths creates a coordination
risk. Review a common adapter contract and a capability inventory so a new
scientific question has explicit support in every applicable route.

Homogenization should target current mutable implementation and user semantics.
Historical verification modules deliberately preserve older meanings; similar
code there is not by itself unnecessary duplication. Do not deduplicate frozen
readers into current producers as a cleanup exercise.

Nature-specific journeys remain uneven. The protein profile has rich structural
topics, while small-molecule and disease profiles are narrower. Literal access
to retained content does not replace a readable, scientifically contextualized
panel. Complete the [broad exploration inventory](pending_proposals/card_exploration_completion_0150.md),
including activities, clinical context, variants, sites and comparisons, with
clear unsupported/partial states and consistent return/source navigation.

Whole-session capture, retained history and saved-reading costs still need
representative acceptance under [#167](https://github.com/uibcdf/sabueso/issues/167).
Local improvements on a small workload are not general latency or memory guarantees.
[#174](https://github.com/uibcdf/sabueso/issues/174) separately tracks unbounded
HTTP reads before JSON decoding: the unbounded path is observed; resulting memory
exhaustion is a hypothesis, not a measured failure in this audit. Limits must be
visible, preserve completeness reporting and permit deliberate override; silent
truncation is not an acceptable optimization.

### Engineering audit execution and acceptance

Use realistic small, medium and large public or explicitly synthetic workloads,
including increasing retained history and repeated operations. Record input counts,
serialized size, environment, cold/warm state, wall time, peak and retained memory,
swap and scratch use. Separate acquisition, capture, scientific calculation, preview,
compact selection, save and fresh-process read. A bounded preview does not prove
bounded full capture; compressed file size does not bound decoded memory.

Inspect malformed inputs, truncated/corrupted files, decompression limits, HTML
escaping, cancellation and resource cleanup at the relevant boundaries. These are
review targets, not newly observed vulnerabilities. Check atomic failure behavior,
clear diagnostics and deliberate raised/unlimited budgets where supported. Run
heavy checks sequentially within the existing resource safeguards; do not create
unnecessary parallel workers or permanent diagnostic copies.

For maintainability, trace a representative new scientific question across current
adapters, options, explanations, views, agent selection and saved contracts. Record
every place that needs a coordinated edit and any actual divergence. Use that
evidence to choose a bounded refactor, preserving public arguments, SMonitor
diagnostics, DepDigest boundaries and frozen historical predicates. A smaller file
or fewer lines alone is not acceptance evidence.

Review packaging and consumer delivery through the existing release and
[test policy](TESTS.md), rather than treating editable-checkout success as installed
qualification. Keep exact-source CI, original-artifact receiving and scientist
acceptance separate. Retain only useful audit evidence with an owner and review
trigger; remove owned disposable scratch after its last needed use.

## Scientific growth within Sabueso's purpose

| Direction | Scientific benefit and required boundary |
| --- | --- |
| Context-aware comparability | Compare measurements only with explicit assay, construct, isoform, variant, molecular state, cofactor and condition context; expose what is unknown |
| Uncertainty and censoring | Preserve ranges, detection limits and stated uncertainty; name/version endpoint-specific assumptions instead of hiding them in a class |
| Supported multi-Card comparisons | Distinguish source independence, declared copies and tentative correspondence; explain each comparison without inventing identity |
| Located literature assertions | Trace statements to source locations, extraction method and scientific review; mentions alone do not establish a biological claim |
| Peptide and biotechnology journeys | Scope modified molecules, constructs and other entity types from concrete questions and curated acceptance cases before adding providers |

These extend Knowledge rather than moving modeling, geometric computation,
experimental discovery or project-owned Evidence into Sabueso. Coordinate shared
contracts with MOLI and consumer-owned work with the appropriate component.
They elaborate the [scientific potential](SCIENTIFIC_POTENTIAL.md) and both existing
development routes, rather than replacing either route with an unrelated backlog.

## Recommended resumption order and acceptance

This is a recommendation awaiting resumption, not an already adopted schedule.

The immediate deliverable is a bounded correctness block for A1/A2 and an impact
report, not completion of every audit dimension before fixing known errors.
Follow with A3 and risk-prioritized rule families. Each block updates the coverage
map and owning issues with actual evidence; unassessed areas remain visible.

1. Report A1/A2 and correct the scientific classifications with explicit versioning,
   independent expected outcomes and historical compatibility. Assess released
   impact and any maintenance delivery separately.
2. Scope A3 with assay-aware positive, conflicting and missing-context examples;
   determine how tentative correspondence affects counts and molecule classes.
3. Establish independently reviewed scientific question benchmarks across the
   existing public test systems and entity natures. Cover positive, conflicting,
   absent, unasked, failed, partial and adversarial inputs. Tests should challenge
   scientific assumptions, not only reproduce implemented rules.
4. Finish the promised human/agent panels using shared scientific adapters and
   nature-specific language. Validate that a scientist can find an answer, inspect
   its support and limits, and return to context without knowing storage internals.
5. Qualify representative session costs, installed delivery and remaining consumer
   contracts before consolidating 0.15.0. Preserve the full agreed scope and the
   distinction between local tests, scientific acceptance and release qualification.

The intended exceptional experience requires all of these: a useful answer,
scientifically defensible interpretation, visible limitations, effortless access
to original support and acceptable cost. No test count or attractive preview
alone establishes that outcome. The existing
[consumer scientific acceptance plan](pending_proposals/consumer_scientific_acceptance.md)
provides a starting point for that independent review.

## Audit completion versus release readiness

The document is now a broader assessment and executable review plan. The audit
itself remains incomplete until the selected coverage gaps have actual results,
finding dispositions and independent review. Do not mark an area complete merely
because its checklist or tests have been written.

For each future bounded audit checkpoint, publish a scope statement identifying
what was examined, what passed, what remains unresolved and which scientific
claims remain unsupported. High-consequence correctness findings need explicit
disposition before claiming the affected capability scientifically qualified.
Sampling or reviewer availability limits remain part of that statement.

The maintainer's full Card exploration and human-experience requirement before
0.15.0 remains the accepted release scope in the
[completion inventory](pending_proposals/card_exploration_completion_0150.md).
The expanded audit does not automatically add every future growth direction or
future Deck interface to that release, waive any existing gate, or resume release
consolidation. Proposed priorities and benchmark targets require explicit recording
when adopted. Scientific growth, maintenance correction, usability acceptance and
release delivery are related workstreams with distinct evidence of completion.
