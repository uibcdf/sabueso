# Protein activity and literature exploration

Owners: [Sabueso #148](https://github.com/uibcdf/sabueso/issues/148) and
[#112](https://github.com/uibcdf/sabueso/issues/112); bibliography/source lineage
also belongs to [#108](https://github.com/uibcdf/sabueso/issues/108).
This is the activity/literature part of B4 in the
[integrated plan](../CONTINUATION_PLAN_20261104.md#destination-review-and-next-actions).

## Live contract

`card.explore().answer("measured_molecules")` and `.view("bioactivities")`
show the same captured native result as `explorer.access.select("bioactivities")`.
An exact request runs the existing native reader once on a detached Card; later
display, support, paging and equal requests reuse the result. Browsing never
queries a scientific provider or changes the original Card.

Open a molecule for its native measurement groups, a group for its original
source activity records, and a record for its unabridged reported qualifiers.
`explain()`, `related()` and `back()` retain the originating selection and exact
source/relationship locations. Assay, citation, grouping, coverage and whole-Card
context are explicit destinations. Opening an exact publication materializes and
caches the existing `explain_literature()` result only when requested.

The public TcTIM case uses `P52270`, molecule `chembl:CHEMBL1161789`, activity
`24815542`, `IC50 = 33000 nM`, assay `CHEMBL5138431`, and document `CHEMBL5137001`.
Its native display name is not retained, so the interface shows the exact ChEMBL
identifier. Benznidazole (`chembl:CHEMBL110`) supplies a single-point percentage
and a missing-value control. Its two selected activity records link to publication
`pubmed:20889239`; that publication's complete context has 459 original activity
links. The publication context is never reduced to the selected molecule.

The complete fixture has 493 activity records. Counts distinguish native groups
from source records; neither establishes independent experiments. Defaults remain
`bioactivity_class@4`, `measurement_identity@1`, `bioactivity_target_scope@1`,
`include_indirect=False`, and the existing threshold policy. Opt-in @2 review
remains deferred and no new classification, grouping or source mapping is added.

Machine projection, exact membership, typed equality and ordering only select
displayed original members. Quantity values retain their PyUnitWizard field and
unit. Measurement comparisons require explicit concentration or percentage units;
membership and nonquantity predicates first establish the candidate subset;
mixed dimensions within that subset refuse comparison. Aggregated or grain-inapplicable scalars
are distinguished from genuinely unknown source values. Scientific uncertainty
persists through filtering, including a valid zero-match subset. An unavailable
result without retained rows refuses display filtering explicitly (#191).

Group explanations retain their complete original membership as native context.
The displayed records are the intersection of that group, the selected molecule
and the selected inclusion policy. Explicit `focus_membership` separates included
records from context-only records, for both group and relationship selectors.
An identifier known for only some aggregate members never fills a missing member.
The original native output and record qualifiers remain unchanged.

An independent implementation review identified these two possible misleading
summaries before the first B4 capture. Deliberate mixed known/missing identifiers
and declared copies across molecule/target-assignment contexts provide their
regression controls. The source/grain observations are code-confirmed; their
effect on an uncoached researcher's understanding remains a human-review question.
These findings and the conjunction-selection clarification belong in the next
reviewable #148 update, not a change to scientific defaults.

## Original support and limits

Original activity and assay SourceAssertions remain inspectable, including
missing references and qualifier conflicts. The ChEMBL mapper retains citation
fields on activity relationships but does not retain a separately asserted
original document object. The interface labels that citation context accurately;
it does not invent a document SourceAssertion, article reading or Nextia Evidence.
Dedicated document-object lineage remains an owning-source follow-up under #108.

Concentration bands are not efficacy, selectivity or mechanistic conclusions.
Single-point inhibition does not establish potency or an inferred test dose.
Unrequested, failed, scoped-empty and incomplete source outcomes remain distinct.
Foreign or ambiguous focal identity refuses unscoped interpretation.

## Independent original saved reading

The historical SDK200 reader and its complete retained public saved journey pass
local technical receiving. Its semantic format
`sabueso.card_exploration@17` uses `bioactivity_exploration_binding@1` to bind
the original captured input, native answer, focused molecule/group/record
membership, quantities, support, human navigation and exact machine request.
The separate physical representation `sabueso.card_exploration@18` uses
`shared_exploration_values@3` and `shared_exploration_values_binding@3` for
logical format @17. Sharing changes storage, never identity, list occurrences or
scientific meaning. Formats @1–@16 and their frozen verifier/codec meanings remain
unchanged; the older shared codecs do not acquire new admitted formats.

Original reading uses immutable SDK200 predicates and an inert captured-input
shim. It does not construct a Card, call current scientific engines, scientific
option digesters or source clients, generate acquisition/attribution, or replace an
original answer with a newly generated one. Expected findings are private
consistency checks against retained knowledge, not a claim of source authenticity
or independent scientific truth. Supported original policies include classes
@3/@4 and measurement/target-scope @1/@2; the live defaults and deferred B2 review
remain unchanged.

Saving retains already executed human and agent requests and their required
support/navigation closure. Reading can return only an exact retained request,
including its scientific options, focus, projection, predicates, membership and
ordering. An unvisited topic, focus or machine request reports `not_saved` rather
than running a current reader. A later explicit new exploration remains separate.
Repeated saving preserves original native producer labels even when the writer's
version is newer. Only declared generated-rule metadata paths supply those labels;
source records with similarly named version fields remain ordinary original data.

### Genuine pre-reader control

The clean source `2eb611463c0f8ab990039ec017833f5b33ae2711`, SDK
`0.14.0+200.g2eb6114`, produced a genuine live-adapter capture on 2026-11-07 UTC
before the independent reader existed. Its manifest SHA-256 is
`509ee7369f5a0cf53d5d40e872db33a19a5f2e075588e677dbfca7010f670ab6`.
The retained original has 157 members totalling 745,483,187 bytes, including all
493 activity records, exact requests, three row grains and the complete 459-link
publication context. It records zero network attempts and source acquisitions.
It is an unsealed live control, not a retrospectively produced saved-format file.

The repository fixture `tests/core/data/bioactivity_live_v1.json.gz` is a documented
projection of that control, not a regeneration. It preserves the original Card,
all nine scientific wires, native outputs, executed requests and selected human
records. The complete original remains unchanged at
`recovered_work/checkpoint_recovery_20261106/b4-live-original-capture/original3/`;
its bounded capture receipt is `capture3-resource.json` in the parent directory.
See the [fixture provenance](../../tests/core/data/README.md#original-live-bioactivity-projection-before-saved-reading)
for exact projection hashes and omissions.

A separate bounded frozen-predicate check verifies all nine original wire/result
identities and both publication wrappers, including their 9 and 459 links, with
Card construction, current native engines and networking forbidden. Its receipt
is `recovered_work/checkpoint_recovery_20261106/b4-frozen-original-gate-1/original-resource.json`.
This finite original-consistency check is separate from the complete local
save/read/resave receiving recorded below.

### Complete-session resource scope

The full public root plus retained machine/source/navigation closure measures
**709,616,078 logical JSON bytes**. The size-only diagnostic is retained in
`recovered_work/checkpoint_recovery_20261106/b4-saved-profile-2/profile.log`,
`phases.jsonl` and `profile-resource.json`. It prepared 2,478 views and 2,212
retained objects and wrote no saved result. Its successful size measurement is
not a save/read gate or a benchmark. The preceding profile-1 attempt exceeded
the explicit 512 MiB logical budget and remains a failed attempt.

Complete-session qualification therefore needs an explicit
`max_logical_bytes=1024**3` (1 GiB), alongside the case's explicit 128 MiB encoded
and decoded transport limits. The **256 MiB default logical limit remains
unchanged**. The expanded logical workload, shared physical storage, transport
bytes and process RSS are different quantities; compression does not waive the
logical-work limit. Default-budget refusal must occur without returning a partial
result. The 1 GiB allowance is a bounded test/workload selection; the successful
complete journey has separate receiving below and leaves the global default fixed.

## SDK202 activity and literature boundary

New LIVE activity or literature saves use semantic @19 and optional sharing @20.
The Bio-v2 reader retains SDK202's typed bibliography scalars throughout the
complete activity wire and on-demand publication context. Old @17/@18 reading
and resaving keep the immutable SDK200 predicates above; dispatch follows the
verified logical format. Scientific classifications, quantity handling and
deferred B2 defaults remain unchanged.

The additional clean SDK202 original was captured before Bio-v2 implementation.
It preserves four explicitly synthetic scalar controls, twelve activity wires
across three grains, eight literature wires and four complete publication
wrappers. All members are retained byte-faithfully in
`tests/core/data/bioactivity_literature_scalars_sdk202.tar.gz`; declarations and
source rights remain in [capsule provenance](../../tests/core/data/README.md).
The 22-case source module passes with mutable readers/clients/profiles blocked,
including mixed/standalone saving, exact original types, inert resaving, resealed
substitution refusal, original @17/derived @18 compatibility and explicit
cross-Card/focal context. Full current-source and copied qualification remain
separate. See the [counterexample handoff](../pending_bugs/literature_activity_historical_binding.md).

## Delivery and acceptance

`test_card_bioactivity_exploration_offline.py` covers complete public input and
separately labelled synthetic uncertainty/copy/indirect controls. Both installed
receiving routes copy and select it. The earlier live technical results belong to
the exact source
[receipt](../evidence/bioactivity_live_checkpoint_20261106.json): 1,023 distinct
selected cases pass, including all 40 owning cases and original historical
reading, plus a separate repeat of the 40 owning cases from a copied public
payload outside the checkout. These earlier receipts cover local editable live
receiving; original saved reading has the separate results below.

`test_card_saved_bioactivity_offline.py` adds the original-control, independent
fresh-process, exact-request, quantity, hostile/resealed substitution, full
publication, transport and repeated-save receiving scope. The final local affected
[receipt](../evidence/bioactivity_saved_checkpoint_20261106.json) records 1,109
distinct passing cases: 881 parallel affected cases, 198 serial historical cases,
all 29 saved-bioactivity cases, and one outer copied consumer. All phases have zero
warnings, skipped cases and owned swap. The copied consumer asserts its child's
29 passes; repeated live/strict/copy cases add no distinct cases to that total.
This is a composed affected checkpoint against the editable workspace.

The full 29-case module passes in 841.07 s (843.70 s supervised), with
2,950,713,344 bytes peak owned-tree RSS, under its one-CPU/4 GiB/1,800 s guard.
The outer copied consumer passes in 840.71 s (841.64 s supervised), with
2,980,777,984 bytes peak owned-tree RSS, under its one-CPU/4 GiB/2,400 s guard.
The fresh read/resave timeout is 600 s and the copied-test timeout is 1,800 s;
these receive the observed approximately 330 s full save and 80 s full read.
The earlier combined live/saved 69-case control also passes in 877.79 s
(880.47 s supervised), with 2,944,389,120 bytes peak owned-tree RSS, under its
original 900 s guard and 240 s fresh-process timeout. Preserve that original
successful control and the earlier failed attempts as their actual outcomes.

Standalone historical efficiency controls retain their original budgets and
remain open. Exact-final-source hosted and installed-artifact qualification,
independent scientist and uncoached researcher acceptance remain separate.

Full B4, other shared literature profiles and broader molecule/clinical/disease
routes remain open.
No release, schema freezing or publication is authorized by this slice.
