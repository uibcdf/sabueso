"""Original protein sequence-change occurrences, without genomic correspondence."""

from copy import deepcopy
from dataclasses import dataclass

from ..card_access import _Entry, _handle
from ..errors import ArgumentError
from ..snapshot import canonical_json
from . import annotations
from .rules import make_derivation
from .selection import COLUMNS, DEFAULT_FIELDS, item_ref

TOPIC = "sequence_changes"
ADAPTER = "sequence_change_exploration@1"
SUPPORT_FORMAT = "sequence_change_support@1"
KINDS = ("natural_variant", "mutagenesis")
SCOPE = (
    "One retained Card natural-variant or experimental mutagenesis annotation "
    "per occurrence. Original substitutions, alternatives, stated deletions, "
    "sequence axes, uncertain bounds and source membership remain separate. "
    "No genomic join, alignment, identity merge, pathogenicity, clinical effect "
    "or source acquisition is inferred. Structural questions reuse only the "
    "existing annotation_structure_request@1 admission rule."
)


def options_for_changes(options):
    if options not in (None, {}):
        raise ArgumentError("sequence_changes has no interpretation options.")
    return {}


def descriptor():
    from .selection import FORMAT, SORT_COLUMNS

    return {
        "key": TOPIC,
        "label": "Natural variants and mutagenesis",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            column: {
                "type": "integer|null"
                if column in ("start", "end")
                else "boolean|null"
                if column == "missing"
                else "array[string]|null"
                if column == "alternatives"
                else "string|null"
            }
            for column in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "sort_columns": list(SORT_COLUMNS),
        "selection_policy": FORMAT,
        "mandatory_interpretation": [
            "scope",
            "row_grain",
            "mapping_lineage",
            "original_axis",
            "substitution_scope",
            "support_state",
        ],
        "source_support": {"format": SUPPORT_FORMAT},
        "save": False,
        "save_reason": "Independent original sequence-change saved reading is pending.",
    }


class _AnnotationInputs:
    """The existing annotation predicates need only inert access and source locations."""

    def __init__(self, access):
        self.access = access
        self.profile = access.profile

    def _location(self, *keys):
        return self.access._card_location(
            segments=[{"type": "Key", "value": key} for key in keys]
        )

    def _statement(self, ref):
        location = self.access._card_location(
            segments=[
                {"type": "Key", "value": "source_assertion_store"},
                {"type": "Record", "value": ref},
            ]
        )
        try:
            self.access._resolve(location)
        except ArgumentError:
            return {"id": ref, "state": "not_retained", "location": None}
        return {"id": ref, "state": "present", "location": location}


