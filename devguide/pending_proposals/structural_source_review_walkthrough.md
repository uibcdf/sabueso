---
summary: Review original annotation, chain, ligand/contact and assembly context in one public saved journey.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-10
area: [human-exploration, structural-context, acceptance]
---

# Combined structural source review

The development [walkthrough](../../examples/user_journeys/structural_source_review.py)
connects existing experimental-structure routes over public TcTIM P52270 and
1SUX. It starts from the first source-stated active-site annotation, opens its
regional structural question, then inspects original per-chain gaps/numbering,
ligand instances and contacts, assembly generator positions and exact sources.
No new scientific rule, source acquisition route, identity join or saved format
is introduced. The local example receipt checks recorded observations; independent
exploration validation owns saved scientific semantics. Neither authenticates
the provider's claims or supplies independent researcher acceptance.

## Technical preparation

Use the qualified development environment and a new empty output directory:

```bash
python examples/user_journeys/structural_source_review.py produce --fixtures temp_data --output /tmp/sabueso-structural-source-review
python examples/user_journeys/structural_source_review.py read --output /tmp/sabueso-structural-source-review
```

Keep the complete directory: two original `.json.gz` sessions and `review.json`.
The current Card explicitly uses `temp_data/rcsb_nonpolymer_instances/` for the
1SUX RCSB capture, the ordinary UniProt fixture, and their source notices in
[NOTICE](../../temp_data/NOTICE.md). UniProt-linked structures without newly
requested RCSB input remain in the inventory with their stated limits. The older
schema 0.3.9 frozen Card supplies a separate historical annotation-scope control.
It cannot recover original native scope by refreshing during reading.

The current review distinguishes:

- The source annotation at position 96, whose retained coordinate annotations
  cover chains A/B, from the deliberate `[1, 96]` question with a recorded gap.
  Original author numbering remains chain-specific; structure/reference revision
  agreement is not established.
- Two source ligand components, BTS and SO4, with one and seven instances. Every
  original contact collection is inspected through complete finite agent reads.
  Original values, units, ordering and source scope stay intact. No regional
  overlap, biological binding or assembly-contact assignment is inferred.
- Twelve separate assembly declaration positions, including unresolved K/L.
  Matched native keys retain their original basis. Declaration counts do not
  establish unique physical copies; physical membership stays `not_computed`.
- The historical `missing_prerequisite` outcome, source absence, and an empty
  display selection. These are different states with their own return paths.

Human inspection and finite agent reads address the same original literal nodes;
deferred values are opened through their declared locations. The exact assembly
agent request retains all selected cells and original support. Source/back,
component/back and empty-selection recovery are checked before saving and after
independent reading. The reader needs no fixtures or coordinate engine. This
knowledge-only review complements the separate bounded
[1TCD MolSysMT journey](structural_journey_acceptance_20261104.md#accepted-assembly-scope--2026-11-06).
It does not enlarge that calculation's scope or adopt a shared handoff protocol.

## Independent researcher tasks

The [local receipt](../evidence/structural_source_review_checkpoint_20261110.json)
records 132 selected source cases in seven complete modules and four copied
receiving cases, with exact input/placement proofs and separate earlier calibration
limits. Lint, guide/governance, fixture delivery and warning-fatal documentation
checks pass. This is editable local qualification; installed/platform, hosted and
independent scientific/human acceptance remain separate.

Record the participant's structural/Python familiarity, checkpoint and bundle
digests, assistance, attempted question, observed interpretation, source/return
route, friction and outcome (`accepted`, `revision_needed`, `not_attempted`). A
participant shown the scripted solution is trained; record that separately from
uncoached acceptance. Give only the tasks and ordinary public API help for an
uncoached session:

1. Find the active-site annotation and its original source. Explain the sequence
   axis and whether a recorded position alone supplies coordinates.
2. Inspect 1SUX for position 96, then for `[1, 96]`. Find each chain's exact original
   gaps and author numbering. Explain the distinction between declared sequence
   coverage, coordinate annotation and unspecified reference revision agreement.
3. Inspect BTS and SO4 instances and one original contact's units and mapping
   scope. State what that record cannot establish about regional or biological
   binding and physical assembly membership.
4. Inspect the generator's twelve declared positions and the original source.
   Explain K/L and why ten matched native keys do not count unique physical copies.
5. Reopen the historical Card's annotation question. Explain its missing basis
   without turning an unavailable result into zero structures or source absence.
6. Recover from an unmatched filter; save and independently reopen the observed
   work. Recover a source, a component position and a finite agent request with
   their exact original return context.

Scientific interpretation, uncoached usability, actual agent tasks, representative
workload and actual MOLI-consumer acceptance remain separate B7 obligations.
The [broad inventory](card_exploration_completion_0150.md) retains remaining
cross-provider/structural transitions and nature-specific orientation. #148 owns
the experience, #173 the bounded assembly scope and #112 coordination. B2 review
remains deferred; B8/candidate/schema freeze/release remain unresumed.
