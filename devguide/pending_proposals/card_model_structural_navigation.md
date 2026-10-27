---
summary: Source-bound whole-model questions share the existing reference-region inventory and preserve original navigation.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-27
verification: source_specific_receipts_in_owning_issues
area: [human-exploration, predicted-structures, navigation, persistence]
---

# From a model to its original structural reference

A predicted-model item's `related()` now offers **Experimental structures on this
model's original reference**. It prepares the existing `region_coverage` question;
it does not create a structural reader, acquire data or recommend a model.
Human and compact structural selection reuse the same captured inventory/result.

## Admission and scientific limits

`model_structure_request@1` requires the original source-bound AlphaFold context,
exact focal-entry identity, a verified whole-reference model range/checksum and a
consistent source-supported canonical reference. The selected checksum/length
must retain the actual original assertion IDs and values; the current primary
sequence must also match that original MD5. A shared checksum never establishes
entity identity. Alternative qualifiers or reference conflicts prevent an
implicit choice. Caller changes after capture cannot replace the retained inputs.

A fragment, isoform, different accession, uncertain checksum, changed reference
or missing historical application instead gives an inspectable unavailable
question with original context and a reason. This v1 does not map fragments,
compare fragment sequences, project residues, establish observed coordinates,
experimental equivalence or assembly relevance. These remain explicit limitations,
not a negative scientific finding. The broader model/fragment/assembly and compact
predicted-model routes remain in the [completion inventory](card_exploration_completion_0150.md).

## Original navigation and saved reading

`retained_context_links@4` adds this question and the complete original reference
input destinations. Its typed source location identifies the actual model
relationship. Existing generic @1/@2, annotation @3, ligand and quaternary
navigation keep their original predicates. Older files are never backfilled with
a new question. Unvisited saved requests remain `not_saved`.

The frozen model input binding comes from qualified source `1bfc9e9`, using the
existing versioned AlphaFold context rule. Independent verification uses detached
retained inputs and frozen canonical/model admission; it does not construct a
current Card, run current model readers, acquire source records or read fixtures.
Expected verification values do not replace original results. The destination is
bound to the originating ready question and its exact options; resealed request
and origin substitutions are refused. Unknown outcomes retain their original
reason and input scope. No stored Card schema, source registry or native
scientific rule changes are needed.
Source version/retrieval metadata are those retained by the capture. Semantic
assertion IDs do not independently identify a historical input observation;
[#166](https://github.com/uibcdf/sabueso/issues/166) audits that separate provenance
question. This navigation does not reconstruct unrecorded observation history.

## Historical producer and qualification

The original saved quaternary format @4 capsule from clean `1bfc9e9`, actual SDK
`0.14.0+111.g1bfc9e9`, is now preserved unchanged under `tests/core/data/`, with
producer identity, hashes and synthetic-input scope in that directory's README.
Its producer passes [CI 15/15](https://github.com/uibcdf/sabueso/actions/runs/40452755257)
and [governance 1/1](https://github.com/uibcdf/sabueso/actions/runs/40452755212): full
captures, member hashes, archives and all thirteen summaries verified. Nine
source lanes pass 5,883 each; four installed public-Ackredit lanes pass 1,452 each.
That receipt qualifies the original producer, not this new navigation automatically.

Selected gates cover public TcTIM, synthetic source/identity/checksum/context
limits, independent inert reading, original request/membership/source links,
rehashed changes and actual question origins. Broader local and exact-source
remote results belong to #148/#112. Technical checks do not establish researcher
acceptance or an agreed workload budget. The earlier scoped persistence-size
observation remains open; this navigation change makes no storage-size claim.

Owned local proof: `recovered_work/model_region_148_20261027/`, owner #148/#112;
review at the next exploration checkpoint, exact-source CI completion or release
acceptance. Preserve original capsules, useful receipts and active captures;
remove only finished owned scratch. Release consolidation remains paused.

The final selected integration gate passes **1,103** cases in **155.40 seconds**
with twelve receptor workers and fatal runtime/SQLite/unraisable guards. Its sole
warning is a declared public STRING fixture cut. It includes current AlphaFold
context and native predicted views, all Card access/navigation/history, structures,
oligomer, packet/table/baseline and argument/quantity contracts. The new model gate
has **27** cases, including public positive and independent inert-process reading.
The original saved quaternary module has **41**, including the unchanged genuine
SDK111 producer capsule. These selected gates do not claim a new full-suite or
exact-head remote result for the new source; those receipts remain separate.

All **53** public-guide Python blocks execute offline, including the new model
transition and the existing cross-topic saved journeys. Warning-fatal Sphinx,
Ruff format/lint (**1,177** files), **341** local Markdown targets/anchors,
Python 3.11 parsing of eight changed source/test files, schema/shape **0.3.14** /
**1,938** paths, registry, fixture policy (**51/37**), dependency and governance
checks pass. The full local suite at the preceding code checkpoint and its
remote receipt remain historical; this navigation-only block selects its owning
and broad integration gates under `TESTS.md` and gets a separate exact-source CI.
