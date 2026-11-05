---
summary: Read original AlphaFold sequence intervals under both API field names without hiding conflicts or changing saved meanings.
issue: uibcdf/sabueso#148
status: implementation_receiving
opened: 2026-11-05
area: [predicted-structures, source-contracts, human-exploration]
---

# Original AlphaFold sequence-range aliases

The [source's rename notice](https://www.ebi.ac.uk/pdbe/news/breaking-changes-afdb-predictions-api)
names `sequenceStart`/`sequenceEnd` as replacements for
`uniprotStart`/`uniprotEnd`. The retained public P52270 metadata still contains
both agreeing pairs. Modern-only and disagreement cases below are explicitly
synthetic source-contract counterexamples, not an observed current API outage.

## Rule and original source contract

New mapping uses `alphafold_sequence_context@2` when either modern endpoint key
is present, including null or malformed values. Legacy-only records retain @1.
The new rule retains every supplied pair, exact types, endpoint presence and
original field names in `sequence_context.range_basis`. Both endpoints must be
positive integers in ascending order. Booleans, floats, strings, nulls, reversed
and incomplete pairs cannot establish an interval. Two complete pairs must
agree exactly. A bad pair cannot be replaced silently by a good alias; endpoints
from different pairs cannot be spliced together.

The rule privately projects a successfully bound interval into the unchanged
original MD5/identity policy. That projection is a derivation input, never a
SourceAssertion: original model values and statement IDs are preserved.
On conflicting, invalid or incomplete aliases, range is unknown and neither
whole-reference coverage nor a structural question is admitted. Original
declarations and checksum comparisons remain inspectable. Matching checksums
alone do not establish identity or resolve range disagreement.

Derived qualifier scope now includes `range`. Replay requires the original
model, exact UniProt inputs, named rule, parameters and original output
application. Native `predicted_structure_scope@2` admits that new binding;
original @1 contexts retain their own rule and replay semantics. Units,
coordinate interpretation, source requests and model selection are unchanged.

## Human, agent and saved journeys

The existing predicted-model panel explains alias conflicts and invalid or
incomplete intervals in plain language. Full original inputs remain available
through relationship/support inspection and economical literal agent pages.
Whole-reference and exact-fragment questions use requests @2 and navigation @6
for the new context. The fragment basis names all supporting original range
pairs. Reference/sequence/MD5 prerequisites, include-fragment policy and
coordinate-correspondence limits remain explicit; no physical calculation or
coordinate acquisition is introduced.

New navigation saves as `sabueso.card_exploration@10` with independent
`model_range_navigation_binding@1` verification. Frozen context and navigation
predicates bind exact original fields, requests and support without current
mappings, native readers, Card construction, fixture access or network. Formats
@1–@9 and their verifiers are untouched. A producer capsule created before the
format10 reader, plus genuine pre-change SDK177 modern-only/conflicting sessions,
distinguish new receiving from historical preservation. Old unknown intervals are
not filled in; old recorded coverage is not recomputed under the new rule.

Current packets use `packet_aspects@16`, inheriting @15 outside predicted-model
scope. Original mappings through @15 retain their original model-context policy
and rule inventories. Index/terms access supports the new version without
altering stored old packet payloads.

## Receiving and remaining acceptance

Owned original producers, source hashes, selected gates, resource receipts and
exact-source hosted receiving live in
`recovered_work/alphafold_range_aliases_20261105/`, owner #148/#173/#112,
review at the next B3 checkpoint. Technical receiving does not establish
independent scientific/researcher or whole-session workload acceptance.
A [genuine archive control](alphafold_archive_fragment_control.md) now receives
the native public input; production Card intake remains pending. These synthetic
counterexamples do not qualify a deposited partial model. B2's maintainer review
remains deferred and 0.15.0 release consolidation paused.

Selected receiving reconciles **863 distinct cases** across the owning,
packet/schema and human/history scopes; it is not one full-suite run. The
[dated receipt](../evidence/alphafold_range_aliases_20261105.json) retains initial
failures, exact predicate recoveries, the final copied outside-checkout module
and resource scope. The 18 new optional shape paths are recorded in unpublished
0.3.14 (1,985 paths). Independent hosted qualification remains separate.
