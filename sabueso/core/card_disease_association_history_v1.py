"""Independent SDK227 disease association consistency and original restoration."""

import re

from ._disease_association_history_v1.adapter import ADAPTER as ADAPTER
from ._disease_association_history_v1.adapter import RULE as RULE
from ._disease_association_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._disease_association_history_v1.adapter import TOPIC as TOPIC
from ._disease_association_history_v1.adapter import (
    AssociationResult as AssociationResult,
)
from ._disease_association_history_v1.adapter import defer_frame as defer_frame
from ._disease_association_history_v1.adapter import descriptor as _descriptor
from ._disease_association_history_v1.adapter import materialize
from ._disease_association_history_v1.adapter import (
    options_for_associations as options_for_associations,
)
from ._disease_association_history_v1.inputs import _FrozenAccess
from ._disease_association_history_v1.rules import DEFAULT_PRODUCER, producer
from .card_access import _Entry
from .errors import StorageError
from .snapshot import canonical_json


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def expected_result(access, options=None, *, original=None):
    """Compute private expectations from captured inputs, never replacement output."""
    options_for_associations(options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("native_payload", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"] != RULE
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError("Unsupported original disease association rule label.")
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), options)


def verify_result(access, ref, wire):
    expected = expected_result(access, wire["context"]["options"], original=wire)
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved disease associations differ from their original input/identity/source binding."
        )


def restore_result(ref, wire):
    """Keep original row order: each capture's statements, then its context row."""
    options_for_associations(wire["context"]["options"])
    rows = wire["rows"]

    def ordinal(key):
        matched = re.fullmatch(
            r"(statement|context):(0|[1-9][0-9]*)(?::(0|[1-9][0-9]*))?", key
        )
        if matched is None or ((matched[1] == "statement") != (matched[3] is not None)):
            raise StorageError("Unsupported original disease association row key.")
        return (
            int(matched[2]),
            0 if matched[1] == "statement" else 1,
            int(matched[3] or 0),
        )

    keys = sorted(rows, key=ordinal)
    shell = AssociationResult(ref, wire, (), {})
    return AssociationResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        {},
    )
