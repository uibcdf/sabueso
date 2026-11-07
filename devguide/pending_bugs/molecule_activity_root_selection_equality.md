# Molecule root return conflates equal numeric display operands

Owner: Sabueso #148/#112. Status: confirmed on the current LIVE implementation;
unfixed. An exact public issue-update draft is retained internally for maintainer
approval. This report does not extend permission for earlier approved updates.

## Observation

Create two target-grain molecule activity filters in one explorer: first with
`{"value": 33, "unit": "micromolar"}`, then with a PyUnitWizard quantity of 33
micromolar. Both select the same scientific row and have the same semantic view
handle. The second filter records a JSON operand with floating value `33.0`.
Opening its `molecule_root` link returns the earlier filter, whose recorded
operand has integer value `33`.

The LIVE return predicate compares `_selection_binding(candidate)` with Python
dictionary equality. Python considers these numbers equal. Canonical JSON keeps
their original types distinct. The result is an observable loss of the initiating
display-request detail; it does not change scientific membership, quantities,
source assertions or native crossing results. This is a Sabueso navigation issue,
not an observed PyUnitWizard provider defect.

## Evidence and limits

The immutable SDK211 original already contains this behavior. Its quantity
journey returns node `N35` from the PyUnitWizard target filter; the returned
display records integer `33`, while the originating navigation binding records
floating `33.0`. Both values remain unchanged in the
[complete original capsule](../../tests/core/data/README.md#corrected-quantity-display-live-original-sdk211).

A separate bounded LIVE probe repeats it under editable SDK212 at `9c29eb4`,
using the unchanged public 493-record target. It records one target activity
evaluation, identical scientific payloads, unchanged input Cards, zero network
and acquisition attempts, and zero owned swap. Its source hash and observations
are retained at
`recovered_work/checkpoint_recovery_20261106/b5-molecule-root-selection-probe-1/`.
The probe takes 2.52 seconds at 163,672,064 bytes peak owned RSS. It is a focused
observation, not a broad test qualification.

The independent original human-binding helper explicitly retains the producer's
`molecule_activity_root_selection_python_equality@1` interpretation, including this
limitation. A regression checks both original operand types without rewriting
the capsule or substituting a corrected original. This historical consistency
check is not a correction of current LIVE behavior.

## Proposed follow-up

Bind future LIVE returns to the initiating display request with its original
types, or to an explicit retained instance identity. Qualify coexisting JSON-node
and PyUnitWizard requests, no-op filters, duplicate semantic handles and their
actual back histories. Preserve original saved interpretations under their
versioned predicates; do not silently normalize old operands or regenerate
originals. The exact rule/version and regression scope remain implementation
work under #148, before claiming complete saved navigation.
