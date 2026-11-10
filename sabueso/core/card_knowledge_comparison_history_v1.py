"""Independent SDK243 typed comparison consistency and literal result restoration."""

from copy import deepcopy

from ._knowledge_comparison_history_v1.adapter import ADAPTER as ADAPTER
from ._knowledge_comparison_history_v1.adapter import (
    KnowledgeResult,
    materialize,
    options_for_comparison,
)
from ._knowledge_comparison_history_v1.base import defer_frame as defer_frame
from ._knowledge_comparison_history_v1.inputs import _FrozenAccess
from ._knowledge_comparison_history_v1.rules import DEFAULT_PRODUCER, producer
from .card_access import _Entry, _handle
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

PANEL = "protein_context"
TOPICS = ("comparative_context",)


def coverage(result):
    """State the retained comparison scope without a completeness denominator."""
    return {
        "classification": "not_evaluated",
        "basis": "original_captured_knowledge_comparison",
        "inputs": deepcopy(result.wire["context"]["inputs"]),
        "reason": "Only the explicitly supplied captures and comparison scope are retained; no global knowledge completeness is inferred.",
    }


def options_for_context(topic, options=None):
    if topic not in TOPICS:
        raise ArgumentError(
            "Original knowledge comparison requires comparative_context."
        )
    return options_for_comparison(options)


def expected_result(access, options, *, original=None):
    """Compute only the frozen rule over exact retained input snapshots."""
    options_for_comparison(options)
    version = DEFAULT_PRODUCER
    if original is not None:
        rule = original.get("native_payload", {}).get("rule")
        if (
            not isinstance(rule, dict)
            or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
            or rule["rule"] != "card_knowledge_diff@2"
            or not isinstance(rule["sabueso_version"], str)
            or not rule["sabueso_version"]
        ):
            raise StorageError(
                "Unsupported original knowledge-comparison producer rule."
            )
        version = rule["sabueso_version"]
    with producer(version):
        return materialize(_FrozenAccess(access), options)


def verify_result(access, ref, wire):
    expected = expected_result(access, wire["context"]["options"], original=wire)
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError(
            "Saved knowledge comparison differs from its original typed input/source binding."
        )


def row_keys(native):
    """Preserve original row grains/order, including equal rendered state labels."""
    paths = [("supplied_residue_map", ("residue_map",))]
    paths.extend(
        ("knowledge_field", ("fields", path)) for path in sorted(native["fields"])
    )
    paths.extend(
        ("knowledge_relationships", ("relationships", predicate))
        for predicate in sorted(native["relationships"])
    )
    paths.extend(
        ("knowledge_state", ("knowledge_states", index))
        for index in range(len(native["knowledge_states"]))
    )
    return [
        _handle("K_", {"kind": kind, "native_path": list(path)}) for kind, path in paths
    ]


def restore_result(ref, wire):
    rows = wire["rows"]
    keys = row_keys(wire["native_payload"])
    if len(keys) != len(rows) or set(keys) != set(rows):
        raise StorageError("Original knowledge comparison row grain/order is detached.")
    options = deepcopy(options_for_comparison(wire["context"]["options"]))
    shell = KnowledgeResult(ref, wire, (), options)
    return KnowledgeResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        options,
    )


def descriptor(topic="comparative_context"):
    from .card_protein_context_history_v1 import descriptor as original_descriptor

    result = original_descriptor(topic)
    result["comparison_modes"] = {
        "relationships": {"save": True},
        "sequence": {"save": True},
        "knowledge": {
            "adapter": ADAPTER,
            "native_rule": "card_knowledge_diff@2",
            "save": True,
            "other_ref": "exact supplied protein capture",
            "residue_map": "optional one-to-one positive integer pairs; no alignment performed",
        },
    }
    return result
