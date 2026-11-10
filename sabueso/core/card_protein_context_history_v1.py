"""Independent SDK239 protein-context consistency and literal result restoration."""

from copy import deepcopy

from ._protein_context_history_v1.adapter import ADAPTER as ADAPTER
from ._protein_context_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._protein_context_history_v1.adapter import ProteinContextResult, materialize
from ._protein_context_history_v1.adapter import defer_frame as defer_frame
from ._protein_context_history_v1.adapter import descriptor as _descriptor
from ._protein_context_history_v1.adapter import (
    options_for_context as options_for_context,
)
from ._protein_context_history_v1.inputs import _FrozenAccess
from ._protein_context_history_v1.rules import DEFAULT_PRODUCER, producer
from .card_access import _Entry
from .errors import StorageError
from .snapshot import canonical_json

PANEL = "protein_context"
TOPICS = ("comparative_context", "associations")


def descriptor(topic):
    result = _descriptor(topic)
    result["save"] = True
    result.pop("save_reason", None)
    return result


def expected_result(access, topic, options=None, *, original=None):
    options_for_context(topic, options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("native_payload", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"] != "protein_context_projection@1"
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError("Unsupported original protein-context producer rule.")
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), topic, options)


def verify_result(access, ref, wire):
    expected = expected_result(
        access, wire["context"]["topic"], wire["context"]["options"], original=wire
    )
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved protein-context result differs from its original captured input/source binding."
        )


def restore_result(ref, wire):
    rows = wire["rows"]
    keys = []
    for item in wire["native_payload"]["items"]:
        candidates = [
            key
            for key, row in rows.items()
            if canonical_json(row["item"]) == canonical_json(item)
        ]
        if len(candidates) != 1 or candidates[0] in keys:
            raise StorageError("Original protein-context row grain/order is ambiguous.")
        keys.append(candidates[0])
    if len(keys) != len(rows):
        raise StorageError("Original protein-context rows are detached.")
    shell = ProteinContextResult(ref, wire, (), {})
    return ProteinContextResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        deepcopy(
            options_for_context(wire["context"]["topic"], wire["context"]["options"])
        ),
    )
