"""Compact exact selection over the shared native ligand-site result (#148).

This is a display policy, not a scientific rule. The initial policy deliberately
admits only declared textual columns; numbers, booleans and nulls are not strings.
Saved scientific verification is separate and remains unavailable for this route.
"""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry
from .card_ligand_site_exploration import ADAPTER, SCOPE, TOPIC
from .card_ligand_site_selection_v1 import COLUMNS, DEFAULT_FIELDS, item_ref
from .card_ligand_site_selection_v1 import FORMAT as POLICY
from .errors import ArgumentError


def descriptor():
    return {
        "key": TOPIC,
        "label": "Ligand contacts and annotated-site comparisons",
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
        "selection_policy": POLICY,
        "mandatory_interpretation": ["scope", "comparison", "classification_rule"],
        "save": False,
    }


def options_for_sites(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(f"{TOPIC} has no scientific options.")
    return {}


@dataclass(frozen=True)
class _SiteResult:
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
        row = self.wire["rows"][key]
        return (
            "ligand_contact_comparison"
            if column == "kind"
            else row["item"]["site_class"]
            if column == "site_class"
            else row[column]
        )

    def frame(self, access, selection, entry):
        key = entry.key
        row = self.wire["rows"][key]
        original_support = self.wire["support"][key]
        interpretation_location = access._location(
            self.location("rows", key, "interpretation")
        )
        return {
            "item_ref": item_ref(self, entry),
            "kind": "ligand_contact_comparison",
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "relationship_ref": key,
            "subject_ref": access._resolve(original_support["relationship_location"])[
                0
            ]["subject_ref"],
            "state": "present",
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                "basis": original_support["basis"],
                "source_assertions": deepcopy(original_support["source_assertions"]),
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation_location,
            "cells": {
                column: {
                    "state": "present",
                    "reason": None,
                    "value": deepcopy(self.value(key, column)),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": "derived_ligand_site_comparison",
                    "support_ref": key,
                    "value_included": True,
                    "value_location": access._object_location(
                        "ligand_contact_comparison"
                    )
                    if column == "kind"
                    else access._location(
                        self.location("rows", key, "item", "site_class")
                        if column == "site_class"
                        else self.location("rows", key, column)
                    ),
                    "interpretation_location": interpretation_location,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def materialize(access):
    """Share the exact human result, including original item locations and IDs."""
    key = (ADAPTER, access._focal_key)
    if key not in access._scientific_cache:
        from .card_ligand_site_exploration import _materialize

        ref = _materialize(access)
        wire = access._objects[ref]
        wire["coverage"] = {
            "basis": "retained_contact_declarations",
            "scope": SCOPE,
            "source_request_classification": "not_evaluated_by_this_adapter",
        }
        for row in wire["rows"].values():
            row["interpretation"].update(
                comparison=deepcopy(row["item"]["comparison"]),
                coordinate_scope_rule="ligand_site_coordinate_scope@1",
                annotation_count_semantics="Retained source annotation contexts; not independently identified physical sites.",
            )
        shell = _SiteResult(ref, wire, ())
        entries = tuple(
            _Entry(shell.location("rows", k), k, row)
            for k, row in sorted(
                wire["rows"].items(), key=lambda pair: (pair[1]["ligand_ref"], pair[0])
            )
        )
        access._scientific_cache[key] = _SiteResult(ref, wire, entries)
    result = access._scientific_cache[key]
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Defer values and mandatory comparison context as one inspectable unit."""
    result = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            key: {k: deepcopy(v) for k, v in cell.items() if k != "value"}
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return result
