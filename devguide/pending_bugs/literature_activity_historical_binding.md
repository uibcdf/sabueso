---
summary: Preserve SDK202 bibliography scalars and explicit cross-Card questions in saved reading.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [exploration, persistence, literature, bioactivity]
blocked_by: []
supersedes: []
---

# SDK202 literature and activity binding counterexamples

Owners: Sabueso #148, bibliography/native behavior #108 and checkpoint #112.
This is an internal handoff, not a published issue update. Inputs are public or
explicit synthetic controls; no original fixture or private material is changed.

## Observed scalar inconsistency

SDK202 source `1145ea3` corrects native literature summaries to retain dictionary
scalar `False`, integer zero and floating zero. Frozen SDK200 activity predicates
keep their original summary behavior. Activity wires include a complete literature
overview, so delegating a new mixed @19 file to @17's activity verifier rejects a
valid current result. The mismatch already occurs in whole-wire verification,
before the publication-context wrapper. Raw assertions and activity classes are
unchanged; no efficacy or experimental-independence conclusion is involved.

A reproduction reduces a separate public TcTIM input to one retained activity
and adds an explicitly synthetic citation control with `{"value": false}`.
LIVE literature returns boolean `False`; mixed saving raises a bioactivity binding
`StorageError`. Local evidence:
`recovered_work/checkpoint_recovery_20261106/b4-literature-audit-3/`
(`probe.py`, `receipt.json`, `audit-resource.json`): 2.77 s, approximately 113 MB
peak owned RSS and zero swap. This is not a clean original producer.

Accepted correction direction: NEW LIVE Bio/Lit saves use explicit SDK202 semantic
format @19 / optional sharing @20. A separately frozen Bio-v2 entry point must
bind complete wires and publication contexts using SDK202 literature, while
reusing unchanged scientific/grouping/selection helpers where appropriate.
Original @17/@18 reading and resaving retain SDK200 v1. Dispatch uses the explicit
format boundary, never payload guesses or producer-version text. Capture the
additional clean SDK202 original before implementing the Bio202 predicate.

## Observed cross-Card question inconsistency

An explicit supplied Card A relationship opens Card B through a generic link,
then `destination.explorer.answer("publications")` starts a new question with
effective options. The originating generic link has no publication request.
The new @19 reader incorrectly requires inherited question continuity and rejects
saving. Both Cards in this reproduction are explicit synthetic controls.

Evidence:
`recovered_work/checkpoint_recovery_20261106/b4-literature-cross-card-audit-5/`
(`probe.py`, `cross-card-receipt.json`, `audit-resource.json`): 2.01 s, 76,009,472
bytes peak owned RSS and zero swap. The correction must distinguish a newly asked
question from inherited publication/source/back navigation, while binding exact
options and focal capture. Add read/resave and resealed-request regressions.

## Qualification and handoff

An additional clean SDK202 control is captured and independently verified:
manifest `ae10189753c6a4cfca0bb4a97dba491ba9ad901d5606686c62930f32ebb83b3e`,
755 members, four typed scalar cases, twelve complete Bio wires and eight
literature wires. It predates the new Bio-v2 predicate, not the initial literature
reader. The frozen v2 facade reproduces every wire and all four publication
wrappers with mutable readers, clients, digesters and profiles blocked. Full
current-source workload receiving is included in the
[9,466-case local checkpoint](../evidence/literature_saved_checkpoint_20261107.json).

The third audit counterexample replaces a focused publication's parent with
another captured Card's catalog sharing the publication reference. The initial
reader accepted the foreign return context. The correction binds exact focal
pin/snapshot and original context for inherited literature navigation while
retaining explicit generic cross-Card entry. Original failed evidence is in
`b4-literature-focus-focal-audit-6/`; bounded corrected rejection and legitimate
cross-Card question receiving are in `b4-literature-binder-focal-1/`. Permanent
end-to-end regressions are included in the final 48-case literature and 22-case
Bio-v2 modules, alongside the global foreign-origin serializer controls.
Issue handoff and hosted/artifact/human qualification remain separate; this
report does not claim that the owning issues have been closed.

Nonblocking diagnostic follow-up for #148/#112: the shared restore path admits
chemical results in @19, but its unsupported-format message still lists only
@15/@17. The observed mismatch concerns error guidance; admission itself includes
@19. Align that text on the next maintained storage change, without editing a
frozen verifier or reopening current scientific policy.

The genuine nine-Card SDK202 literature original remains immutable. These
counterexamples do not replace it or qualify complete saved workloads. Preserve
failed receipts and record corrections separately. Offer an update to #148/#108
at the maintainer checkpoint; publication requires its applicable authorization.
