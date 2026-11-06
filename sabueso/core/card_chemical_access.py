"""Compact source-bound chemical classification over one captured Card."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry, _handle
from .card_chemical_selection_v1 import COLUMNS, DEFAULT_FIELDS, FLAGS, item_ref
from .chemical_classification_v1 import RULE, SCOPE, interpret
from .errors import ArgumentError

TOPIC = "chemical_classification"
ADAPTER = "chemical_classification_exploration@1"
SUPPORT_FORMAT = "chemical_classification_support@1"


def descriptor():
    return {
        "key": TOPIC,
        "label": "Chemical classes and source-stated roles",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {"type": "boolean_or_null" if key in FLAGS else "string"}
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "chemical_classification_selection@1",
        "mandatory_interpretation": [
            "scope",
            "rule_names",
            "state",
            "assignment",
            "support_reason",
            "support_grain",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": False,
        "save_reason": "Independent original chemical-profile saved reading is not implemented yet; raw Card export remains available.",
    }


def options_for_chemical(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(f"{TOPIC} has no scientific options.")
    return {}


@dataclass(frozen=True)
class ChemicalResult:
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
        key, row = entry.key, entry.value
        interpretation = access._location(self.location("rows", key, "interpretation"))
        support = self.wire["support"][key]
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "subject_ref": self.wire["native_payload"]["focal_ref"],
            "state": row["state"],
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                "format": SUPPORT_FORMAT,
                "basis": support["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": record["id"], "state": record["state"]}
                    for record in support["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "state": "unknown" if row[column] is None else "present",
                    "reason": "Not stated or not admitted from original support."
                    if row[column] is None
                    else None,
                    "value": deepcopy(row[column]),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": "source_bound_chemical_classification",
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


def materialize(access):
    cache_key = (ADAPTER, access._focal_key)
    if cache_key in access._scientific_cache:
        return access._scientific_cache[cache_key]
    from .card_ligand_site_exploration import _statement

    native = interpret(access._focal)
    ref = _handle(
        "XR_", {"adapter": ADAPTER, "focal": access._focal_key, "native": native}
    )
    shell = ChemicalResult(ref, {}, ())
    rows, supports, explanations = {}, {}, {}
    for original in native["rows"]:
        key = original["row_ref"]
        value = original["value"]
        term = value.get("chebi_id") if isinstance(value, dict) else None
        label = value.get("name") if isinstance(value, dict) else None
        label = (
            label
            if isinstance(label, str) and label.strip()
            else term
            if isinstance(term, str)
            else f"Unrecognized retained {original['kind']} at position {original['index']}"
        )
        field = native["fields"][original["field_path"]]
        selected = field["support_checks"]
        ids = set(selected)
        for source_id in selected:
            for basis in (
                native["identity_bindings"].get(source_id, {}).get("relationships", [])
            ):
                ids.add(basis["source_assertion_id"])
        support = {
            "format": SUPPORT_FORMAT,
            "basis": "source_bound_chemical_classification",
            "rule": RULE,
            "source_assertions": [
                _statement(access, source_id) for source_id in sorted(ids)
            ],
            "source_memberships": deepcopy(original["source_memberships"]),
            "selected_field_checks": deepcopy(selected),
            "field_context_location": shell.location(
                "native_payload", "fields", original["field_path"]
            ),
            "identity_bindings_location": shell.location(
                "native_payload", "identity_bindings"
            ),
            "original_field_member_location": deepcopy(original["location"]),
            "scope": SCOPE,
            "support_grain": original["support_grain"],
        }
        row = {
            "label": label,
            "kind": "chemical_" + original["kind"],
            "term_ref": term
            if isinstance(term, str)
            else "Unrecognized retained identifier",
            "assignment": original["assignment"],
            "state": original["state"],
            "reason": original["support_reason"],
            **{flag: original["categories"].get(flag) for flag in FLAGS},
            "item": deepcopy(original),
            "interpretation": {
                "scope": SCOPE,
                "rule_names": [RULE],
                "state": original["state"],
                "assignment": original["assignment"],
                "support_reason": original["support_reason"],
                "support_grain": original["support_grain"],
                "focal_ref": native["focal_ref"],
            },
        }
        rows[key], supports[key] = row, support
        explanations[key] = {
            "rule": RULE,
            "scope": SCOPE,
            "original_member": deepcopy(original),
            "support_location": shell.location("support", key),
            "field_context_location": support["field_context_location"],
            "identity_bindings_location": support["identity_bindings_location"],
            "original_assertions_location": shell.location(
                "native_payload", "input_source_assertions"
            ),
            "conflicts_location": shell.location("native_payload", "stored_conflicts"),
            "alternatives_location": shell.location(
                "native_payload", "stored_alternatives"
            ),
        }
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": {},
            "used_captures": [access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "support": supports,
        "explanations": explanations,
        "scope": SCOPE,
        "coverage": {
            "scope": SCOPE,
            "basis": native["coverage_basis"],
            "source_request_classification": "not_evaluated_by_this_adapter",
        },
        "outcome": {
            "status": native["status"],
            "reason": None
            if native["status"] == "ok"
            else "Inspect retained field states, original support and coverage; unavailable interpretation is not source absence.",
        },
    }
    result = ChemicalResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
    )
    access._objects[ref] = wire
    access._scientific_cache[cache_key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Keep explicit read destinations when values, scope and support do not fit."""
    deferred = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    deferred.update(
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
    return deferred
