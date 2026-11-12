---
summary: Close the conceptual and functional 0.15.0 scope before further publication-process refinement.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-12
verification: documentation_review
area: [planning, exploration, scientific-integrity]
---

# Functional closeout of 0.15.0

Owner: Sabueso #148, coordinated under #112. This is the immediate work plan.
The [broad inventory](card_exploration_completion_0150.md) defines the required
features; [CHECKPOINT](../CHECKPOINT.md) owns actual implementation and validation.

## Maintainer priority

On 2026-11-12 the maintainer prioritizes the conceptual objectives of 0.15.0 and
continued implementation after that milestone. Further polishing of publication
automation should not dominate the development schedule. The maintainer is willing
to publish a `0.15.0` tag when appropriate; this review has not selected its source
or created a tag. Expected limited public use is context for prioritization, not
evidence of correctness or completed qualification.

The working assessment is that the principal feature families exist. This is not
a completed row-by-row functional audit or acceptance of every journey. Finish a
bounded closeout instead of restarting a broad implementation program or treating
every open validation/publication record as a missing conceptual capability.

## Objectives to close

| Objective | Recorded implementation | Closeout question |
| --- | --- | --- |
| Traceable Knowledge | SourceAssertions, exact support, quantities, explicit conflicts/unknowns and named versioned derivations | Does each selected answer preserve its source, scope and scientific meaning? |
| Protein exploration | Sequence/annotations, structures/models, sites/ligands/assemblies, variants/isoforms and comparative/association profiles | Are the required questions and transitions reachable through the public exploration API? |
| Molecule exploration | Chemical identity/properties/classes, target/activity context, literature, indications and clinical records | Can the user inspect the original record, units, qualifiers and supported context without unsupported efficacy or comparability claims? |
| Disease exploration | Definition/terminology, hierarchy and retained associations | Do hierarchy, identity, association and missing supplied context remain distinguishable? |
| Human and agent access | Readable exploration and typed compact access over shared captured results | Do equivalent requests retain the same values, uncertainty, units and support? |
| Context and complete inspection | Source/detail/back navigation and literal access beyond dedicated panels | Can the user follow a supported cross-topic journey and inspect retained content without losing its exact origin? |
| Portable saved reading | Independent original readers, finite retained requests and historical presentation | Can a separate reader recover the observed answer and context without current acquisition or scientific execution? |
| Bounded MolSysMT integration | The accepted positive/uncertain structural gate has 28 passing destination cases | Are its finite guarantees and unresolved physical context stated accurately? General physical-copy reconciliation is outside this agreed gate. |

The [completed 21-row implementation reconciliation](functional_inventory_review_0150.md)
now identifies the actual public routes, owning tests, source-bound receipts and
concrete limitations. It finds no new feature-sized missing family; it does not
claim independent scientific/usefulness acceptance or a completed candidate gate.

The maintainer explicitly [defers #192 for 0.15.0](../DECISIONS.md#defer-grouped-ligand-investigation-flag-correction-for-0150-2026-11-12)
with a visible limitation, rather than adopting a new aggregation rule. The bug
remains unfixed and must be reconsidered before a later release.

## Execution and exit conditions

1. **Reconcile the functional inventory.** Give every 0.15.0 requirement a concrete
   disposition: implemented with an inspectable route and evidence, an actual
   missing behavior with a reproduction and owner, or an explicitly accepted
   deferral. Replace generic remaining-work phrases with named cases. An older
   paragraph saying a feature was initially missing must be read with its later
   delivery. Do not silently defer a genuine requirement to declare completion.
2. **Close the essential journeys.** Reuse the public protein/structural, molecule/
   activity/clinical and disease examples and existing observations. Check opening,
   question, source/detail, supported transition, return, uncertain/empty recovery,
   agent parity and independent saved reading. Run additional checks for a missing
   demonstration or changed behavior; do not repeat unrelated full suites merely
   to increase test totals. Record exact remaining failures and limitations.
3. **Disposition consequential correctness defects.** The maintainer has deferred
   #192 explicitly for 0.15.0, including its public site/explanation observations.
   Preserve that limitation and its next-release review rather than implementing
   the discussed policy without adoption. The reproduced
   [order-dependent ligand flag](../pending_bugs/ligand_investigation_flag_ordering.md)
   (#192) retains its owner. State the aggregation meaning before a later change
   and preserve genuine historical readings. Review #182's typed glossary/pin concern at the affected
   boundary; its existence is not an automatic instruction to adopt the rejected
   stricter prototype. Fix a required defect or record an explicit owner decision
   and visible limitation; an open issue alone does not establish an accepted deferral.
4. **Write the functional closure record.** Summarize delivered objectives, exact
   outstanding behavior, remaining scientific/agent/workload/consumer acceptance
   and the maintainer's disposition. Keep the independent researcher trial after
   0.15.0 with its actual `not_reviewed` status. No tests or developer-agent
   observations stand in for unperformed human or consumer review.
5. **Prepare the milestone decision, then continue development.** Once the record
   supports conceptual closure, identify the exact proposed `0.15.0` source/tag and
   its limits for maintainer review. Inspect tag-triggered automation and applicable
   source/schema/governance requirements before any push. Keep a code milestone,
   package publication and verified public installation distinct in that record.
   Any changed release prerequisite needs its own explicit disposition; this plan
   neither marks missing gates as passing nor creates an exemption by renaming a release.

## Current execution result

Steps 1–3 now have a concrete [21-row implementation record](functional_inventory_review_0150.md)
and [technical receiving receipt](../evidence/functional_closeout_checkpoint_20261112.json):
821 distinct selected cases pass in two disjoint gates, including all 28 bounded
MolSysMT controls. The existing three public walkthroughs and seven saved readings
retain their own observations and match the unchanged production/runtime maps;
they are not counted as new executions. The maintainer accepts #192 as an explicit
0.15.0 limitation. #182 remains a separate malformed-inner-input/versioning concern;
the current opaque-parent and structural-refusal tests pass without adopting its
stricter prototype. No new feature-sized missing family is identified.

Step 4 is complete: the maintainer [accepts the functional milestone](../evidence/functional_milestone_acceptance_20261112.json)
at reviewed source `9af49bc`, with its explicit #192 limitation. This does not
invent remaining scientific, actual-agent, workload or consumer acceptance.
Step 5 has a read-only automation check: the existing workflows do not
build packages on tag push, while a GitHub Release event can trigger the package
route. No tag source is selected, no release is created and no route is changed.
Missing source/candidate gates or prerequisite decisions keep their real status;
the earlier stopped 288/253-case attempts remain incomplete.

## Separate follow-up

The existing [delivery worksheet](../../devtools/conda-build/release_readiness_0.15.0.md)
continues to own exact candidate CI/governance, schema freezing, installed-platform
and public dependency qualification, package delivery, public-install verification,
archive and release notices. Preserve those obligations and their actual states;
work on them when required for the selected delivery action. Avoid unrelated
publication-process refinement while this functional closeout is unfinished.

The [long-term stages](../ROADMAP.md#accepted-long-term-execution-stages) retain
semantic/temporal access expansion, broader real interoperability, scientific/source
coverage and separately scoped Deck/viewer/export/CLI work. They do not become new
0.15.0 prerequisites. B2 scientific/default review remains explicitly deferred.

The functional closeout records its selected test executions and the maintainer's
bounded acceptance. No online acquisition, private pilot, hosted workflow, schema
freeze, candidate build, tag or publication is performed by this work. Tag/delivery
actions and continuation of authorized development retain their separate scope.
