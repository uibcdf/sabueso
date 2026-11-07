"""Independent SDK205 molecule activity expectations over sealed inputs.

Expected results only check retained knowledge; they never replace it. This
module admits no saved format and uses no current Card, science or source client.
"""

from copy import deepcopy
from dataclasses import dataclass, field

from ._molecule_activity_history_v1.adapter import ADAPTER as ADAPTER
from ._molecule_activity_history_v1.adapter import TOPIC as TOPIC
from ._molecule_activity_history_v1.adapter import MoleculeActivityResult, materialize
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
from .card_access import _Entry, _handle
from .card_bioactivity_history_v2 import _original_versions as bioactivity_versions
from .card_bioactivity_history_v2 import restore_result as restore_bioactivity
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


@dataclass(frozen=True)
class _RetainedMoleculeActivityResult(MoleculeActivityResult):
    """Expose original values with no path to new native crossing evaluation."""

    _native_crossings: dict = field(default_factory=dict, repr=False)

    def native_crossing(self, pin):
        """Read a separately verified retained endpoint in its exact scope."""
        try:
            record = self._native_crossings[pin]
        except (KeyError, TypeError) as error:
            raise StorageError(
                "This exact original native crossing was not retained."
            ) from error
        wrapper, location = record["wrapper"], record["location"]
        policies = {
            key: value
            for key, value in self.options.items()
            if key not in ("target_card_ref", "molecule_ref", "measurement_ref")
        }
        expected_location = {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": _handle(
                "XR_", {"adapter": "literal_metadata@1", "value": wrapper}
            ),
            "segments": [{"type": "Key", "value": "native_payload"}],
        }
        if (
            pin not in self._access._captures
            or wrapper["molecule_card_ref"] != self._access._focal.pin
            or wrapper["target_card_ref"] != pin
            or canonical_json(record["inputs"]) != canonical_json(self._access._inputs)
            or canonical_json(record["policies"]) != canonical_json(policies)
            or canonical_json(location) != canonical_json(expected_location)
        ):
            raise StorageError(
                "Original native crossing has a foreign capture or scope."
            )
        return deepcopy(wrapper["native_payload"]), deepcopy(location)


def restore_result(access, ref, wire, *, entry_keys, native_crossings=None):
    """Restore already verified retained rows, order and native memberships.

    Expected predicates belong to admission and never supply retained values.
    ``entry_keys`` must be the recorded original order. Crossings are separately
    verified retained records, bound to exact pins, input occurrences and policies.
    This private restoration helper does not itself admit a saved file format.
    """
    try:
        options = options_for_activity_context(wire["context"]["options"])
        rows, targets = wire["rows"], wire["native_payload"]["targets"]
        if (
            not isinstance(entry_keys, (list, tuple))
            or not all(isinstance(key, str) for key in entry_keys)
            or len(entry_keys) != len(set(entry_keys))
            or set(entry_keys) != set(rows)
            or wire["context"]["molecule_card_ref"] != access._focal.pin
        ):
            raise StorageError(
                "Original molecule rows lack their exact retained order or focal capture."
            )
        crossings = {} if native_crossings is None else deepcopy(native_crossings)
        if not isinstance(crossings, dict):
            raise StorageError(
                "Original native crossings require retained scope records."
            )
        for pin, record in crossings.items():
            if (
                not isinstance(pin, str)
                or not isinstance(record, dict)
                or set(record) != {"wrapper", "location", "inputs", "policies"}
                or not isinstance(record["wrapper"], dict)
                or set(record["wrapper"])
                != {
                    "native_payload",
                    "molecule_card_ref",
                    "target_card_ref",
                    "structural_flag_limit",
                }
                or not isinstance(record["wrapper"]["native_payload"], dict)
                or not isinstance(record["location"], dict)
                or not isinstance(record["inputs"], (list, tuple))
                or not isinstance(record["policies"], dict)
            ):
                raise StorageError("Incomplete retained native crossing scope.")
        members, native_results, target_accesses = {}, {}, {}
        for key in entry_keys:
            row = rows[key]
            pin = row["target_card_ref"]
            if pin not in target_accesses:
                target_accesses[pin] = access._for_capture(pin)
            target = targets[pin]
            overview = target["overview"]
            native_wires = {
                overview["result_ref"]: overview["wire"],
                **target["focused_results"],
            }
            occurrences = row["native_member_occurrences"]
            if wire["context"]["grain"] == "record":
                occurrences = occurrences[:1]
            members[key] = []
            for occurrence in occurrences:
                original_ref = occurrence["result_ref"]
                cache_key = (pin, original_ref)
                if cache_key not in native_results:
                    native_results[cache_key] = restore_bioactivity(
                        original_ref, native_wires[original_ref]
                    )
                original = native_results[cache_key]
                entry = next(
                    entry
                    for entry in original.entries
                    if entry.key == occurrence["entry_key"]
                )
                members[key].append((target_accesses[pin], original, entry))
        shell = _RetainedMoleculeActivityResult(
            ref, wire, (), deepcopy(options), access, members, crossings
        )
        return _RetainedMoleculeActivityResult(
            ref,
            wire,
            tuple(
                _Entry(shell.location("rows", key), key, rows[key])
                for key in entry_keys
            ),
            deepcopy(options),
            access,
            members,
            crossings,
        )
    except (KeyError, TypeError, AttributeError, StopIteration) as error:
        raise StorageError(
            "Incomplete original molecule activity membership."
        ) from error


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
