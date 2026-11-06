---
summary: Share exact saved JSON components while retaining original scientific and display bindings.
issue: uibcdf/sabueso#167
status: implemented_candidate_receiving_pending
opened: 2026-11-06
verification: full64-item local receiving and1042 distinct cases pass; committed-SDK reproduction and hosted qualification pending
area: [exploration-persistence, human-exploration, agent-access]
---

# Shared saved-view values

## Problem and preserved meaning

The [native interval journey](card_native_model_navigation.md) exposed a complete
public Card session with 64 retained structure-inventory rows. At SDK183 the
session repeated 213,815,942 bytes of view records, against 9,421,317 bytes of
source/result objects. Its original 512 MiB guard stopped preparation; a separate
bounded diagnosis reached the explicit 64 MiB decoded-byte refusal. Query/render
itself used about 124 MiB. Those failures remain evidence, not a passing workload.

The candidate stores exact repeated JSON values once. It retains every view,
selection, source, occurrence, alternative, qualifier, quantity and return route.
Storage equality never merges entities or SourceAssertions and does not establish
scientific correspondence. Existing scientific questions and rules are unchanged.

Small sessions keep their original formats. A session above 16 MiB of logical
canonical JSON uses `sabueso.card_exploration@13` only when shared storage saves
at least 1 MiB. This is structural sharing before the existing `none`/`gzip`/`zstd`
transport, not another compressor or a new data source.

## Representation and original verification

`shared_exploration_values@1` records mappings, arrays and long text in a
content-addressed graph. Mapping keys are canonical and unique; arrays retain
order and duplicate occurrences. Scalar types, UTF-8, quoting, signed zero and
finite numeric values retain their JSON meanings. Native CIF tokens remain
opaque values. QuantityRecord conversion stays with the existing codec.

`shared_exploration_values_binding@1` verifies the physical member/bundle digests,
every node digest, reference closure and exact logical byte count. Missing,
unreachable, cyclic, malformed and unsupported nodes are rejected. It calculates
logical work before constructing the private decoded graph.

The logical bundle retains its original format and semantic verifier. All frozen
verifiers @1–@12 remain unchanged. Their original header predicates are replayed
through a bounded projection: source/result manifests remain complete, and one
representative of each required navigation-marker type preserves their `any`
predicates. No display-state hash of the fully expanded document is allocated.
Every complete logical view then passes its original, unprojected display,
request, identity, source and navigation checks. A fresh representation digest
cannot replace these scientific/semantic checks.

Decoded containers may share storage only within the private capture. Public
payload, row and support access retains defensive copies. Owned JSON native
payloads avoid another private deep copy; typed quantity payloads still use the
original quantity decoder. Reading performs no acquisition, Card rebuilding or
current scientific interpretation.

## Visible resource contracts

Human `CardView.save`, agent selection `save` and `read_exploration` gain
`max_logical_bytes=268435456` (256 MiB), with one ArgDigest handler. It bounds
canonical JSON work with repeated values counted for every occurrence. A small
physical graph cannot conceal exponential validation work. A positive integer
raises or lowers the ceiling; explicit `None` disables it. Backend guards remain
active when digestion is skipped. Refusal reports the counted lower bound, the ceiling
and the exact override route; no partial file is returned.

Existing encoded/decoded defaults remain 64 MiB and the read window remains
8 MiB. For shared packets, the decoded ceiling also bounds combined non-view
metadata and each complete logical view, so structural sharing cannot turn a
small file into one unbounded Card/object/view. The complete repetition between
views uses the separate logical ceiling. Existing explicit decoded/window
overrides keep their meaning. Limits are never increased silently to pass a test.

The writer checks exact sealed JSON size before allocating that text. Physical
transport receipts remain physical; saved validation additionally identifies the
representation rule, original logical format, logical bytes and shared-node count.
Hashes establish captured consistency, not source authenticity or scientific truth.

## Receiving and scope still open

The new standalone gate covers the graph, defaults/overrides, UTF-8 and scalar
fidelity, distinct entity IDs/occurrences/quantity records, all Card natures,
human/agent save/read/resave, defensive access and freshly rehashed semantic
substitutions. The original SDK184 writer source is archived for a labelled
writer replay over five retained public statements. Its format @12 capsule is
**an archived-writer replay, not an independent pre-reader artifact**, and its
empty experimental inventory belongs to a deliberately reduced Card. The real
SDK181/182 original captures remain separate historical controls.

Both installed routes copy/select the standalone gate and replay capsule.
The [technical receipt](../evidence/shared_view_state_20261106.json) records actual
receiving and resource conditions. The complete 64-item save/read/resave journey
now passes locally: 225,817,382 logical bytes become 15,549,478 physical JSON
bytes and a 5,337,106-byte gzip file, with 366,686,208 peak owned RSS bytes,
one low-priority CPU and zero owned swap. All 1,490 source assertions, 215
relationships, original wire/result identities and five source routes remain.
The cold reader forbids current native mapping, parsing, Card reconstruction
and network access. Default physical limits remain 64 MiB. This candidate's
SDK label precedes the new implementation commit; it is not a pre-reader capture
or final-source qualification.

The first candidate exceeded the original 512 MiB writer ceiling. A bounded
encoder memo and single node serialization corrected that peak. A second run
saved successfully but exceeded the combined budget when a cold reader started
while the writer still held its complete session. The passing control instead
exits the writer before starting its independent reader, with the orchestrator
and each active child included in the same resource guard. These are explicitly
different process topologies; concurrent complete sessions are not qualified.

Reproduce with [the offline control](../evidence/check_shared_view_state_20261106.py),
passing the pinned complete public Card through `--card`, a new `--output`
directory, and optionally the exact `--expected-sdk`. Use an external resource
supervisor. Keep complete Card content and original quantities/sources; the
smaller controls cannot substitute for that measurement. All 1,042 distinct local
cases pass, including historical/scientific/human/agent/quantity/argument gates,
fixture/registry/package checks and the isolated copied 56-case receiving payload.
Nested and repeated cases are not added to that count. Final committed-SDK
reproduction and exact-source hosted qualification remain pending.
Use one CPU, low priority and host-memory reserve; defer a gate when the concurrent
machine workload leaves insufficient room.

B3 and wider scientific/researcher/workload acceptance remain open. B2 review is
maintainer-owned and deferred; release consolidation stays paused. This candidate
does not complete the broad 0.15.0 panels or its required human experience.
