# Sabueso — Integrated continuation plan after the audit

Kind: living work plan. Prepared 2026-11-04 at the maintainer's request.
Coordination: [#112](https://github.com/uibcdf/sabueso/issues/112).
Implementation owners remain with each component and feature issue.

## Objective and authority

**0.15.0 must deliver the intended "wow" experience: exceptional scientific
usefulness with simple, understandable and coherent Card exploration.** This is
an existing acceptance requirement for the full broad design, carried through
each implementation block and demonstrated with researchers before consolidation.

Deliver scientifically defensible, understandable and efficient access to Card
knowledge for researchers and agents, while preserving Sabueso's Knowledge role,
source support and historical meanings. Integrate the
[audit findings](GLOBAL_AUDIT_20261104.md) with the existing foundational and
pilot-driven routes. Neither the audit nor presentation work replaces those routes.

The maintainer resumed implementation of this plan on 2026-11-04. Development,
ordinary technical reporting and previously authorized development publication
resume; release consolidation/publication remain subject to the gates below.

The accepted delivery target remains **0.15.0 for all ongoing implementations and
corrections**, with the entire broad Card exploration design and validated human
experience. Follow the [accepted release scope](pending_proposals/release_consolidation_0150.md).
There is no separate maintenance-release workstream. The audit's suggestion to
consider one is an unadopted recommendation; changing the delivery target would
require a new maintainer decision. Published artifacts and original rules/readers
remain immutable. Candidate selection, freezing, staging and release publication
remain paused until the earlier acceptance gates are met and resumption is agreed.

## Required wow experience in 0.15.0

The researcher's intended experience is: **"I understand what we know about this
system, I can find what matters to my question, I can see why it is supported,
and I know how to continue."** Preserve the
[five interaction refinements](pending_proposals/card_human_exploration_api.md#five-required-interaction-design-refinements)
and [nature-specific acceptance](pending_proposals/card_exploration_detailed_design.md#decision-assistance-and-acceptance).
The following criteria make that goal observable:

| Experience | Required demonstration on the supported journeys |
| --- | --- |
| Immediate orientation | The opening identifies the entity and captured date/scope, summarizes useful retained knowledge and consequential gaps/conflicts, and offers a small set of understandable next actions |
| Questions that match scientific work | Researchers discover relevant questions and options through familiar scientific language, help and a consistent small API vocabulary, without learning schema paths, pins or SourceAssertion IDs |
| Understandable depth and complete access | Readable summaries expose important units, qualifiers, uncertainty and context; progressive inspection reaches every retained value, alternative and source, including content outside dedicated panels |
| Continuous exploration | A supported cross-topic journey retains the exact entity, snapshot and selection, shows actionable destinations and a clear way back, and explains unavailable joins or empty results |
| Useful decision assistance | Explicit criteria reveal supported options, exclusions, alternatives and unknowns; contextual next steps help the researcher inspect or change criteria without unsupported ranking, causal claims or efficacy conclusions |
| Nature-appropriate clarity | Protein, small-molecule and disease questions use their own scientific language and presentations with familiar navigation; unknown natures keep complete inspection and explicit interpretation limits |
| Fluent and reproducible work | Plain Python/text and Jupyter preserve essential meaning; measured workloads meet agreed budgets, limits/recovery are understandable, and saved reading recovers the original answer, context and support |

### Make the experience part of each block

Every user-facing slice in B0–B6 carries a concrete scientific task, the proposed
opening/calls and text/HTML responses, the original-support route, applicable
cross-topic/back navigation, and empty/ambiguous recovery. Review that small
journey during implementation. Scientific B1/B2 work must also expose its revised
meaning and uncertainty intelligibly through the public answers/explanations it
changes; it must not leave a new class or grouping basis unexplained.

Keep a short experience review in each block's owning receipt: what became easier
to understand or accomplish, what remains awkward, what was observed versus
predicted, and the next concrete improvement. Reuse these journeys for researcher
feedback as slices become ready. B7 integrates and validates them; it is not the
first time their human experience is considered. Backend work links to the journey
it enables rather than inventing an artificial UI demonstration.

Agent access retains the same scientific guarantees through economical structured
selection and complete inspectability. It need not reproduce the human interface
or consume human prose. Agent conformance and human usefulness remain separate
acceptance dimensions.

### Demonstrate acceptance before B8

Exercise actual public protein, molecule and disease journeys with the maintainer
and a researcher unfamiliar with Sabueso internals, with declared Python
familiarity and without developer coaching through the task. Record correct
understanding, completion, assistance, navigation failures, scientific
misinterpretations, workload results and specific reviewer feedback on usefulness
and ease. Revise and recheck the failed journeys; retain observed feedback rather
than predicting an enthusiastic reaction.

The experience remains pending when a required journey cannot be completed,
needs internal schema explanations for routine use, conceals a consequential
qualifier, loses context, or leaves required content unreachable. These failures
block its acceptance even if technical tests pass. Record subjective presentation
preferences separately from task/scientific failures. No invented satisfaction
score or literal exclamation is an acceptance measure.

**B8 requires explicit recorded human acceptance under #148, alongside scientific,
agent, workload and technical qualification.** Completing panels or passing tests
alone cannot satisfy it. The full design and this experience cannot be postponed
to after 0.15.0 without a new maintainer scope decision. This carries forward the
accepted Card scope; it does not add the separately scheduled viewer, Deck or
video projects to this release.

## Starting state and first actions

Execution update, 2026-11-04: accumulated B0/opt-in B1 source `1290201` is
[qualified](evidence/bioactivity_opt_in_checkpoint_20261104.json): CI 18/18 and
governance 1/1 with complete source/installed and codec receiving. The next B1
slice adopts @4 for current activity/ligand answers and tables, with explicit
original @3, new packet mapping @15 and genuine old @14 reading. Current
integration passes 338 affected cases; later changed bytes need their own hosted
qualification. See
[the scientific scope and public-input comparison](pending_bugs/bioactivity_interpretation.md).
Published final source `7667754` passes 77 post-editable cases; its own CI/governance
are pending complete receiving. Intermediate `7853039` retains its failed
producer-stamp comparison and premature publication record; current scientific
recomputation and exact original stored reading are checked separately.
Independent scientific/consumer acceptance and rich activity exploration remain
open; no scientific/human acceptance is claimed. The next exact-source
checkpoint receives the accumulated changes, without requiring every intermediate
development SHA to acquire a separate green matrix.

- Pre-audit development baseline: `34135591642ae378705343449a037f8a4469c968`, SDK
  `0.14.0+160.g3413559`. Its private exploration-copy optimization has local checks;
  its exact-source remote qualification failed. All four Windows source lanes
  failed one new direct-restore test: implicit text decoding changed UTF-8 content
  before digest validation. Explicit UTF-8 passes locally; simulated cp1252
  reproduces the refusal. Production UTF-8 reading is unchanged. Recover on the
  corrected source `1290201`, now qualified; the failed original remains unqualified.
- The component-preview continuation comprises the renderer, two test files
  and associated documentation. Its final selected local gates passed 440 unique
  cases across 13 files. Public same-capture presentation comparisons and
  warning-fatal Sphinx pass. The presentation/encoding checkpoint is published
  and included in the qualified `1290201` source.
- A1/A2 are reproduced scientific defects; A3 is a reproduced known limitation.
  Owning reports are #184, #185 and #186 respectively. A1/A2 have conservative
  default/consumer implementation; new hosted and independent acceptance remain
  pending. A3 correspondence work is next.
  The broader audit contains explicit unassessed areas, not completed validation.
- [B2 preparation](pending_proposals/assay_aware_measurement_correspondence.md)
  now inventories two exact retained public Cards: all 29 accepted @1 statement
  edges lack one mapped assay description. Candidate copy/correspondence/count/vote
  semantics and independent expected examples are specified for review. The later
  opt-in measurement @2 candidate is now implemented across direct activity/ligand
  answers, explanations and tables, with four same-input public comparisons and
  the actual guide block. @1/defaults and packet meanings stay fixed; no independence
  finding, default adoption or independent scientist/consumer acceptance is claimed.
- Rich activity, clinical, variant/comparative and other nature/shared panels,
  physical assembly reconciliation, broad human acceptance and workload acceptance
  remain open. Completed structural slices must not be reimplemented from scratch.

On resumption, inspect the actual branch, working tree, editable imports and
owned receipts before acting. Preserve existing work and original fixtures; do
not require a clean tree by discarding changes or reapplying the removed stash.
Reconcile any later contributor changes before committing or pushing.

B2 continuation: the [six-case dossier](pending_proposals/measurement_correspondence_review_20261104.md)
is ready. The maintainer will review it, explicitly deferred for now. The
[new #188 prerequisite](pending_bugs/bioactivity_target_scope.md) implements opt-in
target-scope @2 without changing @1/defaults or source data: declared copies cannot
supply direct-only scope over an indirect or unresolved original. Scientific,
default and consumer adoption remain pending. Do not block independent B3 work
on reviewer availability, and do not build B4 summaries as accepted science yet.

## Execution order

The block table is the current scheduling entry point. The
[broad exploration inventory](pending_proposals/card_exploration_completion_0150.md)
continues to own panel completeness, and the audit owns its findings and evidence
requirements. Detailed historical chronologies do not override this proposed order.

| Block | Work and owner | Dependency and exit evidence |
| --- | --- | --- |
| B0 — Reconcile and preserve | Sabueso #112/#167/#148: inspect exact-source remote verification, protect original evidence and close the small existing component-preview continuation | First; explain the verifier failure from actual logs, verify applicable CI/governance through gh-run-receptor, and record the result for its actual SHA. Compare public previews, run missing docs checks, then commit/qualify that continuation separately from scientific fixes. If it reveals larger work, retain it and advance B1 rather than delaying correctness |
| B1 — Correct activity interpretation | Sabueso #184/#185, cross-linked to #112 and historical #37 | Opt-in source qualified; current default/ligand/table and @15 packet adoption implemented with explicit original replay. Complete its exact-source receiving and independent scientific/consumer review. Preserve source data and genuine saved results; broad activity panels remain B4 work |
| B2 — Make measurement correspondence scientifically explicit | Sabueso #186, cross-linked to #66/#112 | After B1's semantics are defined; distinguish explicit copies, supported correspondence, conflicting assay/construct context and missing context. Adopt a named policy with scientist-reviewed examples and count/vote consequences before claiming improved grouping or building summary panels on it |
| B3 — Finish bounded structural journeys | Sabueso #173/#148 and applicable integrity owners | Resume remaining region/site/model/instance/assembly transitions from the existing implementation. State precisely what #173 resolves, what source context remains unknown and which physical calculations belong elsewhere. Qualify coherent native/human/agent/saved routes and independent structural examples; source declaration counts never become unsupported physical claims |
| B4 — Deliver the activity and literature journey | Sabueso #148/#112, with literature owners | Builds on B1/B2: protein → molecule → group → measurement → assay/document → original support. Add shared literature views and molecule target/activity context with exact identity joins. Review measured versus derived results, assay comparability, conflicts and missing methods; no unsupported mechanistic interpretation |
| B5 — Complete molecule, clinical and disease profiles | Sabueso #148 and relevant clinical/identity owners | Reuse existing readers for chemical identity/properties/classes, indications/trials and disease terminology/hierarchy/associations. Distinguish clinical citation from outcome, hierarchy from identity, and prediction from measurement; positive and uncertain public examples plus exact saved/agent access |
| B6 — Complete variants and comparative/association profiles | Sabueso #148 and relevant tissue/comparison owners | Reuse existing variant/isoform/tissue/comparison readers with explicit supplied Card context, genomic/reference scope and support. Include biological associations without inventing causality. Qualify missing/foreign/conflicting mappings and historical scope; comparisons never merge entities by similarity |
| B7 — Accept the combined wow experience and consumer usefulness | Sabueso #148/#112; actual consumers own their receiving | Review the entire panel inventory and audit coverage map, integrate the journeys reviewed throughout B0–B6, perform independent scientific and uncoached researcher tasks, correct experience failures and record human acceptance. Qualify compact agent parity and representative whole-session costs, revisit private vertical pilots, and disposition consequential integrity gaps and unresolved external decisions |
| B8 — Consolidate 0.15.0 | Sabueso release owners and #112; assign the release's own tracking issue at candidate preparation | Only after accepted broad exploration, scientific/usefulness and resource gates, and maintainer resumption of consolidation. Select the final candidate, run exact-source CI/governance and staged installed-artifact gates, freeze only unpublished schema as prescribed, then follow the existing release/promotion/clean-install/archive route |

B0 is an administrative and small-change closeout, not a new optimization project.
It must not postpone B1 for unrelated queue latency. B1 and B2 are bounded
correctness work; a comprehensive audit is not a prerequisite to fixing their
known problems. For B2, missing original methods may prevent a positive comparison;
explicit uncertainty and conservative behavior can still be implemented and tested.

Reconcile the existing #180/#181 integrity receipts and the remaining #182
stored-glossary/versioning/pin prerequisite when reviewing affected input routes.
Do not relabel already qualified corrections as new bugs or adopt a stricter
prototype without its original-data compatibility gate. Any still-reproduced
integrity defect enters the first block that depends on that path.

The [B3 scope review](pending_proposals/structural_journey_acceptance_20261104.md)
now records that pre-implementation acceptance matrix, four actual public
source/native/human/agent/saved journeys and six synthetic counterexamples.
The owner must disposition the undefined "full physical reconciliation" task;
this review does not silently remove it from the broad inventory or close B3.
Independent model/fragment/region work can proceed from its existing original
axis/admission contracts while that decision is pending.

For B3, define source-supported acceptance before further coding. If an additional
physical reconstruction requires unavailable context or a modeling consumer,
record that boundary and obtain the relevant owner decision; do not repeatedly
extend navigation while leaving the scientific question undefined. A prerequisite
in the accepted broad inventory cannot be silently deferred to declare completion.

## Work carried through every block

These are continuing responsibilities within the sequence, not concurrent heavy
test processes or independent open-ended projects.

### Scientific review and impact

Start the benchmark before changing B1, with independent expected outcomes for the
known counterexamples. Extend it as B2–B6 introduce scientific questions. Follow the
[audit protocol](GLOBAL_AUDIT_20261104.md#method-and-evidence-requirements-for-the-next-audit-pass):
question, exact original input, source/rule versions, supported interpretation,
counterexample, scope, reviewer state and reproduction evidence.

Review first the rules and mappings that feed a delivered answer: identity,
quantities/qualifiers, assay correspondence, structure/numbering, variant/tissue,
clinical/disease and literature support. Pair each positive case with applicable
conflicting, partial, unasked, failed or non-applicable cases. Public TcTIM/HsTIM,
HK2, small-molecule and disease examples complement synthetic adversarial probes.
No benchmark author should simply copy current output as scientific truth.

When a change affects an existing rule, compare original and proposed interpretations
on the same frozen public inputs. Report eligible-record denominators, changed
answers and propagation to actual consumers. Missing primary protocols stay
explicit; scientist review is recorded as pending until a reviewer actually responds.
An unavailable reviewer must not prevent unrelated technical work from progressing,
but it prevents claiming scientific acceptance for the dependent capability.
Define task success, permitted scientific conclusions, assistance reporting and
resource targets before evaluating each benchmark candidate. Record actual results
against those criteria; no universal response-time or satisfaction score is assumed.

### Coherent public API and manageable implementation

For each question, trace one captured scientific answer through its explanation,
human view, compact agent selection, source navigation and original saved reading.
Share current adapters where their semantics agree. Preserve distinct nature-specific
language and scientific requirements. Literal access remains available to all retained
information, including unsupported natures, without being counted as a rich panel.

Use concrete inconsistencies and repeated coordinated edits to select small
refactors. Preserve public argument checks, diagnostics, optional dependency
boundaries and frozen verifiers. Avoid a whole-library rewrite or a new generic
framework before existing journeys demonstrate its need. Review menus, defaults,
empty/error recovery, uncertainty wording and return navigation throughout, then
test their combined behavior in B7.

### Resource safety and responsiveness

Continue #167 from representative whole-session measurements rather than another
codec experiment by default. Separate acquisition, capture, science, preview,
compact selection, save and fresh-process read; include retained history.
Address #174's source-response boundary with visible budgets, explicit completeness
and deliberate override. Check encoded/decoded buffering and resource lifetime;
do not infer memory bounds from compressed size or a ten-row preview.

Select checks through [TESTS](TESTS.md). Use the shared editable Python 3.14
environment and pytest-receptor; inspect CI through gh-run-receptor. Under current
resource conditions run heavy gates serially with the retained guards (owned group
RSS at most 1 GiB, host MemAvailable at least 4 GiB, zero owned swap and at most
2 GiB phase scratch). Reassess guards for an explicitly justified larger task;
the earlier use of twelve cores is not a standing instruction to start twelve
memory-heavy workers. Do not provision an extra development environment merely
for isolation; installed-artifact environments are used when qualification needs them.

Maintain owned evidence with its issue and review trigger. Remove disposable
scratch after its last use while preserving active sessions, original capsules,
caller outputs and necessary failure evidence.

### Reporting and publication checkpoints

The A1/A2 bugs and A3 proposal are delivered as #184/#185/#186, with synthetic
reproductions, clear unmeasured prevalence and cross-links. Update them with actual
implementation evidence and reuse existing issues for already owned gaps.
Report additional actionable findings at their owning component.
Protect private material and keep shared contracts in MOLI. Do not turn every
checklist item into a separate issue when a coherent owning issue already exists.

Finish coherent blocks with selected checks and reviewable commits. Previously
authorized intermediate main pushes may use the repository's tested-code batching
policy; record any deferred SHA/scope/owner/recovery route. Complete each code
checkpoint with its applicable exact-source CI/governance. Packaging, dependency,
migration and integration gates retain their immediate requirements. Update public
receipts only after checking actual evidence; an older green run does not qualify
new bytes. Review and intentionally restart any paused automation before allowing
it to edit public comments.

## Vertical pilots and cross-component coordination

Revisit the public benchmark first, then perform a read-only inventory of the
private pilots and retained original results at the relevant question checkpoints:
after B1/B2 for activity semantics, after B3 for structure scope, and in B7 for the
integrated platform use. Compare original results under their original rules with
any explicitly new interpretation; do not rewrite pilot checkouts or conclusions.

Use existing authorization only within its actual provider/payload limits. Saved
reading does not authorize new acquisition, and old approval does not authorize
additional providers or molecular identifiers. Prepare a bounded acquisition scope
only if original retained inputs cannot answer a necessary question. Keep all
pilot artifacts, findings and unpublished aggregates private; public reports describe
generic component behavior or use independently public fixtures.

Nextia owns Evidence and discovery interpretation. MOLI owns platform recording
and shared contracts; the existing Recorda receiving PR and consumer acceptance
must be rechecked for their actual current state. MolSysSuite owns modeling and
geometric work. A ready producer does not establish a consumer's accepted use.
External review/access blocks only the dependent task, while independent work in
the sequence continues. Retain a named owner and next review trigger for each wait.

## Completion ledger and release boundary

After each block, update this plan's starting state, CHECKPOINT, the broad panel
inventory, owning issues and relevant risks/decisions in the same coherent change.
Keep one status per deliverable: pending, implemented, locally checked,
source-qualified, scientist/researcher accepted, installed-qualified or released;
record separate statuses where those dimensions differ. Do not add overlapping
test counts or reuse a previous checkpoint for later changed code.

| Acceptance dimension | Evidence required before claiming the relevant work complete |
| --- | --- |
| Scientific integrity | A1/A2 corrected and qualified, A3 policy explicit, consequential findings dispositioned, assumptions/uncertainty visible and source support preserved |
| Broad Card design | Every required row in the accepted inventory has its nature-specific scientific route and applicable human/agent/navigation/saved coverage |
| Required wow experience | The criteria above are demonstrated across public nature-specific journeys; observed researcher feedback and fixes establish explicit human acceptance under #148 before B8 |
| Human and agent usefulness | Independent scientific question review, uncoached researcher task results and agent completeness/cost evidence; unresolved dependent acceptance remains visible |
| Workload and robustness | Representative input/history sizes, declared resource/latency scope, visible refusal/override, malformed-input checks and cleanup evidence |
| Integration | Retained pilot review privately recorded, actual consumer receiving or explicitly owned external limitations, no project conclusions imported as Knowledge |
| Delivery | Final candidate CI/governance, required installed OS/Python/dependency closure and the staged publication evidence; earlier code receipts remain separate |

The audit's fifteen areas remain a coverage map. Close risk-prioritized gaps that
affect this release's behavior, qualify the scope examined and retain the rest as
owned follow-up. No exhaustive scientific or security certification is promised.

Keep separately scheduled: [Deck navigation #153](https://github.com/uibcdf/sabueso/issues/153),
[document export/interactive viewer #154](https://github.com/uibcdf/sabueso/issues/154),
[video presentation #155](https://github.com/uibcdf/sabueso/issues/155), peptide
scientific expansion, broader literature extraction, deferred provider adoption
and local mirrors. The [Swiss-Prot coverage audit #164](https://github.com/uibcdf/sabueso/issues/164)
remains a source-utilization review; take an immediately relevant integrity fix
into the owning block, without making unrestricted source expansion its prerequisite.
These directions remain useful, but they do not silently enlarge the accepted
0.15.0 scope. Revisit their priority after the current scientific and human-access
milestones, or when a concrete dependency makes one necessary.

## Immediate next work session

1. Inspect the latest source/editable and exact-source remote receipts; qualify the
   accumulated B0/B1 code checkpoint without reclassifying earlier failed runs.
2. Verify B1's current default/consumer adoption with its own original controls and
   hosted receipt; retain independent scientific/researcher review as pending.
3. Continue #186 measurement correspondence, then B3–B6 with ongoing scientific,
   experience and workload review. The remaining broad panels stay required.
4. Obtain actual B7 scientist/researcher and consumer acceptance before deciding
   when release consolidation can resume.
