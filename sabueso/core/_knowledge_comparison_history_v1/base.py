"""Original shared row/cell/frame shape and exact captured locations."""

from copy import deepcopy
from dataclasses import dataclass

from .._protein_context_history_v1.selection import item_ref

ADAPTER = "protein_context_exploration@1"


def location(access, capture, *segments):
    owner = access._captures[capture]
    return {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": owner.pin,
        "snapshot_id": owner.snapshot,
        "segments": list(segments),
    }


def record_location(access, capture, store, identifier):
    return location(
        access,
        capture,
        {"type": "Key", "value": store},
        {"type": "Record", "value": identifier},
    )


def anchor(capture):
    identifier = capture.data["meta"].get("card_id")
    return identifier.split(":", 2)[2] if identifier else None


@dataclass(frozen=True)
class ProteinContextResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    @property
    def explanations(self):
        return self.wire["explanations"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        row = self.wire["rows"][key]
        applicable = {
            "input_index": "supplied_capture",
            "difference_count": "sequence_comparison",
            "identical": "sequence_comparison",
            "predicate": "relationship",
            "channel": "relationship",
            "source": "relationship",
        }
        if column in applicable and row["kind"] != applicable[column]:
            return "not_applicable"
        return row["cell_states"].get(
            column, "present" if row[column] is not None else "unknown"
        )

    def cell_reason(self, key, column):
        return (
            None
            if self.cell_state(key, column) == "present"
            else "The captured record does not state a value of the declared type; inspect the complete original."
        )

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": row["subject_ref"],
            "state": row["state"],
            "location": access._location(entry.location),
            "payload_location": access._location(row["original_location"]),
            "support_location": access._location(self.location("support", entry.key)),
            "support": deepcopy(support),
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": access._location(
                self.location("rows", entry.key, "interpretation")
            ),
            "cells": {
                c: {
                    "value": deepcopy(row[c]),
                    "state": self.cell_state(entry.key, c),
                    "reason": self.cell_reason(entry.key, c),
                    "field": {"adapter": ADAPTER, "column": c},
                    "support_ref": entry.key,
                    "support_basis": support["basis"],
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, c)
                    ),
                }
                for c in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def defer_frame(frame):
    result = {
        k: deepcopy(v)
        for k, v in frame.items()
        if k not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            k: {n: deepcopy(v) for n, v in cell.items() if n != "value"}
            | {"value_included": False}
            for k, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        interpretation_included=False,
        support_included=False,
    )
    return result
