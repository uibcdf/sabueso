---
summary: Keep original model limitations and retained-filter scope visible through ordinary presentation steps.
issue: uibcdf/sabueso#148
status: implemented_candidate_receiving
opened: 2026-11-06
verification: 399 distinct selected cases, original public control and local quality gates pass; exact-source receiving separate
area: [human-exploration, structural-context, history]
---

# Structural scope through display navigation

## Observed problem

At source `df44e1e`, SDK `0.14.0+188.gdf44e1e`, the genuine public SDK185
Q8WZ42 session retains 64 experimental inventory rows for the native model's
201–1600 reference interval. Its original answer displays that sequence-version
date agreement is unknown and that sequence agreement does not establish
experimental equivalence. Filtering to `pdb:6FWX` preserves one displayed row,
all 64 original items and the unchanged `not_computed` outcome, but loses those
model limitations. Calling `table()` or `sort()` also loses the retained-filter
explanation. These are observed text/HTML presentation gaps, not changed source
knowledge or scientific output.

The renderer looked only at the immediate origin for model context and the current
operation for filter guidance. Ordinary presentation steps insert another origin
without changing the underlying question or result.

## Correction and boundary

Follow only recorded filter, sort and presentation steps within the same result
and exact question request. Recover the original question's model context from
that route. Focused structural details may retain the same question's limitations;
they are not labelled as a new filter selection. Display-filter guidance follows
only display steps and reports the current selected count, including zero.

Native reference/date uncertainty and original API-fragment limitations therefore
remain visible in summary, table, ordered/filtered answers and inert saved reading.
The original API fragment and range-alias policies are reused. An unrelated
question with equal options does not gain a model origin; opening a source or
another result does not inherit the preceding filter. No search through other
cached results or reconstruction of unrecorded historical intent is performed.

This changes current text/HTML presentation only. Scientific requests/results,
native and agent payloads, complete source support, quantities, selection/order,
return paths, stored flags and format choice remain unchanged. It adds no Card
schema, source assertion, scientific rule or storage format. Frozen semantic
verifiers and shared codec @13 remain byte-identical; #191's format @14 keeps
its existing meaning.

## Receiving and handoff

The original public session is read with Card reconstruction, current scientific
materialization and network access forbidden. Card and native-wire hashes remain
`40aa6cb6a226add3fa280fed065902bd2118eec16b90892d549299a670d39f30`
and `4aff984e82b58d8e05d029b561bcb61579d7f29966393be19195c575dc06db14`.
All 399 distinct selected cases pass: 171 structural cases, 227 other human/agent/
argument/quantity cases and one isolated receiving test. Its 35 copied nested cases
and seven focused cases overlap those sets and are not added. Ruff, warning-fatal
Sphinx and local governance pass. The complete public control preserves the exact
agent page and peaks near 202 MiB, with one low-priority CPU and zero owned swap.
The broader selected gate peaks near 362 MiB under the unchanged 512 MiB guard.

The [receipt](../evidence/structural_display_scope_20261106.json) records actual
before/after observations and bounded resources. Tests cover native and original/
modern-alias API fragments, live/saved positive and zero-match filters, complete
native/request parity, back navigation and a direct-question counterexample.

Owning work is #148, with #173/#191/#112 coordination. The maintainer-authorized
[owning update](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6678353796)
now records the correction and actual local receiving. The preceding filter and
CI recovery are reported in [#191](https://github.com/uibcdf/sabueso/issues/191#issuecomment-6678348141)
and [#167](https://github.com/uibcdf/sabueso/issues/167#issuecomment-6678351360).
Scientific/researcher/workload acceptance,
the B3 assembly-scope decision and exact-source hosted qualification stay separate.
B2 scientific review remains maintainer-deferred and 0.15.0 consolidation paused.
