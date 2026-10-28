---
summary: Open the exact original structure declaration containing a ligand instance without requiring a separate structure Card.
issue: uibcdf/sabueso#148
status: open
opened: 2026-10-27
verification: selected_offline_qualification
area: [human-exploration, navigation, saved-reading]
---

# Original parent structure from a ligand instance

An item in `answer("structure_ligands")` / `view("ligand_instances")` now offers
**Original structure declaration** through `related()` with role
`structure_context`. Opening it inspects the exact captured relationship that
contains the instance, including its original qualifiers, units, alternatives and
relationship-level support. Its existing source, subject and object links remain.

This closes an observed navigation gap: the parent was present in support, but the
separate object-Card link correctly reported `context_not_supplied` when no PDB
Card had been supplied. That link keeps its original meaning. A supplied object
Card, multiple supplied revisions and the local parent are separate destinations.

## Admission and original reading

`ligand_instance_context_links@1` is a frozen navigation policy over the existing
`ligand_instances_fields@1` membership. It uses the typed instance occurrence and
its actual parent relationship location, never a search by PDB/component/instance
label, a new identity merge, contact mapping or assembly correspondence. Foreign
subjects are not admitted. Duplicate labels keep their original indices and
histories; empty instances and conflicting qualifiers remain inspectable.

Human following and compact literal access use the same captured destination.
`back()` preserves the actual intervening detail/link/filter trail. Browsing does
not query a source, construct another scientific Card or run a scientific reader.
Repeated saving without further exploration preserves identical bytes.

The independent verifier checks original membership, capture/input scope, complete
source/endpoint/parent decisions and the originating instance detail. A freshly
identified, consistently rendered and sealed link to another valid retained parent
is refused against the original instance, even when labels match. Swapped related
operations between identical instances are also refused. Hashes establish internal
consistency, not source authenticity or truth.

Existing formats and frozen `retained_context_links@1/@2/@3/@4` keep their meaning.
Older files without this new navigation are not backfilled. The small synthetic
legacy capsule in `tests/core/data/` is produced by exact original codec bytes
from `9696fbc`, SDK116, with the method/hashes recorded in its README and owning
receipt. It contains no scientific source or private/pilot material and does not
freeze a Card schema. Current independent reading forbids Card construction,
fixture access, network access and live navigation/resolution helpers.

No stored Card schema, source registry, native scientific rule, dependency
requirement or cross-component contract changes.

## Qualification and next work

The owning tests cover public P52270, clearly synthetic duplicate/foreign/empty/
conflicting cases, captured-input isolation, separate supplied-Card/revision scope,
bounded literal access, original saved reading, semantic parent substitution,
related-operation origin and historical compatibility. Broader Card/access/
navigation/native/quantity/argument gates and documentation checks have separate
source-bound receipts in #148/#112; local success never implies remote success.

This is one structural transition, not completion of the broad profile or actual
researcher acceptance. Fragment/isoform coordinate admission, region/site/model/
assembly reconciliation, other scientific panels and workload budgets remain in
the [completion inventory](card_exploration_completion_0150.md). The
[persistence review](card_persistence_cost.md) stays open; no latency or size
reduction is claimed by adding this link.

Owned proof: `recovered_work/ligand_parent_navigation_148_20261027/`, owner #148/#112,
review at the next structural checkpoint or before 0.15.0 acceptance. Retain useful
source-bound receipts and original capsules; remove only completed owned scratch.
Tests run serially with successful-function temporary cleanup and explicit owned
RSS/free-RAM/available-RAM/swap stops under the current host-memory constraint.

Selected integration passes **1,178 cases /577.68s** across 39 Card/native/history/
argument/quantity/accounting files, serial through pytest-receptor with explicit
local-source inputs and fatal runtime/SQLite/unraisable guards. Sampled owned RSS
peaks at about **810 MiB**, with at least **5.6 GiB genuinely free host RAM** and no
resource stop. Three declared warnings are the fixture UniChem failures and public
STRING cut. The focused instance/parent gate passes 38 cases /34.84s; it overlaps
the integration scope and is not added as unique coverage.

The changed public-guide block executes on a fresh public Card/explorer without
queries or mutation. All 53 snippets pass syntax checks; this does not claim
rerunning the complete accumulated walkthrough. Warning-fatal Sphinx, Ruff format/
lint, 167 local Markdown targets, Python 3.11 parsing of five changed Python files,
fixture delivery (51 public/37 protected originals) and local governance pass.
The checked intermediate source and subsequent exact editable-label checks are
recorded in #148/#112. Hosted qualification remains deferred under the
[intermediate recovery route](deferred_ci.md); the earlier code checkpoint's green
CI does not qualify this new source automatically. 0.15.0 consolidation stays paused.
