---
summary: Recover original molecule context operations after display filtering and sorting, including resaving.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-12
verification: reproduced
area: [human-exploration, saved-reading, molecule-context]
---

# Original molecule context display and resaving

Actual public developer-agent exploration at `f4850ef` / SDK265 exposes two
current presentation/navigation gaps despite the complete passing offline
baseline. This is an experienced agent with prior implementation and answer
exposure, not an independent researcher or scientist result.

The producer opens a measured molecule's supplied target, its group and original
record, then visits assay, citation and complete publication destinations through
`record.related().filter("role", equals=...).items()[0].open()` before saving.
Two fresh readers recover the original root, source record and unit-bearing
measurement, but those context opens incorrectly return `not_saved`. The actual
filtered node and destination are present in the verified file. New public
regressions reproduce the same refusal for sorted link views.

Generic display clones inherited the unfiltered molecule node. The strict
operation lookup correctly refused that mismatched source instance. Generic saved
molecule context filtering/sorting now reuses the existing `recorded_display`
lookup after validating and evaluating the display request. It accepts only the
exact recorded source and operation. An unexecuted display's source destination
remains `not_saved`; equal labels or endpoint values do not supply another route.

Replaying original scientific views also creates new view instances. An untouched
SDK265 read/resave succeeds, but resaving after that legitimate navigation exposed
missing source-instance explanation/link closure. Saved molecule preparation now
reopens verified original support only for new instances, checking their retained
closure first. Original instances and other saved families are left to their
existing preparation. No scientific topic, source query or missing support is
generated. The original verifier still checks every actual operation edge.

The current activity opening separately claimed saving was unavailable, even
though `capabilities["save"]` was true and the public save succeeded. New sessions
record `molecule_activity_actions@1` and expose their actual saving action. Missing
historical policies become explicit `legacy_molecule_activity_actions@1` before
resaving. Original text/HTML and old producer files stay unchanged; current
capabilities remain separately inspectable. Explicit unknown policies are refused.

The [receiving receipt](../evidence/molecule_context_display_checkpoint_20261112.json)
records 455 distinct selected source cases and the overlapping complete 71-case
copied LIVE child, with exact source and current/historical presentation checks.
Actual SDK265 replay/resave preserves original text/HTML; explicit `start_new()`
checks the current action separately. Fresh 11,519-case discovery is collection
only; the earlier complete 11,514-case baseline precedes this correction. New regression readers run in fresh processes outside checkout, with Card
construction, acquisition, current materialization and derivation forbidden. They
check all three visited contexts, exact back routes, resaving and an unexecuted
operation's refusal. Genuine SDK265 bytes and its original text/HTML hashes are
retained separately from new current sessions. Original SDK205/208/218 controls
keep their independent expectations. No Card schema, scientific adapter/rule or
original verifier is changed. The separate grouped investigation-flag limitation
remains tracked under #192.

Raw observations, complete red/green streams, the explicit baseline test-helper
exception and subsequent source epochs are retained under #148/#112 in
`recovered_work/checkpoint_recovery_20261106/b7-current-full-checkpoint-4/` and
`b7-context-display-correction-1/`, for B7/candidate review. No new issue comment
has been published. Exact-final-head hosted/installed qualification and remaining
B7 acceptance retain their scope; the independent trial remains explicitly
deferred until after 0.15.0. B8 is not resumed by this correction.
