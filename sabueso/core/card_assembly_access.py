"""Bounded machine access to the same captured assembly findings as human views."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry
from .card_assembly_exploration import ADAPTER, SCOPE, TOPIC, options_for_assembly
from .card_assembly_selection_v1 import COLUMNS, DEFAULT_FIELDS, NULLABLE, item_ref
from .snapshot import canonical_json

SUPPORT_FORMAT = "assembly_generation_support_membership@1"


def result_location(ref, *path):
    return {
        "format": "card_access_location@1",
        "kind": "result",
        "result_ref": ref,
        "segments": [
            {"type": "Index" if type(k) is int else "Key", "value": k} for k in path
        ],
    }


def descriptor():
    return {
        "key": TOPIC,
        "label": "Assembly components and operations",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            k: {
                "type": ("integer" if k == "declaration_count" else "string")
                + ("|null" if k in NULLABLE else "")
            }
            for k in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": options_for_assembly(None),
        "native_rule": "rcsb_assembly_generation@4",
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "assembly_generation_access_selection@1",
        "mandatory_interpretation": [
            "scope",
            "rule_names",
            "status",
            "operator_scope",
            "component_scope",
            "count_state",
            "count_basis",
            "physical_membership",
            "original_context_location",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
        "save_reason": None,
    }


@dataclass(frozen=True)
class _AssemblyResult:
    result_ref: str
    wire: dict
    options: dict
    entries: tuple

    def location(self, *keys):
        return result_location(self.result_ref, *keys)

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        row = self.wire["rows"][key]
        if column == "declaration_count" and row["count_state"] in (
            "factored",
            "not_applicable",
        ):
            return row["count_state"]
        return "unknown" if row[column] is None else "present"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        if state == "factored":
            return (
                "Exact factors are retained; the count is not represented by a scalar."
            )
        if state == "not_applicable":
            return "This row is not a generator count."
        return (
            "Value not available in this original scope."
            if state == "unknown"
            else None
        )

    def frame(self, access, selection, entry):
        key = entry.key
        row, original = self.wire["rows"][key], self.wire["support"][key]
        interpretation = access._location(self.location("rows", key, "interpretation"))
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "relationship_ref": row["relationship_id"],
            "state": "present",
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                "format": SUPPORT_FORMAT,
                "basis": original["basis"],
                "source_reference_state": original["source_reference_state"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": r["id"], "state": r["state"]}
                    for r in original["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "state": self.cell_state(key, column),
                    "reason": self.cell_reason(key, column),
                    "value": deepcopy(row[column]),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": original["basis"],
                    "support_ref": key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", key, column)
                    ),
                    "interpretation_location": interpretation,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def materialize(access, options):
    key = (ADAPTER, access._focal_key, canonical_json(options))
    if key not in access._scientific_cache:
        from .card_assembly_exploration import _materialize

        ref = _materialize(access, options)
        wire = access._objects[ref]
        shell = _AssemblyResult(ref, wire, deepcopy(options), ())
        entries = tuple(
            _Entry(shell.location("rows", k), k, row) for k, row in wire["rows"].items()
        )
        access._scientific_cache[key] = _AssemblyResult(
            ref, wire, deepcopy(options), entries
        )
    result = access._scientific_cache[key]
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Defer values together with their mandatory interpretation and support."""
    result = {
        k: deepcopy(v)
        for k, v in frame.items()
        if k not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            k: {a: deepcopy(b) for a, b in cell.items() if a != "value"}
            | {"value_included": False}
            for k, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return result
