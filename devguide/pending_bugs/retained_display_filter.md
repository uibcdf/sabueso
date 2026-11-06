---
summary: Filter retained scalar cells without promoting an uncomputed scientific result or rewriting old display history.
issue: uibcdf/sabueso#191
status: implemented_candidate_receiving
opened: 2026-11-06
verification: 685 distinct selected cases, full public control and local quality gates pass; exact-source receiving pending
area: [human-exploration, history, public-api]
---

# Retained display filtering

## Reproduced defect and current selection

The public frozen P52270 regional question retains seven structure declarations
with scientific status `not_computed`. Before the correction, equality for 1SUX
returned all seven rows, without recording a filter operation or explaining the
no-op. The complete public Q8WZ42 interval journey exhibited the same behavior
with 64 retained rows. The early guard confused unavailable scientific calculation
with the availability of retained scalar cells.

`retained_cell_filter@2` selects exact retained cells using the existing column,
operand and physical-quantity validation. It preserves the original scientific
status and reason, complete native result, source support, units and result
identity. A zero-match display keeps the underlying result and uncertainty;
it does not assert source/global absence. Chained projections remain bounded to
the already selected rows. Equal labels keep their distinct original entries.

Unavailable views without retained rows now refuse explicitly. Unavailable
assembly views whose adapter has no supported display projection also refuse;
their historical behavior remains available only during original verification.
Ordinary `ok`/`empty` filtering and ambiguous link selection retain their existing
semantics. Machine scientific selections are unchanged.

## Explicit history boundary

New semantics are recorded in `filter_policy` on the display operation. Saving
such a route uses outer `sabueso.card_exploration@14`, verified by
`retained_cell_filter_binding@1`. The single payload keeps its original scientific
and storage representation, including the existing shared-value format @13.
The payload is not asserted to be a standalone legacy display bundle when a new
filter operation is present. Older readers reject the new outer format explicitly.

The envelope binds its exact producer, policy, payload and independent expected
digest. Nested policy envelopes, unknown policies, unmarked new operations,
downgrading to an old standalone format, changed display membership and changed
scientific status/reason are refused. Original scientific, source and navigation
predicates still check the complete payload. A scoped ContextVar selects legacy
display filtering while original files are verified, and the new selection only
under the explicit outer policy. It resets on success and failure and never
changes another caller's navigation. Original verifiers and shared codec @13
remain byte-identical.

This is an exploration-file boundary, not a Card schema change, scientific
classification, migration, SourceAssertion or Evidence. Physical limits remain
64 MiB, logical retained-content work remains 256 MiB and the codec window remains
8 MiB by default, with the existing visible positive/None override contracts.
Logical view states are released after shared packing; the envelope does not
retain an additional expanded copy. Only one policy wrapper is supported.

## Original receiving

The actual clean SDK187 producer `6bdac1ff328b5cf327ac873f33f13977ae3d00a8`
saved the pre-fix behavior before this change. Its original 314,462-byte file has
SHA256 `d806c3802dbfab562f1951baa62fef3aa9f9c9f5bb58ad27d97d165401d54225`.
It preserves all seven labels and no recorded display operation. The reader must
keep that membership; it cannot infer the discarded caller intent. Re-saving the
original route preserves it. Calling `filter()` now creates a separate new route.
The original file is never regenerated with the correction.

`test_card_retained_filter_offline.py` covers live and saved requests, quantity
equality, duplicate declarations, missing data, no-match/chained selection,
old/no-op and new read/resave, shared payloads, context reset and freshly rehashed
policy/membership/status substitutions. Both installed routes copy/select it and
the original capsule. The copied receiving payload runs without checkout fixtures.

The [technical receipt](../evidence/retained_display_filter_20261106.json) records
685 distinct selected cases, the complete public 64-item filtered
save/independent cold-read/resave control and actual resource conditions. The
control preserves all 1,490 SourceAssertions and 215 relationships, with about
327 MiB peak owned RSS, one low-priority CPU and zero owned swap. The copied
31-case module needs no checkout fixtures. Original scientific/history receiving,
Ruff, warning-fatal Sphinx, fixture/registry and local governance gates pass.

Prior-source CI `42163618832` has the same observed flat-format test expectation
failure on Linux 3.12 and 3.13: the archive control assumed standalone @11 while
exact sharing produced @13 with logical @11. Its corrected expectation verifies
both levels and retains all original-content/source/export assertions. All five
archive-control cases pass locally; the prior source remains unqualified.

Source/full/installed-artifact qualification
and scientific/researcher acceptance remain separate. Correcting this bug does
not close B3, decide assembly modeling scope, adopt the deferred B2 scientific
policy or resume 0.15.0 consolidation.
