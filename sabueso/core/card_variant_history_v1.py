"""Independent SDK230 variant/isoform consistency and literal original restoration."""

import re
from copy import deepcopy

from ._variant_history_v1.adapter import ADAPTER as ADAPTER
from ._variant_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._variant_history_v1.adapter import TOPIC as TOPIC
from ._variant_history_v1.adapter import VariantResult as VariantResult
from ._variant_history_v1.adapter import defer_frame as defer_frame
from ._variant_history_v1.adapter import descriptor as _descriptor
from ._variant_history_v1.adapter import materialize
from ._variant_history_v1.adapter import options_for_variants as options_for_variants
from ._variant_history_v1.inputs import _FrozenAccess
from ._variant_history_v1.rules import DEFAULT_PRODUCER, producer
from .card_access import _Entry
from .errors import StorageError
from .snapshot import canonical_json


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def expected_result(access, options=None, *, original=None):
    """Calculate private input-bound expectations, never replacement knowledge."""
    options = options_for_variants(options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("native_payload", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"]
            != (
                "pext_at_variant@2"
                if options["mode"] == "variants"
                else "isoform_exon_usage@3"
            )
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError("Unsupported original variant tissue rule label.")
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), options)


def verify_result(access, ref, wire):
    expected = expected_result(access, wire["context"]["options"], original=wire)
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved variant tissue context differs from its original input/source/scope binding."
        )


def restore_result(ref, wire):
    """Restore original native occurrence order without recomputing any science."""
    options = options_for_variants(wire["context"]["options"])
    rows = wire["rows"]

    def ordinal(key):
        match = re.fullmatch(re.escape(options["mode"]) + r":(0|[1-9][0-9]*)", key)
        if match is None:
            raise StorageError("Unsupported original variant tissue row key.")
        return int(match[1])

    keys = sorted(rows, key=ordinal)
    shell = VariantResult(ref, wire, (), options)
    return VariantResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        deepcopy(options),
    )
