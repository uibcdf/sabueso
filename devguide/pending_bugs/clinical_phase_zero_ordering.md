---
summary: Native indication ordering gives known phase zero and an unknown phase the same primary key.
issue: uibcdf/sabueso#81
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [clinical, ordering]
blocked_by: []
supersedes: []
---

# Known zero and unknown clinical phase ordering

Internal handoff for Sabueso #81, to review during the next B5 clinical increment.
No issue update has been published. The observation uses synthetic records and
does not alter a source assertion or establish a clinical outcome.

`clinical_view()` orders indications by `-(max_phase or -1)`, followed by disease
term and reference. Numeric phase zero and an unknown `None` both receive primary
key `1`. A direct invocation with an unknown-phase term `A unknown` and a
zero-phase term `Z zero` consequently places the unknown row first. Both original
values remain correctly present in the returned rows.

The local reproduction is retained at
`recovered_work/checkpoint_recovery_20261106/b5-clinical-ordering-observation-1.json`.
It exercises the existing native function with a minimal synthetic Card and no
source clients. Prevalence in public inputs and impact on users are unmeasured.
The current full shared-reading checkpoint deliberately retains unchanged code.

Proposed follow-up: distinguish `None` explicitly in the native ordering key and
add a focused zero/null ordering regression when implementing clinical browsing.
Preserve molecule maximum phase, indication phase and registry phase/status as
separate source statements. Offer the concrete observation as an update to #81
at the maintainer checkpoint; retain this handoff until publication is authorized.
