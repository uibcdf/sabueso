# Molecule root return conflates equal numeric display operands

Owner: Sabueso #148/#112. Status: confirmed on the current LIVE implementation;
unfixed. The exact separately approved report is
[published in #148](https://github.com/uibcdf/sabueso/issues/148#issuecomment-6713763040).
The returned body matches the reviewed draft byte for byte. Its authorization,
payload and response receipts are retained internally; this permission covers
that concrete report only.

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

An isolated process-only prototype now binds the return to the actual initiating
target view in the origin chain, verifies retained-instance membership and exact
canonical selection binding, and preserves its typed display request. Four
comparison cases use both creation orders of JSON integer and PyUnitWizard float
operands. Current LIVE loses the second request's type in either order; the
prototype preserves both original requests, scientific payload and back route.
Each case evaluates the target once, with unchanged inputs and zero network or
acquisition attempts. The supervised experiment takes 8.05 s at 245,923,840 bytes
peak RSS and zero swap; all 1,169 protected source hashes stay unchanged.
Evidence is retained in `b5-root-return-prototype-1` under
`recovered_work/checkpoint_recovery_20261106/`, owned by #148/#112 until the
versioned correction is implemented and qualified. This is not a production fix,
new genuine original or saved-reading qualification; the status remains unfixed.

Bind future LIVE returns to the initiating display request with its original
types, or to an explicit retained instance identity. Qualify coexisting JSON-node
and PyUnitWizard requests, no-op filters, duplicate semantic handles and their
actual back histories. Preserve original saved interpretations under their
versioned predicates; do not silently normalize old operands or regenerate
originals. The exact rule/version and regression scope remain implementation
work under #148, before claiming complete saved navigation.

Before changing LIVE, preserve a representative genuine @21/@22 saved control
from the next clean qualified producer. Current original-file writer helpers
reenact UI operations through LIVE functions; a corrected return must not be
used to regenerate SDK211's historical expectation. Keep that older meaning
under explicit original predicates and qualify a separately versioned new
interpretation against its own clean LIVE original.
