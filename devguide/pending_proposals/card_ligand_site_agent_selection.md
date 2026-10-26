---
summary: Compact exact agent selection shares the human ligand-site comparison result and original support.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-26
verification: selected_tests_pass
area: [agent-access, scientific-views, human-exploration]
---

# Compact ligand-site comparison selection

`explorer.access.select("ligand_site_comparisons", fields=None, where=None,
item_refs=None, order_by=None, options=None)` shares the human pane's captured
native result, original explanations and result/item identities. Either entry
order evaluates science once. The cache belongs to the access context, keyed by
adapter and focal capture; no second scientific engine, source access or Card
recapture is introduced. Human rows use those same original entries.

## Exact economical requests

Default columns are `ligand_ref`, `comparison_status` and native `site_class`.
Optional textual columns are `label`, `kind`, readable `outcome`, `matched_sites`
and `reason`. A selected cell is present as a retained result field; a present
`comparison_status="not_computed"` does not claim a computed comparison.

`ligand_site_access_selection@1` is a display policy, not derived knowledge:

- `where` is AND over exact declared string values. Numeric, boolean and null
  operands never become strings. Invalid types, options, columns and ordering
  units fail before native calculation, also with digestion skipped.
- `item_refs` is exact result membership. Foreign/duplicate refs fail; an empty
  list selects no rows. Caller order never substitutes for explicit ordering.
- `order_by` admits a textual column and optional boolean `descending`; units
  are inapplicable. Equal keys retain the original ligand-reference/relationship
  ordering. Scientific options are empty.
- Restricted selections bind the versioned policy, original result, projection,
  effective request, ordered members, counts and display exclusions. Unrestricted
  handles use the existing result-bound `scientific_access_selection@1` format.
  An empty display selection preserves the underlying operation outcome.

The topic catalog advertises actual columns, defaults and capabilities without
running scientific readers. `selection(ref)` returns an already retained request;
`explain(item_ref)` reads its original explanation without calculating again.

## Mandatory scope, support and bounded delivery

Even a zero-column projection retains comparison status/basis, compared and
uncomputed annotation indices, original contact scope, classification/scope rules
and the declaration grain. Annotation contexts are not independently identified
physical sites. Partial positives, uncomputed scope and unstated revision agreement
remain explicit; projection never makes unknown results negative.

Inline items carry actual declared relationship subjects, source membership and
exact support/explanation/value locations. The delivery continuation uses
`ligand_site_support_membership@1`: every original member ID/state stays inline,
with one exact captured `source_store_location`. A present member appends a
`Record(id)` segment to that container; missing members have no destination.
The complete original per-source locations remain at `support_location`. This
transport format introduces no source assertion or new scientific classification. Source-request coverage is referenced
and explicitly not evaluated by this adapter. Atomic deferral removes values and
their interpretation/support closure together, preserving states and inspectable
locations. The complete canonical UTF-8 JSON envelope, including cursors and
mandatory metadata, stays within the requested byte bound. Native Card quantities
remain at original locations with their existing unit bindings.

## Historical reading remains a required next block

Saving this scientific result or a navigation closure originating from it remains
unavailable. Existing original saved formats/readers are unchanged. Saved sessions
advertise this topic as `not_saved`; selection does not execute installed science.
This is an explicit remaining implementation requirement, not a release exception.

The next block must introduce an explicit new saved format/capability dispatch
without changing @1/@2 meanings. Its immutable verifier must bind canonical
coordinate admission, overlap @3, explanations, original source closure, human
display and agent policy decisions, plus related-operation origins. It must read
independently with current Card constructors, scientific readers, source clients
and sockets forbidden. Preserve genuine previous producer capsules and refuse
coherently edited/rehashed results, support, qualifiers, selected membership and
navigation origins. A common JSON digest alone cannot supply those guarantees.

Assembly reconciliation, region/model transitions, remaining nature-specific
panels, agreed workloads and actual researcher acceptance stay in the
[complete pre-0.15.0 inventory](card_exploration_completion_0150.md).

## Qualification and retained resources

Qualification receipts belong to #148/#112 and the owned local evidence directory
`recovered_work/site_agent_148_20261026/`, with review trigger next exploration
checkpoint or release acceptance. Selected, full and exact-source remote gates
are distinct; pending runs are not passing evidence. No new scientific requests,
private pilot content, stored Card schema, scientific rules or shared MOLI
contracts are introduced. No release/tag or consolidation is authorized by this
bounded selector delivery.


Current local qualification passes **830 cases /88.85 seconds** with twelve
pytest-receptor workers, verified local originals and fatal runtime/SQLite/
unraisable guards. This includes 26 new agent cases, native comparison scope and
genuine original saved producers. The earlier same-scope run passes 830/87.71s;
the final run additionally verifies explanation access from human items before
machine selection and unrelated saved-source admission after machine use.
All 39 public guide blocks execute offline with original inputs unchanged.
Ruff (1,147 Python files), schema/shape 1,938, fixture policy 51+37, source registry,
dependency preflight, governance, 275 local Markdown targets/anchors, 39 Python
snippets/7 Python 3.11 source parses and warning-fatal Sphinx pass. The preceding
7,226 full-suite and exact-source remote receipt belongs to `b6bdb7f`, not to this
later selector source. A broader full/remote checkpoint is still due for the
accumulated implementation block; no researcher or release acceptance is claimed.


## Measured source-path delivery continuation

The initial selector's public six-row pages repeated full captured Card paths for
every support member. [The reported observation](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6428058678)
found default pages of 61,187/56,653 bytes; 8 KiB pages deferred values. An initial
lookup-per-source prototype reduced repetition but left a historical row deferred.
The versioned common-store membership above now keeps all original IDs/states,
complete interpretation, units and direct source access while removing duplicate
source paths. New tests reconstruct every original location and check exact bytes,
all rows across small pages, original uncertainty, absent members, capture isolation
and the absence of repeated scientific execution. Original scientific results,
selection policy and saved @1/@2 readers are unchanged.

In one local observation on each same public input, complete default pages fall to
**32,354/31,705 bytes** (47.12%/44.04% less). At 8 KiB each first page delivers one
complete record, about 6.5 KiB, rather than two deferred records. These are scoped
byte observations, not tokenizer counts, universal workload budgets or scientist
acceptance. Preserve record/byte limits and atomic deferral for larger inputs.
The next required implementation remains immutable original saved comparison
reading; broader populated/topic costs and the complete 0.15.0 inventory stay open.


The delivery integration gate passes **835 local-original cases /84.78 seconds**
with twelve receptor workers and fatal runtime/SQLite/unraisable guards. Its final
owning gate passes **58 cases /4.39 seconds**, including a later focal/related
revision isolation guard; the new delivery file adds six regressions. These
selected results do not substitute for the accumulated source's full/remote
checkpoint. Its owner remains #148/#112; evidence is retained at
`recovered_work/site_delivery_148_20261026/`, reviewed at the next exploration
checkpoint or release acceptance. No scientific queries or private pilot reads.


**Saved-reading continuation, 2026-10-26:** the
[original comparison reader](card_saved_ligand_site_comparisons.md) supersedes this
initial delivery's unsavable limitation. It adds explicit @3 scientific/source/
request/navigation verification and preserves @1/@2. Missing/unvisited requests
remain `not_saved`; broader profile/workload/researcher acceptance stays open.
