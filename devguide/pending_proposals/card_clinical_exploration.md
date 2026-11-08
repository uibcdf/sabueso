# Clinical indication and registry exploration

Owners: Sabueso [#148](https://github.com/uibcdf/sabueso/issues/148),
native clinical semantics [#81](https://github.com/uibcdf/sabueso/issues/81),
checkpoint/delivery [#112](https://github.com/uibcdf/sabueso/issues/112).
This is the clinical B5 increment of the accepted rich 0.15.0 profiles.

## Implementation and qualification boundary

The development LIVE adapter is implemented. Human `view("clinical")` and
`answer("clinical_context")` share one captured result with compact-agent
`access.select("clinical")`. The [selected checkpoint](../evidence/clinical_live_checkpoint_20261108.json)
passes 576 distinct source cases, including all 40 owning cases; the complete
40-case clinical module also passes outside checkout with unchanged public
inputs. Both installed workflows copy/select it once. These repeated copied
cases add no distinct coverage. [CHECKPOINT](../CHECKPOINT.md) owns source epochs,
current gates and the next action.
The earlier complete 10,050-case receipt qualifies its recorded reader source,
not this new clinical implementation.

No independent clinical saved reader or original clinical capsule is claimed yet.
Qualify and commit the clean producer, verify coherent editable metadata, then
capture its genuine complete LIVE original before implementing that reader.
Public clinical saving truthfully reports unavailable in the meantime. Original
exploration formats and their scientific interpretations stay fixed.

## Native knowledge and row grains

`clinical_exploration@1` reads the existing `Card.clinical()` through a detached
capture. It preserves the complete native payload, indication/trial order,
source values and original query/quality records. Opening, selecting, explaining
or following this result never acquires a source. There are no scientific options.

The four explicit row grains are:

- `clinical_molecule_phase`: the retained ChEMBL molecule maximum-phase field;
- `clinical_indication`: one native indication, with its original term, MeSH
  heading, phase, reference types and cited trial IDs;
- `clinical_trial_citation`: one trial occurrence within an indication. A trial
  cited by two terms remains two occurrences, with its original indication;
- `clinical_registry_record`: one native retained trial context. Its registry
  record can be received, explicitly not found, or unverified because support is
  missing or bound to another role. A `tested_in` relationship whose registry
  reports not found retains the original ChEMBL citation.

ChEMBL maximum phase and ClinicalTrials.gov study phases/status remain separate.
Registry status/phases are not projected as unknown source values on citation
rows: those columns are not applicable to that grain. Conditions, interventions,
enrollment, dates, sponsor, result flag and every raw source field remain in the
native item and original source assertions. Intervention text never establishes
molecule identity. A citation, completed study or result flag establishes neither
efficacy nor a treatment recommendation.

The adapter retains native ordering, including the existing zero/missing-phase
ordering; this increment does not adopt a scientific/default ordering change.
Two terms sharing a MeSH heading stay separate. Citation counts count original
occurrences, not unique studies or independent experiments.

## Source, request and uncertainty scope

`clinical_support_membership@1` records exact original relationships and source
assertions. ChEMBL indication assertions bind to the relationship's molecule
subject and `relationships.investigated_for`; registry assertions bind to its NCT
object and `relationships.tested_in`. Molecule-phase assertions retain their
source-stated identity links. Subject, source or field mismatches are explicitly
unverified; missing references stay visible. Qualifier conflicts remain available.
These support records are derived metadata, never new SourceAssertions.

The original native knowledge-state rows remain unchanged under `native_rows`.
`clinical_query_scope@1` supplies separately identified presentation rows for
clinical areas absent from that native report: no matching request in a retained
enrichment ledger is `not_queried`; an absent ledger is `not_recorded`, with unknown
count. Original reported partial/failed/not-stated states are preserved.
`not_fetched` alone does not say whether trials were unrequested, limited or
unavailable. Neither an empty display nor an unanswered request establishes
absence in a registry or in clinical knowledge.

## Human and compact-agent continuity

Human items open complete original native items, explain their role-bound source
membership and follow exact retained assertion/relationship/request destinations.
Cited occurrences link to their complete original indication and its trial list,
and to their exact retained NCT context when available. The full indication list
is retained once rather than copied into every citation occurrence.
Every destination returns to the actual initiating view and retains its question.
Text/HTML previews are bounded and escaped; complete values stay readable.

`clinical_access_selection@1` supports declared projection, exact typed equality,
exact result membership and scalar ordering with nulls last in either direction.
Numeric phase operands retain their type: `4` and `4.0` are different requests.
Registry phases retain their native string list, with exact list equality and no
scalar ordering. Phase categories are not physical quantities and accept no
unit argument. Bounded pages defer values with their mandatory interpretation
together while retaining exact read paths. Foreign capture members/cursors are
refused.

## Completion sequence

After the clean genuine capture, implement a separately versioned independent
reader with frozen clinical/source/selection predicates. Qualify all original
human/machine/source/back observations, semantic refusal, plain/gzip/zstd resaves
and fresh inert/copied receiving. Never regenerate the original to satisfy a
later reader. Installed-platform/hosted receiving and B7 scientist, uncoached
researcher, agent, workload and actual-consumer acceptance remain separate.
Disease and B6 profiles follow; B8 and release remain unresumed.
