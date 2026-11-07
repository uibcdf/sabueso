"""Original SDK202 literature predicates and retained-result restoration.

Private expected results verify original knowledge; they never replace it. No
Card, current scientific reader, source client or public digester is used here.
"""

from copy import deepcopy

from ._literature_history_v1.adapter import ADAPTER as ADAPTER
from ._literature_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from ._literature_history_v1.adapter import TOPIC as TOPIC
from ._literature_history_v1.adapter import LiteratureResult as LiteratureResult
from ._literature_history_v1.adapter import defer_frame as defer_frame
from ._literature_history_v1.adapter import descriptor as _descriptor
from ._literature_history_v1.adapter import materialize
from ._literature_history_v1.adapter import (
    options_for_literature as options_for_literature,
)
from ._literature_history_v1.inputs import _FrozenAccess
from ._literature_history_v1.rules import DEFAULT_PRODUCER, producers
from .card_access import _Entry
from .errors import StorageError


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def _bind(versions, method, record, name, path):
    """Only a declared generated output rule supplies a producer label."""
    if (
        not isinstance(record, dict)
        or set(record) != {"rule", "inputs", "parameters", "sabueso_version"}
        or record["rule"] != name
        or not isinstance(record["sabueso_version"], str)
        or not record["sabueso_version"]
    ):
        raise StorageError(f"Unsupported original generated literature rule at {path}.")
    key, version = (method, name), record["sabueso_version"]
    if key in versions and versions[key] != version:
        raise StorageError(f"Conflicting original generated-rule producers at {path}.")
    versions[key] = version
    return version


def _original_versions(original, options):
    if original is None:
        return {}, DEFAULT_PRODUCER
    if not isinstance(original, dict) or not isinstance(
        original.get("native_payload"), dict
    ):
        raise StorageError("Original literature wire requires a native payload object.")
    native, versions = original["native_payload"], {}
    if not native:
        return versions, DEFAULT_PRODUCER
    primary = _bind(
        versions,
        "knowledge_state",
        (original.get("coverage") or {}).get("rule"),
        "knowledge_state@5",
        "coverage.rule",
    )
    if options["publication_ref"] is not None:
        _bind(
            versions,
            "explain_literature",
            native.get("rule"),
            "literature_explanation@1",
            "native_payload.rule",
        )
    explanations = original.get("explanations")
    if not isinstance(explanations, dict):
        raise StorageError("Original literature explanations must be an object.")
    for key, explanation in explanations.items():
        if not isinstance(explanation, dict):
            raise StorageError("Original publication explanation is unavailable.")
        _bind(
            versions,
            "explain_literature",
            explanation.get("rule"),
            "literature_explanation@1",
            f"explanations[{key}].rule",
        )
    return versions, primary


def expected_result(access, options=None, *, original=None):
    """Evaluate only immutable original predicates over the captured input."""
    options = options_for_literature(options)
    versions, primary = _original_versions(original, options)
    with producers(versions, primary):
        return materialize(_FrozenAccess(access), options)


def restore_result(ref, wire):
    """Expose verified retained rows in native order, never canonical key order."""
    options = options_for_literature(wire["context"]["options"])
    native, rows = wire["native_payload"], wire["rows"]
    if native:
        if options["publication_ref"] is None:
            keys = [item["publication_ref"] for item in native["publications"]]
        else:
            publication = native["publication"]
            keys = [publication["publication_ref"]] if publication is not None else []
    else:
        keys = []
    if len(keys) != len(rows) or set(keys) != set(rows):
        raise StorageError(
            "Original literature rows differ from retained native membership."
        )
    shell = LiteratureResult(ref, wire, (), deepcopy(options))
    return LiteratureResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        deepcopy(options),
    )
