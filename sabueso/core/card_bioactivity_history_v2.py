"""Original SDK202 B4 predicates and retained-result restoration.

Private expected results verify original knowledge; they never replace it. No
Card, current scientific reader, source client or public digester is used here.
"""

from copy import deepcopy

from ._bioactivity_history_v2.adapter import (
    ADAPTER as ADAPTER,
)
from ._bioactivity_history_v2.adapter import (
    SUPPORT_FORMAT as SUPPORT_FORMAT,
)
from ._bioactivity_history_v2.adapter import (
    TOPIC as TOPIC,
)
from ._bioactivity_history_v2.adapter import (
    BioactivityResult as BioactivityResult,
)
from ._bioactivity_history_v2.adapter import (
    _native,
    materialize,
)
from ._bioactivity_history_v2.adapter import (
    defer_frame as defer_frame,
)
from ._bioactivity_history_v2.adapter import (
    descriptor as _descriptor,
)
from ._bioactivity_history_v2.adapter import (
    options_for_bioactivities as options_for_bioactivities,
)
from ._bioactivity_history_v2.inputs import _FrozenAccess
from ._bioactivity_history_v2.rules import DEFAULT_PRODUCER, producers
from .card_access import _Entry
from .errors import StorageError


def descriptor():
    result = _descriptor()
    result["save"] = True
    result.pop("save_reason", None)
    return result


def _bind(versions, method, record, name, path):
    """Only an explicitly selected generated rule supplies a producer label."""
    if (
        not isinstance(record, dict)
        or set(record) != {"rule", "inputs", "parameters", "sabueso_version"}
        or record["rule"] != name
        or not isinstance(record["sabueso_version"], str)
        or not record["sabueso_version"]
    ):
        raise StorageError(
            f"Unsupported original generated bioactivity rule at {path}."
        )
    key, version = (method, name), record["sabueso_version"]
    if key in versions and versions[key] != version:
        raise StorageError(f"Conflicting original generated-rule producers at {path}.")
    versions[key] = version
    return version


def _activity_versions(versions, native, method, options):
    _bind(
        versions,
        method,
        native.get("classification"),
        options["classification_rule"],
        "native_payload.classification",
    )
    checks = native.get("checks")
    if not isinstance(checks, list) or len(checks) != 2:
        raise StorageError("Original activity consistency checks are unavailable.")
    for index, name in enumerate(("pchembl_consistency@1", "unit_scale_discrepancy@1")):
        _bind(versions, method, checks[index], name, f"native_payload.checks[{index}]")
    _bind(
        versions,
        method,
        (native.get("measurement_identity") or {}).get("rule"),
        options["measurement_rule"],
        "native_payload.measurement_identity.rule",
    )
    if options["target_scope_rule"] == "bioactivity_target_scope@2":
        _bind(
            versions,
            method,
            (native.get("scope") or {}).get("target_scope"),
            "bioactivity_target_scope@2",
            "native_payload.scope.target_scope",
        )
        _bind(
            versions,
            method,
            (native.get("target_selection") or {}).get("rule"),
            "bioactivity_target_scope@2",
            "native_payload.target_selection.rule",
        )


