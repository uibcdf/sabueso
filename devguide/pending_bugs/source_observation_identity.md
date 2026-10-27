---
summary: Stable statement identity is not observation identity; conflicting duplicate records must not overwrite source metadata.
issue: uibcdf/sabueso#166
status: open
opened: 2026-10-27
verification: source_specific_receipts_in_owning_issues
area: [knowledge-integrity, provenance, aggregation, refresh]
---

# Semantic assertions and source observations

## Audit conclusion

A SourceAssertion ID deliberately identifies a semantic statement independently
of retrieval time and source release. The same statement in two source releases
has one assertion ID; each complete Card snapshot identifies which retained
source/version/retrieval record was read. Changing assertion IDs would break the
accepted contract and is not the correction.

The public `refresh_card` route rebuilds a new Card. Synthetic UniProt/AlphaFold
fixture clients with the same checksum/length and different entry releases and
retrieval dates confirm that both model-value interpretations remain supported,
the statement ID stays equal, the Card pins differ, and loading the earlier pin
returns the unchanged earlier metadata. Refresh does not transplant the old
model derivation into new observations. Original caller data remain unchanged.

The ordinary mapping-merge/aggregation route exposed the actual defect:
`merge_mapping_results` preserves both input records, but `SourceAssertionStore`
previously kept whichever duplicate ID was added last. Different source versions,
retrieval dates or other observation context were discarded without an error.
Reversing the inputs reverses which metadata survive. Store insertion also kept
caller-owned dictionaries, permitting later external mutation of captured input
records. These are confirmed local defects, not demonstrated corruption of an
already stored pin or an original saved exploration.

## Bounded correction

`SourceAssertionStore.add` deduplicates identical records and recursively completes
only conflict-free `source_metadata`. Missing keys may be supplied; an existing
scalar/list or explicit null cannot be replaced. Every other retained field must
match exactly, using typed canonical JSON comparison. Conflicts raise SMonitor
`SchemaError` before mutation. New records and completed metadata are detached
from caller objects. Distinct versions/retrieval observations need separate pins.

The first deliberately strict candidate rejected every metadata difference. Its
full offline gate caught ten compatibility failures (7,472 passed); it was never
published. Diagnosis separated actual context collisions from legitimate input
completion and explicit original-intake restoration:

- UniProt P35372 contains equal function text for distinct native products. Newly
  mapped molecule-scoped text comments now put the complete original comment and
  selected text index in `asserted_value`, and keep the text in `normalized_value`.
  Different contexts receive different semantic IDs under the unchanged algorithm.
  Unscoped text mapping and old stored assertions remain unchanged.
- Europe PMC can return the same native annotation through distinct article
  selectors and retrieval dates. `located_annotation_observations@1` explicitly retains
  every pair in `source_metadata.annotation_requests[]`, with the rule named by
  `source_metadata.annotation_request_rule`. The scientific annotation mapping
  remains @2; native and frozen knowledge-coverage rows keep the same meaning.
  Only identical subject, native content, source release, acquisition and remaining
  metadata can coalesce.
  The root selector/date is the first canonical-JSON-sorted receipt, not an inferred
  latest/earliest source observation. Original request outcomes remain separate.
  The literature explanation follows all retained selectors. Conflicting native
  observations never coalesce; no generic source/version union is introduced.
- Literal extraction refresh already validates complete original support before
  restoring its first intake time. That deliberate restoration now uses explicit
  replacement after whole-batch typed canonical-JSON prevalidation, rather than
  implicit store overwrite. A failed batch changes no prior record.
- Two synthetic helpers omitted the statement subject from their simulated source
  content; they now distinguish different source statements correctly.

The optional receipt paths are recorded in unpublished schema 0.3.14 and migration
metadata. Migration neither invents missing request observations nor reconstructs
lost product contexts. Refresh obtains new inputs. Published schemas, original
pins, frozen capsules and scientific rules stay unchanged. Raw Card/store edits
remain intentionally mutable and create a different Card state.

## What original means

An original saved reading preserves the exact input values, records, qualifiers,
versions, dates and outputs **in its captured snapshot**. A derived model's input
IDs and replayable values do not independently identify the particular source
observation used by a historical mapping invocation. Acquisition traces describe
observed source calls; an arbitrary custom client or a bare semantic assertion ID
does not establish that stronger binding. No old observation is reconstructed
from the latest source record, and no new provider access is credited by reading.

Use the original pinned Card (and explicitly retained acquisition sidecars where
applicable) when reviewing that state. If a workflow needs a distinct historical
invocation-observation reference, that must be supplied/stored explicitly; it is
not inferred by this correction. The existing native value rules and frozen
historical results retain their semantics.

## Qualification and ownership

Regressions reproduce both merge orders, version/date/native metadata/acquisition/
normalization/subject/type differences, compatible metadata completion, alias/date
receipt retention and conflicting-context refusal, scoped native comment identity,
exact duplicate deduplication, caller isolation, and the real public refresh/rebuild/store path using synthetic fixture
clients and no network. The first selected source/model/resolver gate passes **72**
cases. Wider integration, full code validation and exact-source CI have separate
receipts in #166/#148/#112. Technical/source acceptance remains separate from
researcher usefulness, workload budgets and release-artifact qualification.

Owned evidence: `recovered_work/source_observations_166_20261027/`, owner #166/#112;
review at the next exploration checkpoint, exact-head CI completion or release
acceptance. Retain original fixtures/pins/capsules and useful receipts; remove only
finished owned scratch. All work targets **0.15.0**; release consolidation stays paused.

The selected aggregation/curation/acquisition/refresh/store/migration/application/
model/history/quantity gate passes **334 cases /122.40s**, with twelve receptor
workers and fatal runtime/SQLite/unraisable guards. Two warnings are explicit
simulated UniProt failures in the acquisition regression. Core insertion affects
all sources, so a separate full offline checkpoint is required before publication;
its source/SDK/hash/remote receipts are recorded in the owning issue.

The initial full-suite compatibility failure is retained as diagnostic evidence,
not qualification. Subsequent gates and final source/SDK receipts supersede only
the local candidate, never the original public inputs or earlier measurements.

The refined selected compatibility gate passes **207 cases /22.43s**, including
actual public alias intake with different response dates, native/frozen coverage
row parity and atomic typed original-extraction restoration. Four warnings are
explicit unavailable-Europe-PMC regressions. The scientific annotation mapping
remains `located_accession_mapping@2`; only its independent observation-receipt
policy is new. Final full-suite and exact-source remote receipts remain separate.

The complete code checkpoint at `c649a06` runs **7,497 cases**, with **7,495 passed
and two prior scoped-comment assertions failing** /989.09s. Both expected raw
text where the documented new contract retains native comment context plus
normalized text. Their tests now verify both original native context and textual
Card values. The expanded owning/native gate passes **323 /38.91s**. Production,
schema and input bytes are unchanged from the full run; only those two test files
changed. The exit-1 full receipt is retained honestly: no all-green local full
rerun is claimed. Final-source targeted checks and exact-head CI have separate
receipts. Release and researcher acceptance remain separate.

After the maintainer's memory caution, heavy local gates run serially with four
workers and built-in `tmp_path_retention_policy=failed`. The full code run peaks
at **2.09 GiB owned RSS**, **zero owned swap**, and at least **6.97 GiB genuinely
free host RAM**. Finished owned scratch is removed after preserving useful proof;
active outputs, original inputs/capsules and other owners' resources stay protected.
