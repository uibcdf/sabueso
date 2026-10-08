---
summary: Bounded private-consumer revalidation of the qualified recovered development checkpoint.
issue: uibcdf/sabueso#132
status: active
opened: 2026-10-08
closed:
verification: inspected
area: [consumer-acceptance, traceability, persistence]
blocked_by: []
supersedes: []
---

# Bounded consumer revalidation after consolidation

The qualified code checkpoint `dc4642414c46744f39d85cb666094b0d52dd705a`
passes a bounded execution of existing consumer cells, exact saved-state reading
and replay of original source answers. Overall consumer acceptance remains open
in [#132](https://github.com/uibcdf/sabueso/issues/132). A concrete acquisition
observation gap belongs to [#108](https://github.com/uibcdf/sabueso/issues/108).

## Scope and confidentiality

Evaluation uses editable Python 3.14.7 in the existing shared development
environment. Runtime code, schemas, packaging and test inputs match the qualified
checkpoint. This does not qualify an installed artifact or a new release.
The original installed-package environment guard rejects this editable scope as
expected; neither that guard nor the read-only consumer checkout was changed.

The maintainer explicitly authorized bounded identity requests to UniProt and
NCBI Taxonomy, including returned candidate records and taxonomy. No other
providers, broad profiles or mirrors were queried. Original workflow revisions,
notebooks, query payloads, scientific values, outputs, source archives and exact
artifact digests remain in an ignored private workspace. This public report
contains only generic engineering results. Local transport adapters are declared
separately from the unchanged original cells.

## Executed acceptance

| Exercise | Result | Qualification limit |
| --- | --- | --- |
| Original identity cells with authorized live inputs | 5/5 cells pass; two cards resolve; eight source responses archived; no warnings | Bounded identity acquisition only |
| Original local bibliography, curation-template and pinned-support cells | 9/9 cells pass; support remains readable after subsequent card saves; no warnings | Human curation and Evidence templates stay empty |
| Supplemental residue context and saved views | Named `source_active_site_selection@1` and `residue_set_composition@1` views retain support and separate source-sequence axes | Comparison explicitly remains `not_compared`; no correspondence or alignment is inferred |
| Supplemental local deck and packet | One deck and one identity/literature packet persist with original producer sidecars; no source operations | This is not execution of the original full packet-acquisition route |
| Independent saved-result reader | Two original and two current card pins, ten exact SourceAssertions, two unit-bearing quantities, one deck and one packet pass; eleven immutable files verify | Acquisition, derivation and fresh credit capture are forbidden; bibliography exports use original saved attribution |
| Original-answer replay | 5/5 identity cells pass without network access; both cards retain identical raw SourceAssertions, stored sections and scientific retrieval times | Original answers are replayed; fresh availability and missing historical pins are not qualified |
| Public-fixture transport preflight | 5/5 identity cells pass without network access | Explicit fixture adapter; separate from live acquisition |

Fourteen distinct original consumer cells pass. Inspection found 45 code cells
across eight notebooks: the environment guard is an expected rejection in the
declared editable scope and 30 cells remain unexecuted. Supplemental checks and
replay do not increase the count of distinct original cells accepted. Temporary
harness setup errors were corrected and recorded privately; they are not SDK
regressions or successful executions of the unrun original routes.

The original raw source archive and eleven immutable source/report files remain
byte-identical after local saves, independent reading and replay. Current saves
advance the mutable knowledge store while the original card pins still load their
exact earlier snapshots. No SourceAssertion becomes project Evidence, and no
scientific conclusion or scientist acceptance is inferred from passing cells.

## Concrete component finding

The raw archive contains four UniProt and four NCBI Taxonomy responses. The
acquisition operation sidecar contains four UniProt operations and no NCBI Taxonomy
operation. Native taxonomy records preserve source/retrieval information, but the
built-in taxonomy client is outside the declared 34-source observation coverage.
The trace explicitly declares other sources and custom clients `not_observed`;
it must not be presented as complete pipeline observation or bibliography.

The next bounded Sabueso slice under #108 should instrument the existing
`OnlineNCBITaxonomyClient.taxa` and fixture route, preserving batched request
scope, failures/missing records, original replay times and unknown source versions.
Use existing public fixtures or synthetic responses for regression qualification;
private execution inputs must not become public fixtures. This requires no new
provider and no shared-contract change. Instrumentation was not implemented by
the original documentation checkpoint; the subsequent implementation is recorded
below.

## Measured cost

| Exercise | Seconds | Initially reported `ru_maxrss` (MiB) |
| --- | ---: | ---: |
| Live identity acquisition | 13.801 | 942.30 |
| Local cells and supplemental saved views | 1.679 | 93.16 |
| Independent saved-result reader | 0.952 | 86.60 |
| Original-answer replay | 6.179 | 84.19 |

Timers start after process imports/setup; the RSS counter covers process history.
These are single-run observations, not matched sustained-memory samples or a
release benchmark. The initially reported live value used `resource.ru_maxrss`;
the follow-up below shows that this counter already had that value before importing
Sabueso. It must not be attributed to the identity operation or retained knowledge.
The original unprofiled process's Linux high-water mark was not recorded, so it
cannot be reconstructed from this receipt.
At the identity-stage boundary, enumerated retained files total 1,159,163 bytes;
the archive records 213,460 response-content bytes, compressed to 30,920 stored
content bytes. These nested measurements are not additive, and the file total
does not describe the later complete workspace after local saves and exports.

## Remaining acceptance and development order

Keep #132 open. Original broad structural/activity profiles, structural inventory,
full packets and comparative-context acquisition remain unexecuted. Other
documented consumer routes without an executable baseline remain unqualified.
Historical notebook outputs exist, but their original stores/archives are absent;
current cards cannot reconstruct or qualify those historical pins or credit.

The follow-up closes the observed taxonomy-operation gap under #108 and rechecks
bounded reader/replay behavior. Choose the next existing consumer route with an
explicit source-access scope; avoid widening queries or downloading mirrors merely
to finish a checklist. Continue the foundational scientific journey/query work in
[ROADMAP.md](../ROADMAP.md#immediate-resumption-sequence), with persistent Nextia
Evidence and shared MOLI recording acceptance retained by their owners. Earlier
[public CI qualification](post_recovery_public_checkpoint.md) remains the code
baseline; this report adds bounded editable-consumer evidence only.

## Taxonomy and memory follow-up

The existing built-in online and fixture `taxa` routes are now observed, including
public `get_taxon` and normal card/packet enrichment. `get_taxon` carries a detached
trace in its source envelope; native taxon returns, scientific card serialization
and schema remain unchanged. `ncbi_taxonomy_observation@1` records completed
batches, source omissions, unavailable local inputs and unanswered failure scope.
Completed batches remain creditable after later failure, and archive replay
preserves original scientific retrieval times. Route `v2` is not a record revision;
unknown revisions and taxonomic-publication metadata remain explicit.

The coherence review also corrects a pre-existing fixture-state inconsistency:
an unavailable organism fixture was previously mapped to `not_found` and card
knowledge state `not_stated`. Fixture metadata now declares unavailable IDs;
public lookup reports a connector failure and enrichment reports `unavailable`.
A source-stated empty online answer remains not found. Native records and
partially available ancestor support are preserved; no new source access follows.

With the new adapter, both the authorized live execution and original-answer replay
record eight operations: four UniProt and four NCBI Taxonomy. Replaying the original
answers still yields identical SourceAssertions and stored scientific sections.
An independent reader rechecks the original persisted cards, support, units, deck,
packet and immutable files without acquisition, derivation or fresh credit. Original
archives, execution receipts and the private checkout remain unchanged. All new
fixtures/regression inputs are public or synthetic; no private data enters Git.
Earlier four-operation sidecars remain original; new replay traces describe the
actual replay and do not reconstruct missing historical credit.

Memory sampling starts before importing Sabueso and records Linux `VmRSS`/`VmHWM`
alongside `resource.ru_maxrss` and Python allocation tracking. The live process
starts at **19,236 KiB VmHWM**, while `ru_maxrss` already reports **964,916 KiB**;
that counter remains constant throughout execution. Its 942.30 MiB value predates
the SDK execution rather than measuring new identity-operation allocations.
The sampled live Linux peak is **135,120 KiB (131.95 MiB)**; replay peaks at
**131,688 KiB (128.60 MiB)**. Python tracked allocation peaks are 41,485,398 and
41,188,718 bytes, respectively. These measurements include profiler overhead and
are not uninstrumented production benchmarks or a comparison to the earlier
unprofiled replay. No 942 MiB SDK allocation or memory optimization is established.

Final selected regressions pass **173 tests / 23.43 s**; full local-original qualification
passes **5,592 tests / 196.16 s**, with ten expected fixture warnings. Both use
Python 3.14.7, pytest-receptor and 12 workers. Warning-failing Sphinx passes;
registry, protected-input delivery, Ruff and governance checks pass. Published
code `a05e0a3132a43bf3a7bd53b94217db9690f39693` passes
[15/15 exact-SHA CI jobs](https://github.com/uibcdf/sabueso/actions/runs/37847914597)
and [governance](https://github.com/uibcdf/sabueso/actions/runs/37847914659), inspected
with gh-run-receptor. All nine Linux/Windows/macOS repository-input lanes pass
4,039 cases with ten native skips and 26 online deselections. Four installed public
Ackredit 0.9.0 receiving lanes pass 981 cases each and the public workflow. Linux
Python 3.14 retains 67 unclosed SQLite warnings, separately tracked in #133;
other repository lanes have six expected fixture warnings and receiving lanes two.
This is code/receiving qualification, not a new Sabueso release. #108 remains open
for other source/derived-operation/bibliography gaps; #132 remains open for the
unexecuted consumer routes and actual scientific acceptance.
The [sanitized qualification receipt](taxonomy_followup_checkpoint.json) records
this follow-up separately from the original bounded-consumer checkpoint.
