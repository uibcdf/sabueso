"""Compact live access to the same captured quaternary findings as human views."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry
from .card_quaternary_exploration import ADAPTER, SCOPE, TOPIC
from .card_quaternary_selection_v1 import COLUMNS, DEFAULT_FIELDS, item_ref
from .errors import ArgumentError

SUPPORT_FORMAT = "quaternary_support_membership@1"


def descriptor():
    return {
        "key": TOPIC,
        "label": "Interface classifications and family-site comparisons",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {key: {"type": "string"} for key in COLUMNS},
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "quaternary_access_selection@1",
        "mandatory_interpretation": [
            "scope",
            "rule_names",
            "status",
            "coordinate_status",
            "revision_agreement",
            "reason_codes",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
    }


def options_for_quaternary(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(f"{TOPIC} has no scientific options.")
    return {}


@dataclass(frozen=True)
class _QuaternaryResult:
    result_ref: str
    wire: dict
    entries: tuple

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def frame(self, access, selection, entry):
        key = entry.key
        row, original = self.wire["rows"][key], self.wire["support"][key]
        interpretation_location = access._location(
            self.location("rows", key, "interpretation")
        )
        return {
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "relationship_ref": row["item"]["relationship_id"],
            "subject_ref": access._resolve(original["relationship_locations"][0])[0][
                "subject_ref"
            ],
            "state": "present",
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                "format": SUPPORT_FORMAT,
                "basis": original["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": row["id"], "state": row["state"]}
                    for row in original["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation_location,
            "cells": {
                column: {
                    "state": "present",
                    "reason": None,
                    "value": deepcopy(self.value(key, column)),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": "derived_quaternary_interpretation",
                    "support_ref": key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", key, column)
                    ),
                    "interpretation_location": interpretation_location,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def materialize(access):
    key = (ADAPTER, access._focal_key)
    if key not in access._scientific_cache:
        from .card_quaternary_exploration import _materialize

        ref = _materialize(access)
        wire = access._objects[ref]
        shell = _QuaternaryResult(ref, wire, ())
        entries = tuple(
            _Entry(shell.location("rows", key), key, row)
            for key, row in wire["rows"].items()
        )
        access._scientific_cache[key] = _QuaternaryResult(ref, wire, entries)
    result = access._scientific_cache[key]
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_exploration_quaternary import saved_selection as original_selection

    return original_selection(access, fields, options, where, item_refs, order_by)


def defer_frame(frame):
    """Defer values and mandatory interpretation/support together, with read paths."""
    result = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            key: {k: deepcopy(value) for k, value in cell.items() if k != "value"}
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return result
