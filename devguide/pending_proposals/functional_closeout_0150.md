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

These entries summarize existing implementation. Their final disposition must
reference the owning inventory row, example or receipt; this table creates no new
scientific result or global acceptance claim.

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
3. **Disposition consequential correctness defects.** Start with the reproduced
   [order-dependent ligand flag](../pending_bugs/ligand_investigation_flag_ordering.md)
   (#192). State the aggregation meaning before changing it and preserve genuine
   historical readings. Review #182's typed glossary/pin concern at the affected
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

The conceptual closeout is complete when every required capability has a concrete
disposition, essential journeys have adequate evidence, and consequential defects
have an accepted treatment. It is not complete merely because all feature families
have implementations. The exact-source heavy integrations and hosted recovery
remain pending at `9ab6dd7`; the earlier stopped attempts remain incomplete.

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

This documentation change runs no scientific exploration, private pilot, test
suite, hosted workflow, schema freeze, build, tag or publication. It records work
priority and the bounded next steps, not their completion.
