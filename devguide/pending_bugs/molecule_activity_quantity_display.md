---
summary: Preserve declared PyUnitWizard display quantities in serializable molecule navigation requests.
issue: uibcdf/sabueso#148
status: open
opened: 2026-11-07
closed:
verification: reproduced
area: [exploration, quantities, source-navigation]
blocked_by: []
supersedes: []
---

# Quantity display filters lose original source navigation

At clean `75a7533` / SDK210, the public molecule activity profile accepts a
PyUnitWizard concentration operand and selects the same row as its explicit
value/unit node. Calling `filtered.items()[0].related()` then raises
`TypeError: Object of type Quantity is not JSON serializable`. The matching JSON
quantity-node control opens the full source trail. Public TcTIM/BTS data retain
all 493 target records; inputs stay unchanged and the guarded probe records zero
network/client-construction attempts.

The selected column's `quantity_node` contract explicitly accepts PyUnitWizard
quantities. `display_filter` validates that quantity but stores the raw object in
`_display_request.equals`. `_navigation` copies it into the original selection
binding; the generic literal-metadata identity requires canonical JSON.
This is a Sabueso boundary defect. No PyUnitWizard/provider defect is established.

Six permanent regressions fail on the original TypeError across target, group and
record grains, with ordinary or skipped argument digestion. They check actual
source/back/publication/native crossings, unchanged full inputs and shared target
evaluation. The correction converts only a non-dictionary PyUnitWizard operand
to its explicit finite value/unit node before storing the generated display
request. Existing JSON operands keep their original types and units. Scientific
values, source statements, policies, Card schema, frozen predicates, original
capsules and formats @1–@20 stay fixed.

The initial probe, both operand observations and complete six-case red gate are
retained under `recovered_work/checkpoint_recovery_20261106/b5-molecule-quantity-display-*`.
The [735-case selected correction](../evidence/molecule_activity_quantity_display_checkpoint_20261107.json)
passes all 60 LIVE cases, 291 shared, 383 native/profile and one copied outer case.
The 60 copied child cases and six focused repeats add no distinct coverage.
Complete receptor/source/node/resource checks pass with zero owned swap and two
expected offline UniChem warnings. Keep this evidence under #148/#112 through
full original saved-reader and source/origin receiving. This finding is separate
from the corrected cross-focal cache and unfixed #192 flag aggregation.

The exact approved preparation-time report is
[published in #148](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6712960392).
Its body, SHA-256, authorization and returned-body equality receipts remain in
the local recovery tree. Later qualification results were not appended to that
approved material; this maintained report records the current correction scope.