@dataclass(frozen=True)
class SequenceChangeResult:
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
        return self.wire["rows"][key]["cell_states"].get(
            column, "present" if self.value(key, column) is not None else "unknown"
        )

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        return (
            None
            if state == "present"
            else (
                "The retained input shape is unrecognized; inspect the complete original annotation."
                if state == "unrecognized_shape"
                else "The original annotation does not state this value; no replacement is inferred."
            )
        )

    def frame(self, access, selection, entry):
        row = self.wire["rows"][entry.key]
        support = self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": access._focal.pin,
            "location": access._location(entry.location),
            "payload_location": access._location(row["original_location"]),
            "state": row["state"],
            "support_location": access._location(self.location("support", entry.key)),
            "support": {
                "ref": entry.key,
                "format": SUPPORT_FORMAT,
                "basis": support["basis"],
                "source_assertions": [
                    {k: r[k] for k in ("id", "state", "role")}
                    for r in support["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "value": deepcopy(self.value(entry.key, column)),
                    "state": self.cell_state(entry.key, column),
                    "reason": self.cell_reason(entry.key, column),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_ref": entry.key,
                    "support_basis": support["basis"],
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, column)
                    ),
                    "interpretation_location": interpretation,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def _field(access, kind):
    group = access._focal.data.get("sections", {}).get("features_positional")
    return group.get(kind) if isinstance(group, dict) else None


def materialize(access, options=None):
    options_for_changes(options)
    if access.mode != "live" or access.profile != "protein":
        raise ArgumentError(
            "Sequence-change projection requires a live protein capture."
        )
    cache = canonical_json({"focal": access._focal_key, "topic": TOPIC})
    if cache in access._scientific_cache:
        return access._scientific_cache[cache]
    facade = _AnnotationInputs(access)
    original_entries, raw_gaps = annotations.entries(facade)
    selected = [
        e
        for e in original_entries
        if annotations.annotation_path(e.location)[0] in KINDS
    ]
    coverage = {
        "scope": SCOPE,
        "field_states": {},
        "gaps": [
            g
            for g in raw_gaps
            if g["state"] != "retained_empty"
            and (
                g["field"] == "features_positional"
                or any(
                    g["field"].split("[", 1)[0] == "features_positional." + kind
                    for kind in KINDS
                )
            )
        ],
        "conflicts": [],
        "alternatives": [],
    }
    quality = access._focal.data.get("quality", {})
    conflicts = quality.get("conflicts", []) if isinstance(quality, dict) else []
    if isinstance(conflicts, list):
        coverage["conflicts"] = [
            deepcopy(c)
            for c in conflicts
            if isinstance(c, dict)
            and str(c.get("field")).removesuffix(".value")
            in {"features_positional." + k for k in KINDS}
        ]
    else:
        coverage["gaps"].append(
            {"field": "quality.conflicts", "state": "unrecognized_shape"}
        )
    for kind in KINDS:
        node = _field(access, kind)
        values = node.get("value") if isinstance(node, dict) else None
        coverage["field_states"][kind] = (
            "retained_empty"
            if values == []
            else "retained"
            if isinstance(values, list)
            else "not_retained"
            if node is None or values is None
            else "unrecognized_shape"
        )
        if isinstance(node, dict):
            coverage["alternatives"].append(
                {
                    "field": kind,
                    "selection_alternatives": deepcopy(
                        node.get("selection_alternatives", [])
                    ),
                    "alternatives": deepcopy(node.get("alternatives", [])),
                }
            )
    rows, supports, explanations = {}, {}, {}
    for entry in selected:
        kind, index = annotations.annotation_path(entry.location)
        original = entry.value
        basis = annotations.support(facade, entry.location)[0]
        structural = annotations.context(facade, entry.location)
        refs = [
            facade._statement(ref) | {"role": "annotation"}
            for ref in [
                *basis["source_assertion_ids"],
                *basis["missing_field_source_assertion_ids"],
            ]
        ]
        retained = (
            bool(basis["source_assertion_ids"])
            and not basis["missing_field_source_assertion_ids"]
        )
        state = "retained" if retained else "partial"
        support = {
            "basis": "original_annotation_item",
            "format": SUPPORT_FORMAT,
            "state": state,
            "annotation_support": deepcopy(basis),
            "source_assertions": refs,
            "source_assertion_ids": list(basis["source_assertion_ids"]),
            "original_location": deepcopy(entry.location),
        }
        axis = original.get("location")
        axis = (
            axis.get("sequence")
            if isinstance(axis, dict) and axis.get("kind") == "sequence"
            else None
        )
        axis = axis if isinstance(axis, dict) else {}
        substitution = original.get("substitution")
        substitution = substitution if isinstance(substitution, dict) else {}
        row = dict.fromkeys(COLUMNS)
        row.update(
            kind=kind,
            feature_type=kind,
            label=annotations.label(entry),
            original_location=deepcopy(entry.location),
            item=deepcopy(original),
            context_state=structural["state"],
            support_state=state,
            state=state,
            cell_states={},
        )
        raw = {
            "feature_id": original.get("feature_id"),
            "description": original.get("description"),
            "sequence_ref": axis.get("sequence_id"),
            "start": axis.get("start"),
            "end": axis.get("end"),
            "start_modifier": axis.get("start_modifier"),
            "end_modifier": axis.get("end_modifier"),
            "original": substitution.get("original"),
            "alternatives": substitution.get("alternatives"),
            "missing": substitution.get("missing"),
        }
        for column, value in raw.items():
            valid = value is None or (
                type(value) is int and value > 0
                if column in ("start", "end")
                else type(value) is bool
                if column == "missing"
                else isinstance(value, list) and all(isinstance(v, str) for v in value)
                if column == "alternatives"
                else isinstance(value, str)
            )
            if (
                column in ("original", "alternatives", "missing")
                and original.get("substitution") is not None
                and not isinstance(original["substitution"], dict)
            ):
                valid = False
            row[column] = deepcopy(value) if valid else None
            row["cell_states"][column] = (
                "unrecognized_shape"
                if not valid
                else "unknown"
                if value is None
                else "present"
            )
        row["interpretation"] = {
            "scope": SCOPE,
            "row_grain": "one retained Card annotation occurrence; duplicate list occurrences remain separate",
            "mapping_lineage": "Exact subject/field/value membership under annotation_item_support@1; multiple matching native source statements remain explicit, without inventing unique feature correspondence.",
            "original_axis": deepcopy(original.get("location")),
            "substitution_scope": "Original alternatives remain one statement; missing/deletion is asserted only by its stated flag. Natural variation and experimental mutagenesis remain different kinds.",
            "support_state": state,
            "structural_request": deepcopy(structural),
            "source_conflicts": deepcopy(coverage["conflicts"]),
            "source_alternatives": deepcopy(coverage["alternatives"]),
        }
        key = f"{kind}:{index}"
        rows[key], supports[key] = row, support
        explanations[key] = {
            "original_annotation": deepcopy(original),
            "support": deepcopy(support),
            "interpretation": deepcopy(row["interpretation"]),
        }
    partial = bool(coverage["gaps"] or coverage["conflicts"]) or any(
        s["state"] != "retained" for s in supports.values()
    )
    native = {
        "rule": make_derivation(
            "sequence_change_projection@1", inputs=[access._focal.pin]
        ),
        "items": [deepcopy(e.value) for e in selected],
    }
    ref = _handle(
        "XR_",
        {
            "format": ADAPTER,
            "focal": access._focal_key,
            "native": native,
            "rows": rows,
            "support": supports,
            "coverage": coverage,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": {},
            "used_captures": [access._focal_key],
            "grain": "original protein sequence-change annotation",
        },
        "native_payload": native,
        "rows": rows,
        "support": supports,
        "explanations": explanations,
        "scope": SCOPE,
        "coverage": coverage,
        "schema": descriptor(),
        "exclusions": [],
        "outcome": {
            "status": "missing_prerequisite"
            if not rows
            and all(
                value == "not_retained" for value in coverage["field_states"].values()
            )
            else "partial"
            if partial
            else "ok"
            if rows
            else "empty"
            if all(v == "retained_empty" for v in coverage["field_states"].values())
            else "missing_prerequisite",
            "reason": "Inspect original annotation support, field states and structural scope; unstated values remain unknown.",
        },
    }
    shell = SequenceChangeResult(ref, wire, (), {})
    result = SequenceChangeResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
        {},
    )
    access._objects[ref] = wire
    access._scientific_cache[cache] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Keep typed states while deferring values and mandatory meaning atomically."""
    deferred = {
        k: deepcopy(v)
        for k, v in frame.items()
        if k not in ("label", "interpretation", "support", "cells")
    }
    deferred.update(
        cells={
            k: {n: deepcopy(v) for n, v in cell.items() if n != "value"}
            | {"value_included": False}
            for k, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return deferred
