---
summary: Bound UniRef member pagination independently of retained row count.
issue: uibcdf/sabueso#140
status: open
opened: 2026-10-10
closed:
verification: local_runtime_tested
area: [source_access, attribution, knowledge_integrity]
blocked_by: []
supersedes: []
---

# UniRef member pagination termination (#140)

Owner: [uibcdf/sabueso#140](https://github.com/uibcdf/sabueso/issues/140), following
the [UniRef observation checkpoint](../pending_proposals/uniref_observation.md).

The published 0.14.0 client and source `c6cb0e3` capped retained rows at 5,000 but
did not bound requests when continuation pages were empty. A synthetic transport
reproduced repeated continuation without any provider query; this is a client
termination defect, not a claim that the live service emitted such links.

Development uses `uniref_member_pagination@1`. Each member operation may request
at most 100 logical pages, including empty responses, and never requests an exact
URL twice. Detection happens before the next request. Either condition raises
`ConnectorError` with structured SMonitor context (`stop_reason`, `remaining_url`,
`requested_pages`, `page_limit`). Completed pages, original headers, counts and
portable resource attribution survive in detached observation; no partial client
result or cluster/member card assertions are returned. Empty pages followed by
failure do not establish complete absence.

Reaching the existing 5,000-member ceiling remains a successful explicitly
truncated result, even when the last link repeats or the last page reaches the
page budget. A final page without continuation at the budget is ordinary route
exhaustion. Normal order, overrun handling and per-page release disclosures remain
unchanged. URL equality is exact; no identity or semantic equivalence is inferred
from related query strings. Fixtures keep their declared subset semantics.

The 100-page ceiling permits sparse responses while giving distinct empty chains
a finite limit. Shared retries are separate: with the current two transient and
two unreadable-body retries, a logical page may consume at most nine transport
attempts. Therefore the native client makes at most 900 transport attempts per
member operation under this policy. Per-attempt timeouts and retry waits are not
a strict wall-clock deadline. Archive reuse/replay retains original bytes and
times with zero new network attempts; failed pagination remains a failure there.

No public argument, stored card field, schema version, scientific source identity,
fixture bytes or published artifact changes. Broader OMA/gnomAD/derived operation
coverage remains #108; installed-artifact and human scientific acceptance remain
separate.

## Verification

Local qualification passes: 322 selected cases in 18.33 seconds and all 5,984
local-original cases in 171.92 seconds with twelve receptor workers on Python
3.14.7. Thirteen expected fixture warnings remain; fatal SQLite/unraisable guards
pass. Ruff, unchanged 1,627-path card shape/schema, source registry, fixture
delivery, dependency preflight, governance/canonical guide equality, warning-fatal
Sphinx, 140 relative file links and whitespace checks pass. Exact-source CI
qualification is pending. The public fixture/synthetic module adds 21 cases
for empty/nonempty single/multiple-URL cycles, distinct empty/nonempty chains at
the real and reduced budgets, row-ceiling precedence, exact-boundary exhaustion,
transient/nested unreadable-body retries, failed card support and original archive
reuse/replay. Existing later-page failures also check logical request counts.
No new provider queries or private fixtures are involved.

## Acceptance criteria

Cycles and distinct empty chains terminate before another request exceeds policy.
Normal native order, the member ceiling and original attribution/replay behavior
remain intact. Failed enrichment creates no partial SourceAssertions. Applicable
local gates and exact-source CI pass; published artifact qualification stays separate.
