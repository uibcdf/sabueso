---
summary: Six exact public cases for independent review of copy scope and activity summary abstention.
issue: uibcdf/sabueso#186
status: open
opened: 2026-11-04
verification: review_prepared_scientist_response_pending
area: [scientific-review, bioactivities, source-scope]
---

# Scientific review: copied activity records and summary meaning

Reviewer response: **pending, deliberately deferred**. On 2026-11-04 the maintainer
accepted responsibility for this scientific review and explicitly left it for
later. Continuation of implementation is not review acceptance or default-adoption
approval. Owner #186/#188, coordination #112/#148. This
worksheet prepares independent scientific review; its author has not accepted the
candidate on a scientist's behalf. The
[continuation plan](../CONTINUATION_PLAN_20261104.md#scientific-review-and-impact)
requires actual review before deliberate default adoption.

Engineering status, received on 2026-11-05: opt-in measurement correspondence @2
and copy-aware target scope @2 are implemented and technically qualified in
`c5b8af1`; see the
[exact-source checkpoint](../evidence/bioactivity_target_scope_checkpoint_20261105.json).
The six cases below retain their original inputs and policy comparison. Passing
software gates does not supply the deliberately deferred scientist response or
authorize adopting either policy as the default.

## Question and retained inputs

Can a researcher interpret these retained records as direct activity on the focal
protein, and what concentration-band summary is justified? Keep this distinct
from whether several database records represent independent experiments.

The six cases are the complete set of changed molecule summary classes in the
four-input comparison of `measurement_identity@1` and opt-in
`measurement_identity@2`, using `bioactivity_class@4`. They are selected because
the policy changes their answer, not as a representative or unbiased source sample.
Two original retained public Cards and two three-source public fixture rebuilds
are compared at the same exact input pins; original values, units, qualifiers and
individual record classes remain unchanged.

Complete original quantities, source records, declared pointers, assay/document
context, actual group/voter decisions and pinned SourceAssertion references are in
[the casebook](../evidence/measurement_correspondence_review_cases_20261104.json).
Input Card hashes and source provenance are retained in
[the candidate receipt](../evidence/measurement_correspondence_candidate_20261104.json).
The exact four input Cards remain owned under #186 for this review. All data come
from the existing [public fixture set](../../temp_data/NOTICE.md); no source was
queried, no primary protocol was newly reviewed and no private pilot was read.

## Six cases to inspect

All six included records are PubChem BioAssay copies. Their comparison relation is
not stated in the mapped record; the scalar and depositor outcome remain separate.
The existing individual concentration-band policy reads an unqualified scalar as
a point. The candidate's molecule summary instead abstains when its included group
has no non-copy original voter. These are different interpretation levels.

| Case | Focal input / displayed molecule | Retained copy measurement | Original → candidate summary | Original scope on this Card |
| --- | --- | --- | --- | --- |
| 1 | TcTIM / PubChem CID168270788 | IC50 11 µM; relation unstated; AID1882558 /SID482049346 | weak → inconclusive | Declared ChEMBL assay CHEMBL5138433 exists, but no original molecule row is resolved for this copy |
| 2 | HsTIM / CHEMBL3142429 | Ki 15 µM; relation unstated; AID214625 /SID242581948 | weak → inconclusive | Original ChEMBL activity 906612 is present but excluded as H; the copy is mapped D and included |
| 3 | HsTIM / PubChem CID129627013 | IC50 100 µM; relation unstated; AID1803397 /SID341104385; depositor outcome Inactive | weak → inconclusive | Declared BindingDB assay BindingDB_8411_1 is not resolved on the Card |
| 4 | HsTIM / PubChem CID137241593 | IC50 100 µM; relation unstated; AID1803397 /SID341104384; depositor outcome Inactive | weak → inconclusive | Same unresolved declared assay scope as case 3; original record identity is not established |
| 5 | HsTIM / PubChem CID73187903 | IC50 100 µM; relation unstated; AID1803397 /SID341104383; depositor outcome Inactive | weak → inconclusive | Same unresolved declared assay scope as case 3; original record identity is not established |
| 6 | HsTIM / CHEMBL1161997 | Ki 1000 µM; relation unstated; AID292822 /SID103762083 | inactive → inconclusive | Original ChEMBL activity 1958603 is present but excluded as H; the copy is mapped D and included |

H/D here are the retained/mapped target-assignment codes used by Sabueso's current
filter. This worksheet does not infer experimental target identity from an article
title, an accession match, a scalar or a database name.

## Consequential finding: direct-only selection needs correction

Cases 2 and 6 reproduce the original/default target-scope limitation in
[#188](https://github.com/uibcdf/sabueso/issues/188). With `include_indirect=False`,
original H records are excluded while their declared copies bypass that exclusion
through the PubChem mapping's D value. Grouping policy changes alone do not
correct which records enter the answer. The technically qualified opt-in
target-scope @2 now requires the resolved original's scope and exposes unresolved
or disagreeing context; original @1/default behavior remains reproducible.
Scientific/default adoption and acceptance of rich summaries remain pending.

Case 2's original states Ki = 15000 nM, while its copy states 15 µM without the
relation. Case 6's original states Ki > 1000000 nM and records rabbit assay context;
its copy states 1000 µM without the relation. These are retained source facts,
not a newly established experimental or clinical conclusion. The full records and
exact original support remain inspectable. Source disagreements must be shown,
not silently assigned a winner.

The other four cases do not establish that the original is absent from its
external database. A source's local assay identifier may be unavailable in a
retained mapping; the molecule selector may remain unresolved. These are distinct
from a source failing, never being asked or explicitly stating no measurement.

## Reviewer worksheet

Record your own rationale and cite the retained fields or needed original method;
do not treat a matching output/test as experimental validation.

1. Which cases justify a statement about direct activity on the focal protein?
   What original target/organism/construct context is missing or conflicting?
2. For a copied scalar without its relation, what may the concentration band mean?
   Should it be a clearly qualified record-level band, a supported molecule
   summary, or an uncomputed summary? State the assumptions rather than converting
   a depositor's Inactive outcome into an unstated numeric bound.
3. Distinguish a fully qualified copied measurement from these six inputs. Does
   missing original access alone justify abstaining, or is the actual missing
   qualifier/target context decisive? Keep source reliability and experimental
   independence separate from concentration-band calculation.
4. Do the declared-copy selectors establish the same source result within the
   retained scope? Which unresolved pointers or conflicting contexts require
   further inspection, without merging molecules by similarity?
5. Do record/group counts, per-molecule item sums and original-vote decisions
   communicate their actual scope? Which wording could imply independent
   confirmation, inactivity, efficacy or comparability without support?
6. What should a scientist inspect next for an unresolved/excluded result? Record
   any primary-method access needed, and distinguish that dependency from a
   software selection/explanation defect that can already be corrected.

For each case record: reviewer/name/date, supported conclusions, unsupported
conclusions, missing context, proposed presentation, acceptance/changes requested,
and source/protocol references actually reviewed. "Pending" remains the state
until a reviewer supplies a response. Maintainer policy choice, independent
scientific review and uncoached researcher usability acceptance are separate.

## Delivery boundary

Default adoption remains pending. Existing rules, source data, Card pins and
stored answers are retained. The opt-in #188 correction has its own
positive/conflicting/unresolved cases, public-input impact and exact-source
technical receiving at `c5b8af1`. These establish retained selection consistency;
they do not establish experimental target identity or independent scientific
acceptance. The reviewer response above remains required.
The activity explorer, economical agent access and original saved scientific
activity reading remain B4 work; this casebook does not implement those panels
or establish the required 0.15.0 human wow acceptance.
