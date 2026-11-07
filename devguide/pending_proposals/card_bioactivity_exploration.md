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

## Delivery and acceptance

The initial implementation is live only. Human and machine saving refuse
explicitly; raw Card export remains available. Independent original reading needs
its own versioned binder and genuine live-adapter capture made before its reader
is implemented. Existing saved formats and frozen scientific meanings stay fixed.

`test_card_bioactivity_exploration_offline.py` covers complete public input and
separately labelled synthetic uncertainty/copy/indirect controls. Both installed
receiving routes copy and select it. Technical results belong to the exact source
[receipt](../evidence/bioactivity_live_checkpoint_20261106.json): 1,023 distinct
selected cases pass, including all 40 owning cases and original historical
reading, plus a separate repeat of the 40 owning cases from a copied public
payload outside the checkout. This is local editable receiving, not installed
artifact or complete-suite qualification. Full B4, independent scientist
and uncoached researcher acceptance, representative saved workloads, other shared
literature profiles and broader molecule/clinical/disease routes remain open.
No release, schema freezing or publication is authorized by this slice.
