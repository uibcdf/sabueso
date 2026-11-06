---
summary: Preserve opaque literal metadata through chemical saved-reading dispatch.
issue: uibcdf/sabueso#148
status: locally_verified_checkpoint_hosted_pending
opened: 2026-11-06
area: [human-exploration, persistence, literal-integrity]
---

# Literal metadata in the chemical saved-reading candidate

Current local disposition: committed `0f197e5` passes the [705-case checkpoint](../evidence/chemical_saved_checkpoint_20261106.json) and complete public saved workloads. Hosted/scientific/researcher acceptance remains separate. The observations below retain the original precommit chronology.

An opaque metadata object may retain `context`, `native_payload` and nested
`explanations` keys. Those names alone cannot establish scientific ownership.
Original false, zero, null and array values must remain inspectable.

Two controls with a chemical-looking or unrelated adapter declaration passed
under the 128 MiB focused guard after explicit metadata ownership was added to
chemical routing. A subsequent `context=False` control reproduced a save failure:
`StorageError`, caused by a boolean receiving `.get`. The new @15 verifier still
entered inherited scientific-discriminator helpers for this literal object.

The candidate now routes registered literal metadata directly through the original
literal request predicates and keeps its state checks on that same basis. An
additional direct traceback located the remaining false/null/array failure in the
earlier explanation-request precheck. The @15 dispatcher now excludes explicitly
registered metadata from that scientific precheck; it still applies full literal
request, target, state and display verification. The
original formats @1–@14 and their frozen predicates are unchanged. An explicit
scientific manifest cannot claim a literal metadata object. This is a correction
within the uncommitted @15 candidate, with no change to native chemical knowledge.

The regression in `tests/core/test_card_saved_chemical_offline.py` now covers
all six scientific adapter declarations, an unrelated declaration and
false/null/array contexts. All ten cases pass after correction. A separate
resealed substitution proves that metadata cannot claim a scientific manifest.
Three further controls preserve related/back navigation from literal `items`.
These fourteen focused cases use a minimal synthetic molecule Card to isolate
namespace ownership without loading unrelated public data. The full 38-case saved
module retains its genuine SDK193 controls for scientific receiving.

The earlier five-case run stopped at the strict 128 MiB RSS ceiling; the next
single-case run stopped at the unchanged 6 GiB host reserve. A bounded resource
watch subsequently timed out without launching a test. These are not passes.
The fourteen corrected controls peak below 100 MiB with zero owned swap; complete
source, installed, mixed and historical reruns remain pending available headroom.
Do not relax limits or substitute the minimal namespace controls for those gates.

Static review also identified a similar `items`-link discriminator in the @15
verifier. Its probe first deferred at the host reserve, then reproduced the
boolean `.get` failure when resources returned. Explicit metadata ownership now
keeps that branch literal. The three related/back controls and the combined
fourteen-case gate pass after correction. All source-supported structural links
still enter their original predicates; original scientific meanings stay fixed.

Owner: #148/#112. Reporting remains in the local issue draft pending the existing
publication permission. See the [candidate contract](../pending_proposals/chemical_classification_exploration.md)
and [receiving receipt](../evidence/chemical_saved_candidate_20261106.json).
