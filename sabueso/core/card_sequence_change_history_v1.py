"""Independent SDK234 input consistency and literal original result restoration."""

from copy import deepcopy

from ._sequence_change_history_v1.adapter import ADAPTER as ADAPTER
from ._sequence_change_history_v1.adapter import (
    KINDS,
    SequenceChangeResult,
    materialize,
)
from ._sequence_change_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._sequence_change_history_v1.adapter import TOPIC as TOPIC
from ._sequence_change_history_v1.adapter import defer_frame as defer_frame
from ._sequence_change_history_v1.adapter import descriptor as _descriptor
from ._sequence_change_history_v1.adapter import (
    options_for_changes as options_for_changes,
)
from ._sequence_change_history_v1.inputs import _FrozenAccess
from ._sequence_change_history_v1.rules import DEFAULT_PRODUCER, producer
from .card_access import _Entry
from .errors import StorageError
from .snapshot import canonical_json


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def expected_result(access, options=None, *, original=None):
    """Compute private expectations; never replace original retained knowledge."""
    options_for_changes(options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("native_payload", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"] != "sequence_change_projection@1"
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError("Unsupported original sequence-change rule label.")
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), {})


def verify_result(access, ref, wire):
    expected = expected_result(access, wire["context"]["options"], original=wire)
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved sequence-change result differs from its original input/source binding."
        )


def restore_result(ref, wire):
    """Restore original Card occurrence order; do not calculate scientific results."""
    rows = wire["rows"]

    def ordinal(key):
        kind, index = key.rsplit(":", 1)
        if kind not in KINDS or not index.isdecimal() or str(int(index)) != index:
            raise StorageError("Unsupported original sequence-change occurrence key.")
        # The original annotation reader scans field names in lexical order.
        return kind, int(index)

    keys = sorted(rows, key=ordinal)
    shell = SequenceChangeResult(ref, wire, (), {})
    return SequenceChangeResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        deepcopy(options_for_changes(wire["context"]["options"])),
    )
