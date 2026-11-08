"""Independent SDK224 clinical expectations and retained original restoration."""

from ._clinical_history_v1.adapter import ADAPTER as ADAPTER
from ._clinical_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._clinical_history_v1.adapter import TOPIC as TOPIC
from ._clinical_history_v1.adapter import ClinicalResult as ClinicalResult
from ._clinical_history_v1.adapter import defer_frame as defer_frame
from ._clinical_history_v1.adapter import descriptor as _descriptor
from ._clinical_history_v1.adapter import materialize
from ._clinical_history_v1.adapter import options_for_clinical as options_for_clinical
from ._clinical_history_v1.inputs import DEFAULT_PRODUCER, _FrozenAccess, producer
from .card_access import _Entry
from .errors import StorageError
from .snapshot import canonical_json


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def expected_result(access, options=None, *, original=None):
    """Use frozen rules on captured data; only a declared generated rule labels it."""
    options_for_clinical(options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("coverage", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"] != "knowledge_state@5"
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError("Unsupported original clinical generated coverage rule.")
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), options)


def verify_result(access, ref, wire):
    expected = expected_result(access, wire["context"]["options"], original=wire)
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved clinical result differs from its original native/source/request binding."
        )


def restore_result(ref, wire):
    """Restore original order; validation never replaces the retained wire."""
    options_for_clinical(wire["context"]["options"])
    native, rows = wire["native_payload"], wire["rows"]
    keys = ["molecule_phase"] if "molecule_phase" in rows else []
    for index, indication in enumerate(native["indications"]):
        keys.append(f"indication:{index}")
        keys.extend(
            f"citation:{index}:{position}"
            for position in range(len(indication["trials"]))
        )
    keys.extend(f"registry:{index}" for index in range(len(native["trials"])))
    if len(keys) != len(rows) or set(keys) != set(rows):
        raise StorageError(
            "Original clinical rows differ from native membership/order."
        )
    shell = ClinicalResult(ref, wire, (), {})
    return ClinicalResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        {},
    )