def _original_versions(original, options):
    if original is None:
        return {}, DEFAULT_PRODUCER
    if not isinstance(original, dict) or not isinstance(
        original.get("native_payload"), dict
    ):
        raise StorageError(
            "Original bioactivity wire requires a native payload object."
        )
    native, versions = original["native_payload"], {}
    if not native:
        return versions, DEFAULT_PRODUCER
    if options["measurement_ref"] is not None:
        method = "explain_measurement"
        name = (
            "measurement_group_explanation@2"
            if options["measurement_rule"] == "measurement_identity@2"
            else "measurement_group_explanation@1"
        )
        primary = _bind(
            versions, method, native.get("rule"), name, "native_payload.rule"
        )
        _bind(
            versions,
            method,
            native.get("grouping_rule"),
            options["measurement_rule"],
            "native_payload.grouping_rule",
        )
    elif options["molecule_ref"] is not None:
        method = "explain_bioactivity"
        name = (
            "bioactivity_explanation@4"
            if options["target_scope_rule"] == "bioactivity_target_scope@2"
            else "bioactivity_explanation@3"
            if options["measurement_rule"] == "measurement_identity@2"
            else "bioactivity_explanation@1"
            if options["classification_rule"] == "bioactivity_class@3"
            else "bioactivity_explanation@2"
        )
        primary = _bind(
            versions, method, native.get("rule"), name, "native_payload.rule"
        )
        _activity_versions(versions, native, method, options)
    else:
        _activity_versions(versions, native, "bioactivities", options)
        primary = versions[("bioactivities", options["classification_rule"])]
    _bind(
        versions,
        "knowledge_state",
        (original.get("coverage") or {}).get("rule"),
        "knowledge_state@5",
        "coverage.rule",
    )
    rows = original.get("rows")
    if not isinstance(rows, dict):
        raise StorageError("Original bioactivity rows must be an object.")
    for key, row in rows.items():
        interpretation = row.get("interpretation") if isinstance(row, dict) else None
        if not isinstance(interpretation, dict):
            raise StorageError(
                "Original bioactivity row interpretation is unavailable."
            )
        _bind(
            versions,
            "bioactivities",
            interpretation.get("classification"),
            options["classification_rule"],
            f"rows[{key}].interpretation.classification",
        )
        if options["target_scope_rule"] == "bioactivity_target_scope@2":
            _bind(
                versions,
                "bioactivities",
                (interpretation.get("target_assignment") or {}).get("target_scope"),
                "bioactivity_target_scope@2",
                f"rows[{key}].interpretation.target_assignment.target_scope",
            )
    return versions, primary


def expected_result(access, options=None, *, original=None):
    """Evaluate only immutable original predicates over the captured input."""
    options = options_for_bioactivities(options)
    versions, primary = _original_versions(original, options)
    with producers(versions, primary):
        return materialize(_FrozenAccess(access), options)


def restore_result(ref, wire):
    """Expose verified retained rows in native order, never canonical key order."""
    options = options_for_bioactivities(wire["context"]["options"])
    native, rows = wire["native_payload"], wire["rows"]
    grain = wire["context"]["grain"]
    keys = []
    if native:
        if grain == "molecule":
            keys = [item["molecule_ref"] for item in native["items"]]
        elif grain == "group":
            for index, group in enumerate(native["groups"]):
                key = group["group"]
                keys.append(key if key not in keys else f"{key}:occurrence:{index}")
        elif grain == "record":
            keys = [
                record["relationship"]["id"]
                for record in native["records"]
                if record["relationship"]["id"] in rows
            ]
        else:
            raise StorageError("Unsupported original bioactivity row grain.")
    if len(keys) != len(rows) or set(keys) != set(rows):
        raise StorageError(
            "Original bioactivity rows differ from retained native membership."
        )
    shell = BioactivityResult(ref, wire, (), deepcopy(options))
    return BioactivityResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", key), key, rows[key]) for key in keys),
        deepcopy(options),
    )


def expected_publication(access, publication_ref, *, original):
    """Original on-demand publication context, without fetching or source rewriting."""
    if not isinstance(original, dict):
        raise StorageError("Original publication context requires a retained object.")
    explanation = original.get("original_explanation")
    if not isinstance(explanation, dict):
        raise StorageError("Original publication explanation is unavailable.")
    versions = {}
    version = _bind(
        versions,
        "explain_literature",
        explanation.get("rule"),
        "literature_explanation@1",
        "original_explanation.rule",
    )
    frozen = _FrozenAccess(access)
    with producers(versions, version):
        literature = _native(frozen, "literature")
        publication = next(
            (
                row
                for row in literature["publications"]
                if row["publication_ref"] == publication_ref
            ),
            None,
        )
        if publication is None:
            raise StorageError(
                "Publication is outside the original retained literature context."
            )
        return {
            "original_summary": deepcopy(publication),
            "original_explanation": _native(
                frozen, "explain_literature", publication_ref
            ),
            "publication_ref": publication_ref,
        }
