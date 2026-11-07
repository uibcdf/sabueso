"""Independent SDK205 molecule activity expectations over sealed inputs.

Expected results only check retained knowledge; they never replace it. This
module admits no saved format and uses no current Card, science or source client.
"""

from ._molecule_activity_history_v1.adapter import ADAPTER as ADAPTER
from ._molecule_activity_history_v1.adapter import TOPIC as TOPIC
from ._molecule_activity_history_v1.adapter import materialize
from ._molecule_activity_history_v1.adapter import (
    options_for_activity_context as options_for_activity_context,
)
from ._molecule_activity_history_v1.inputs import _FrozenAccess
from ._molecule_activity_history_v1.rules import DEFAULT_PRODUCER
from ._molecule_activity_history_v1.selection import (
    active,
    evaluate,
    normalize,
    projection,
    selection_ref,
)
from .card_access import _handle
from .card_bioactivity_history_v2 import _original_versions as bioactivity_versions
from .errors import StorageError
from .snapshot import canonical_json


def _versions(original):
    if original is None:
        return {}, DEFAULT_PRODUCER
    if not isinstance(original, dict) or not isinstance(
        original.get("native_payload"), dict
    ):
        raise StorageError("Original molecule activity wire is unavailable.")
    native = original["native_payload"]
    rule = native.get("rule")
    if (
        not isinstance(rule, dict)
        or set(rule) != {"rule", "inputs", "parameters", "sabueso_version"}
        or rule["rule"] != "molecule_activity_context@1"
        or not isinstance(rule["sabueso_version"], str)
        or not rule["sabueso_version"]
    ):
        raise StorageError("Original generated molecule activity rule is unavailable.")
    versions = {}
    targets = native.get("targets")
    if not isinstance(targets, dict):
        raise StorageError("Original supplied target contexts are unavailable.")
    for target in targets.values():
        if not isinstance(target, dict) or set(target) != {
            "overview",
            "focused_results",
        }:
            raise StorageError("Original target result context is unavailable.")
        try:
            wires = [target["overview"]["wire"], *target["focused_results"].values()]
            for wire in wires:
                bound, _ = bioactivity_versions(wire, wire["context"]["options"])
                for key, version in bound.items():
                    if key in versions and versions[key] != version:
                        raise StorageError(
                            "Conflicting original target generated-rule producers."
                        )
                    versions[key] = version
        except (KeyError, TypeError, AttributeError) as error:
            raise StorageError(
                "Original native target binding is unavailable."
            ) from error
    return versions, rule["sabueso_version"]


def expected_result(access, options=None, *, original=None):
    options = options_for_activity_context(options)
    versions, primary = _versions(original)
    frozen = _FrozenAccess(access, versions, primary)
    with frozen.producers():
        return materialize(frozen, options)


def verify_result(access, ref, wire):
    """Compare all original result fields; return only the supplied retained wire."""
    try:
        options = wire["context"]["options"]
        expected = expected_result(access, options, original=wire)
    except (KeyError, TypeError) as error:
        raise StorageError("Incomplete original molecule activity result.") from error
    if ref != expected.result_ref or canonical_json(wire) != canonical_json(
        expected.wire
    ):
        raise StorageError("Molecule activity result differs from original predicates.")
    return wire


def expected_selection(
    result, *, fields=None, where=None, item_refs=None, order_by=None
):
    """Original projection/membership/order over an already verified result."""
    fields = projection(fields)
    query = normalize(where, item_refs, order_by)
    entries, spec = evaluate(result, query) if active(query) else (result.entries, None)
    ref = (
        selection_ref(result, fields, spec)
        if spec is not None
        else _handle(
            "XA_",
            {
                "format": "scientific_access_selection@1",
                "result_ref": result.result_ref,
                "fields": fields,
            },
        )
    )
    return ref, entries, fields, spec
