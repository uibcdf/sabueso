---
summary: Open the exact original ligand, assembly, chain and author-numbering declarations of an experimental or literal structure item.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-27
verification: selected_offline_qualification
area: [human-exploration, navigation, saved-reading]
---

# Original structure declaration context

An experimental `view("structures")` item, a literal `has_structure` relationship
item or its exact `qualifiers` item now offers original structure, ligand, assembly,
chain and author-numbering destinations through `related()`. This also continues
the instance-to-parent route: inspect that parent's qualifiers to open its fields.
The separate object link still addresses an explicitly supplied Card and preserves
missing context or revision ambiguity. It does not substitute for the local record.

## Scientific scope and original reading

`structure_declaration_context_links@1` binds each destination to one exact typed
relationship location in the focal captured protein. Experimental admission uses
the original `structure_exploration@1` support's relationship location, never a
PDB-label search or metadata lookalike. Literal admission requires that original
focal `has_structure` subject. Source support remains at relationship level; every
retained source, alternative, conflict and physical unit stays available.

The four field links expose `declaration_state`: `retained`, `retained_empty`,
`retained_null`, `unrecognized_shape`, `not_retained` or
`unrecognized_parent_shape`. Existing malformed/null/empty nodes are inspectable;
a missing node has no fabricated location. Missing-field/source guidance concerns
that original snapshot rather than suggesting an unrelated destination Card.
Earlier navigation namespaces retain their original wording and semantics.

No ligand/assembly assignment, residue projection, atom coverage, biological
relevance, identity merge, acquisition or scientific recalculation is performed.
Compact literal reading addresses the same destinations with bounded pages.
No stored Card schema, migration, provider, dependency or shared contract changes.

The independent saved verifier checks original source admission, all complete link
decisions, input/focal captures and actual originating experimental focus or literal
detail. Freshly identified/sealed substitutions of another valid field or origin
are refused. Existing formats remain unchanged. A genuine synthetic old-codec
capsule from `9d5bd09`, actual SDK117, proves that older files keep their original
links without backfill; production method and hashes are in the test-data README.
Frozen helpers and policy must retain their meaning for future saved readers.

## Qualification and follow-up

Owning cases cover public P52270 plus explicit synthetic duplicate/foreign/missing/
null/empty/malformed contexts, separate supplied revisions, original support and
capture isolation, compact access, no science rerun, independent inert @1/@2
reading, semantic substitutions, repeat-save stability and genuine historical
compatibility. Source-bound gate results belong to #148/#112. Local success does
not qualify a remote OS/Python/installed matrix.

A new observed defect is recorded in [#168](https://github.com/uibcdf/sabueso/issues/168):
reference-only native inventory explanations crash when two retained relationships
share one PDB label. This block tests their exact **literal** navigation separately;
it does not claim experimental duplicate-reference support. Correct that ambiguity
without rewriting historical explanations before broad structural acceptance.
Then continue the [completion inventory](card_exploration_completion_0150.md),
including scientific region/site/model/assembly integration and actual researcher/
workload acceptance. This source-field navigation is not an assembly-aware
scientific reconciliation or completion of the broad pre-0.15.0 experience.

Owned proof: `recovered_work/structure_context_148_20261027/`, owner #148/#112;
review at the next structural checkpoint or before 0.15.0 acceptance. Tests run
serially through the receptor under explicit owned-RSS/free/available-RAM/swap
stops. Retain original inputs/capsules and useful qualification; remove completed
owned scratch after its last needed use. Hosted qualification follows the
[intermediate recovery ledger](deferred_ci.md); release consolidation stays paused.

The selected Card/native/history/argument/quantity integration passes **1,198
cases /590.53s** across 40 files, serial through pytest-receptor with explicit
local-source inputs and fatal runtime/SQLite/unraisable guards. This includes the
20 owning cases; overlapping focused checks are not additional unique coverage.
Sampled owned RSS peaks at **773 MiB** with at least **7.2 GiB genuinely free host
RAM**, and no resource stop. Three declared warnings concern fixture UniChem
failures and the public STRING cut. The initial experimental duplicate-reference
failures are retained as #168 observations, not passing qualification.

The new public guide block executes on a fresh unchanged public Card without
queries; all 54 snippets receive syntax checks, without claiming a complete
accumulated walkthrough rerun. Applicable Ruff, Python 3.11 parsing, local Markdown
link, fixture-delivery (51 public/37 protected originals) and local governance
checks pass. Warning-fatal Sphinx and final editable-label checks have their own
source-bound receipts in #148/#112. Hosted OS/Python/installed and coverage checks
remain deferred for this intermediate runtime; no previous green CI is attributed
to it. The final exact source and recovery route are recorded in the owning issues.
