---
summary: Shared live human and compact agent exploration of assembly-generation findings.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-30
verification: owning_offline_qualification
area: [human-exploration, agent-access, structural-context]
---

# Assembly components and operations

`explorer.answer("assembly_generation")`, `view(...)` and
`explorer.access.select("assembly_generation")` share one captured native
`rcsb_assembly_generation@4` result per normalized request, under
`assembly_generation_exploration@1`. Browsing never fetches, refreshes the caller
or changes stored knowledge. The [native contract](rcsb_assembly_generation.md)
owns scientific interpretation; this adapter presents its original findings.

## Scientific grains and readable navigation

Each generator is a separate row with original assertion, parent/generator
positions and native identity scope. Missing/null/empty/unrecognized source or
parent collections, unplaced declarations and missing RCSB inputs have their own
rows. Counts describe source component-position × operation-tuple declarations,
including repeats; no distinct physical copy, geometry, assembly contact or
biological relevance is inferred.

Protein topics/questions include **Assembly components and operations**. The
table uses readable plan/key states, declared combinations and reasons. `open()`
keeps the complete native finding and a labeled bounded preview of expression
and component bindings. `explain()` retains named rules, exact request, source
membership and original input/context destinations. `related()` opens sources,
structure declarations, generator inputs, complete native source context and
acquisition/quality records. Missing source members remain unavailable links.
Every step keeps its actual `back()` origin. Complete values remain available
through `rows()`, `native_payload` and typed read locations.

`declaration_count` is a nullable scalar. A `factored` cell has complete exact
factors and their read location, not an unknown or zero count. Non-generator
rows use `not_applicable` count cells. Display selection can distinguish these
states explicitly.

## Exact requests and compact agent access

Options are exact `structure_ref`, optional `relationship_id` requiring that
reference, strict `expand_operations`/`expand_occurrences` booleans, and positive
non-boolean `operation_budget` or explicit None. Defaults retain compact plans
with a 100,000-work ceiling. Native admission and whole-request count/text
preflight remain authoritative. Invalid selectors/options and typed display
operands fail before scientific work, including empty captures. Normalized
options stay in both human question requests and machine context.

`assembly_generation_access_selection@1` defines exact equalities, unique item
membership and stable scalar ordering with missing values last. Counts accept
nonnegative integers or None, never booleans, floats or quantities. Nullable text
columns accept None; other columns take strings. None matches an unavailable
scalar representation; use `count_state` to distinguish factored, unavailable
and non-applicable counts. Filtering changes display membership, not the native
result or its sources. Foreign item references cannot be rebound by equal labels.

Projected pages retain named rules, original context, count basis/state,
component/operator scope, physical limits and source-ID membership or complete
typed read paths. `assembly_generation_support_membership@1` binds IDs to the
captured source store. Oversized values are deferred together with mandatory
interpretation/support; inspection locations remain. Limits, cursors and framing
stay shared with existing access. No optional dependency or source query is added.

## Persistence and remaining work

The [original assembly reader](card_saved_assembly.md) now supports saving this
view, exact machine selections and derived navigation under explicit exploration
format @5. A session retaining the [exact structure-to-assembly question](card_structure_assembly_navigation.md)
uses explicit @6 for that additional original navigation contract; scientific
assembly findings keep their existing rules. Captured Card export remains available. Genuine older scientific files
return `not_saved` for this topic without current scientific execution. Original
scientific/native modules and previous saved formats remain unchanged.

Full nonpolymer/physical-occurrence and assembly-contact
scope remains explicit in #173. Researcher acceptance and workload qualification
remain separate in #148. The [complete inventory](card_exploration_completion_0150.md)
governs pre-0.15.0 delivery; consolidation and release stay paused. Source-specific
local/hosted receipts belong to #148/#173/#112; intermediate hosted debt follows
the [recovery ledger](deferred_ci.md) and must be recovered before route completion.

## Local qualification

The preceding live-only slice (2026-10-30, `77fd770`) passes 34 new exploration cases and all 152 native
owning cases. The final 40-file integration passes **1,223 cases /565.15 seconds**
across four serial pytest-receptor invocations, including those 186 cases, with
fatal runtime/SQLite/unraisable guards. Peak sampled owned RSS is 890,834,944
bytes, minimum host available RAM 16,294,400,000 bytes and owned swap zero. The
groups use a 1 GiB owned ceiling, 4 GiB available and 256 MiB genuinely free host
floors. Earlier catalog-expectation failures and an all-in-one free-RAM guard stop
remain separate diagnostic receipts; they are not passing qualification.

All six public guide blocks execute on three retained public controls and a
historical Card, without acquisition or mutation. All 49 protected original
modules remain byte-identical to `a1a5436`. Pinned whole-tree Ruff, warning-fatal
Sphinx, local links/snippets/Python 3.11 parsing, unchanged shape/schema, source
registry, fixture delivery, dependency and governance checks pass. Exact source,
editable SDK and final owning receipts belong to #148/#173/#112 and the owned
`recovered_work/assembly_exploration_148_20261030/` checkpoint, reviewed at the
independent original-reader block or before 0.15.0. These selected local checks
do not establish a full-suite, hosted, researcher or release qualification.
