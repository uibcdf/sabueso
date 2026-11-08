# Molecule root return conflates equal numeric display operands

Owner: Sabueso #148/#112. Status: LIVE correction passes its selected local
checkpoint; the new independent saved binding remains open. The exact separately approved report is
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

The pre-fix LIVE return predicate compares `_selection_binding(candidate)` with Python
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

## Prototype and original follow-up

An isolated process-only prototype now binds the return to the actual initiating
target view in the origin chain, verifies retained-instance membership and exact
canonical selection binding, and preserves its typed display request. Four
comparison cases use both creation orders of JSON integer and PyUnitWizard float
operands. Pre-fix LIVE loses the second request's type in either order; the
prototype preserves both original requests, scientific payload and back route.
Each case evaluates the target once, with unchanged inputs and zero network or
acquisition attempts. The supervised experiment takes 8.05 s at 245,923,840 bytes
peak RSS and zero swap; all 1,169 protected source hashes stay unchanged.
Evidence is retained in `b5-root-return-prototype-1` under
`recovered_work/checkpoint_recovery_20261106/`, owned by #148/#112 until the
versioned correction is implemented and qualified. That process-only experiment
is not a production fix, genuine new original or saved-reading qualification.

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

That pre-fix file is now captured from clean `a759b1d` / SDK216. Its complete
96-view/six-request journey passes fresh inert receiving, and the
[frozen control](../../tests/core/data/README.md#genuine-pre-fix-saved-molecule-control-sdk216)
retains all actual instances and writer node mappings. It is a compatibility
control for the old meaning, not adoption of the process-only correction.

## Current implementation

LIVE `molecule_activity_root_selection_exact_origin@1` follows the actual origin
chain, requires the exact retained instance and explorer, and compares canonical
typed selection bindings. Equal semantic handles no longer choose another
instance. Four positive cases cover both operand orders and repeated no-op
displays; three refusal cases cover missing retention, a foreign instance and
an operand-type substitution. Together with machine-first save refusal, the
focused eight-case gate passes in 12.91 s pytest / 14.08 s guarded, at 175,153,152
bytes peak RSS, zero warnings/swap and 1,170 stable source/input hashes.

New LIVE saving reports unavailable until its own independent binding is ready;
it cannot silently serialize the new interpretation as the older Python-equality
policy. The descriptor states the reason. Existing @21/@22 reading and resaving
remain available; historical reenactment helpers explicitly retain the SDK216
root-return branch and original policy. The scientific result schema, source
assertions, native quantities and earlier capsules are unchanged.

The [515-case selected checkpoint](../evidence/molecule_activity_root_exact_live_checkpoint_20261107.json)
passes all 68 LIVE cases, 443 adjacent cases and four genuine-file compatibility
controls, with complete receptor/source accounting and zero warnings/swap.
Clean `b1bbfaa` / SDK218 now supplies
[two complete originals](../evidence/molecule_activity_root_exact_original_20261107.json),
one for each operand creation order, before implementing the new independent
saved interpretation. Next qualify that reader, restore new LIVE saving and
qualify complete source/back/machine, semantic refusal, transport and copied
receiving. No new saved-format admission or acceptance is claimed here.
