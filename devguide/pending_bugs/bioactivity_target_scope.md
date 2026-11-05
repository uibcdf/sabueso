---
summary: Declared copies can bypass retained original indirect-target exclusions.
issue: uibcdf/sabueso#188
status: open
opened: 2026-11-04
closed:
verification: reproduced
area: [scientific-interpretation, bioactivity, public-api]
blocked_by: []
supersedes: []
---

# Source-bound bioactivity target scope

Owner: [#188](https://github.com/uibcdf/sabueso/issues/188), a B2 prerequisite
for #186/#148/#112. This is a Sabueso selection defect, not a demonstrated provider
error. Scientific/default adoption remains pending. The maintainer will review
the [six-case dossier](../pending_proposals/measurement_correspondence_review_20261104.md)
and explicitly deferred that review on 2026-11-04.

## Reproduction and scope

The retained public HsTIM three-source Card includes two PubChem copies whose
resolved ChEMBL originals are excluded by the direct-only filter: ChEMBL activities
906612 and 1958603 are mapped H, while copies AID214625/SID242581948 and
AID292822/SID103762083 are mapped D. Original measurement grouping and opt-in
measurement @2 both admit those copies. Changing grouping alone does not repair
which source records enter the summary. The exact source fields and supports are
in the [casebook](../evidence/measurement_correspondence_review_cases_20261104.json).
This establishes inconsistent retained selection; it does not establish the
experimental target from the accession, molecule name or article title.

## Opt-in correction

`target_scope_rule="bioactivity_target_scope@2"` is a separate, named selection
interpretation shared by `bioactivities`, `explain_bioactivity`, `ligands`,
`explain_ligand`, `compare_ligands` and their flat tables. Default and explicit
`bioactivity_target_scope@1` preserve original behavior and shapes. Classification
and measurement policies are independent selectors.

For the direct-only answer, @2 requires an explicit focal protein reference and
exact subject agreement. A non-copy needs mapped assignment D. A declared copy
needs a unique non-copy original, resolved only through measurement @2's declared
copy edges, with the same focal subject, mapped D and no different stated copy
assignment. Numeric/publication candidates never supply an original or target
scope. Missing, ambiguous or cyclic originals, unstated assignments and different
subjects remain unconfirmed or disagreements, with readable reasons. D is retained
source/mapping context, not independent experimental validation of direct binding.

`include_indirect=True` deliberately includes every retained record and preserves
these diagnostics. No new acquisition occurs. Each decision links the original
record and its original(s) to their SourceAssertions; raw D/H fields, measurements,
units and Card pins are untouched. A known molecule excluded from the new scope
has explanation status `outside_scope`, rather than `not_on_card`, and retains
its excluded source support. New activity explanation @4 and ligand explanation
@5 name this scope. Original packet mappings, including @15, explicitly keep @1;
this slice adds no rich explorer panel or saved-scientific adapter.

## Same-input comparison and receiving

Four retained public Cards are compared under both measurement policies. Eight
genuine ca9e0f3 views were captured before the change. Default and explicit @1
outputs preserve those controls; only formal producer stamps may change on fresh
recomputation under a later SDK, while original stored reading remains exact.
The two original example Cards retain their admitted populations. The three-source
TcTIM Card changes from 1,002 to 995 admitted records (seven unresolved originals).
The three-source HsTIM Card changes from 88 to 77 (eight assignment disagreements,
three unresolved originals); eight original H exclusions also remain. Widening
returns all 1,002 and 96 retained records respectively. These finite-corpus counts
are not a provider-wide prevalence estimate or independent scientific acceptance.

The [local receipt](../evidence/bioactivity_target_scope_20261104.json) records
actual gates, resource observations and original controls. Standalone adversarial
cases cover both measurement policies, assignments/subjects, missing/ambiguous/
cyclic originals, chains, defaults, explanations, ligand comparisons, tables and
invalid arguments. CI and staged installed scopes both copy/select that module;
isolated receiving uses the shared editable checkout, while actual installed
artifact qualification belongs to the hosted lanes. Exact-source receiving and
independent scientific/consumer acceptance remain distinct requirements.

## Hosted technical checkpoint — 2026-11-05 UTC

Accumulated source `c5b8af1` /SDK `0.14.0+167.gc5b8af1` is
[qualified](../evidence/bioactivity_target_scope_checkpoint_20261105.json): CI 18/18,
governance 1/1, nine source lanes each 7,254 cases and four installed lanes each
1,792, with full hashes/CRC/steps and codec receiving. This is technical source
receiving, not independent scientific/default/consumer or researcher acceptance.
The maintainer's scientific review remains deferred; #188 stays open and the
original target-scope default remains unchanged. Later docs add no runtime change.

## Experience review and next step

A researcher can now distinguish a retained excluded result from an absent item,
read why an original/copy disagreement prevents direct-only inclusion, inspect
both source supports and deliberately widen scope. The same structured decisions
serve agents and tables. The observed example calls still require knowing policy
names and dictionary keys; a coherent readable activity explorer and compact
saved agent route remain B4 work. No uncoached researcher task or wow acceptance
has been performed. Review the six cases and target-scope consequences before
any default or consumer adoption; unrelated B3 technical work can continue.
