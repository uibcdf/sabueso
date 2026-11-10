---
summary: Prepare combined public B6 tasks without substituting technical success for researcher acceptance.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-10
area: [human-exploration, comparative-context, acceptance]
---

# Combined protein-context review

The development [walkthrough](../../examples/user_journeys/protein_context_review.py)
joins seven existing B6 routes in two ordinary saved sessions. TcTIM P52270 and
the explicitly supplied Q4DV43 capture provide comparative records, equal-position
sequence differences and native `card_knowledge_diff@2` knowledge differences.
HsTIM P60174 provides its own population-variant, isoform/tissue, sequence-change
and biological-association context. Inputs are frozen public fixtures with their
source notices in [NOTICE](../../temp_data/NOTICE.md). No new scientific rule,
source acquisition route, identity join or saved format is introduced.

## Technical preparation

Run from the checkout with the qualified development environment and a new empty
output directory:

```bash
python examples/user_journeys/protein_context_review.py produce --fixtures temp_data --output /tmp/sabueso-protein-context-review
python examples/user_journeys/protein_context_review.py read --output /tmp/sabueso-protein-context-review
```

Keep the complete output directory. `comparisons.json.gz` and
`human_context.json.gz` retain original exploration sessions; `review.json`
records their digests and the observed requests. The reader needs no fixtures.
For every route it checks the complete paginated agent membership, every human/
agent cell value/state/reason, source support, original native payload,
one original source and its return selection. An unmatched display filter returns
to its origin. The receipt detects a changed recorded observation; the independent
exploration verifier owns scientific saved-reading validation. Neither authenticates
provider content or establishes scientific acceptance.

The rendered saved view identifies its saved mode; that notice differs from the
LIVE presentation. Agent cells and original support are compared after following
declared locations, while saved-mode metadata and transport handles may differ.
Exact original agent projection order is retained explicitly,
since requesting the same columns in another order is a different finite request.

The regression copies the script and uses separate processes. The complete
copied-client receiving gate also places pytest scratch and those processes
outside checkout, with byte/import/metadata placement proofs.
Its subprocess wire is explicitly UTF-8, with an inherited CP1252 I/O control;
this portability check does not qualify the native Windows platform.
Reading forbids acquisition, Card construction, current native comparison/state/
tissue functions and current materializers. Prior originals and their historical
meanings remain fixed. Technical preparation does not complete B6, B7 or any
candidate/hosted/installed-platform gate.

## Researcher tasks

Record the researcher's Python familiarity and whether they have already seen
the scripted demonstration. A demonstration is useful training; a trained run
must not be recorded as uncoached acceptance. For an uncoached session, prepare
the public inputs before the participant begins, then give only these tasks and
the normal public API help. Record assistance rather than silently supplying it.

1. Identify each supplied protein and its captured source scope. Find a question
   that compares TcTIM with the supplied Q4DV43 capture. Explain what a retained
   cluster record states and what it cannot establish about those two inputs.
2. Inspect sequence differences and their original sequence sources. Explain
   whether equal integer positions establish biological correspondence.
3. Compare the retained active-site annotations. Explain the result when no
   residue map is supplied, and find the complete source annotations on both
   sides. Do not invent a map or treat unavailable comparison as equality.
4. In HsTIM's own context, inspect a population variant and an isoform's tissue
   usage. Explain the retained assembly/transcript/CDS scope and distinguish
   missing usage, a stated zero and a threshold classification where present.
   Record an unavailable requested distinction explicitly.
5. Find a source-stated interaction or disease/pathway association, inspect its
   original direction and qualifiers, and return to the same selection. Explain
   why the relationship alone does not establish causality or identity.
6. Recover from an empty display filter. Save the observed work and reopen it in
   a separate process. Recover a visited source and an exact agent request;
   distinguish an unexecuted `not_saved` request from source absence.

For interactive preparation from the checkout, the example exposes
`load_public_cards(Path("temp_data"))`, returning `(subject, strain, human)`.
Call `subject.explore(related_cards=[strain])` and `human.explore()` separately.
The helper explicitly reads fixtures before exploration. The scripts above also
exercise the existing human and agent API without requiring a notebook extension.

## Acceptance record and next action

The [local checkpoint receipt](../evidence/protein_context_review_checkpoint_20261110.json)
records 852 distinct selected source cases and 22 copied receiving cases, with
the earlier failing/stopped scope kept separate. It also owns the original
catalog/navigation regressions and preservation limits. These technical results
do not replace the participant record below.

The maintainer/scientist owns review under #148. Record one entry per task with:
participant role and familiarity; runtime/source checkpoint and original bundle
digest; attempted question/options; observed interpretation; source/return path;
assistance; friction/error; and outcome (`accepted`, `revision_needed` or
`not_attempted`). Keep timings descriptive and report the workload and machine.
Protect private or identifying observations through the human handoff route.

Scientific interpretation, uncoached researcher usability, agent task success,
representative workload and actual MOLI-consumer acceptance remain separate.
Failures become concrete implementation work with an owner; no generated score
or passing script supplies missing acceptance. The broader
[profile inventory](card_exploration_completion_0150.md) and
[continuation plan](../CONTINUATION_PLAN_20261104.md#required-wow-experience-in-0150)
retain the remaining molecule/disease/structural and combined-experience work.
