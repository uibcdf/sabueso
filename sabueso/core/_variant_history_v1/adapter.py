"""Captured variant/isoform tissue context under the existing scoped native rules."""

from copy import deepcopy
from dataclasses import dataclass

from ..card_access import _Entry, _handle
from ..errors import ArgumentError
from ..snapshot import canonical_json
from .selection import COLUMNS, DEFAULT_FIELDS, item_ref
from .source import assertion_value

TOPIC = "variants"
ADAPTER = "variant_tissue_context_exploration@1"
SUPPORT_FORMAT = "variant_tissue_context_support@1"
SCOPE = (
    "Retained population-variant and UniProt isoform tissue context. Native "
    "pext_at_variant@2 and isoform_exon_usage@3 keep exact genomic, transcript, "
    "CDS and per-tissue scope. No alignment, liftover, identity merge, source "
    "acquisition, pathogenicity, harmlessness or zero-expression inference."
)


def options_for_variants(options):
    if options is None:
        options = {}
    if not isinstance(options, dict) or set(options) - {"mode", "threshold"}:
        raise ArgumentError("variants options are mode and threshold only.")
    mode = options.get("mode", "variants")
    if not isinstance(mode, str) or mode not in ("variants", "isoforms"):
        raise ArgumentError("variants mode requires variants or isoforms.")
    from .validation import digest_threshold

    threshold = digest_threshold(options.get("threshold", 0.1))
    return {"mode": mode, "threshold": threshold}


def descriptor():
    from .selection import FORMAT

    return {
        "key": TOPIC,
        "label": "Variants, isoforms and tissue context",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {
                "type": "integer|null"
                if key in ("genomic_position", "own_coding_bases", "tissue_count")
                else "boolean|null"
                if key == "own_bases_complete"
                else "string|null"
            }
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {"mode": "variants", "threshold": 0.1},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": FORMAT,
        "mandatory_interpretation": [
            "scope",
            "row_grain",
            "native_rule",
            "coordinate_scope",
            "tissue_scope",
            "support_state",
        ],
        "source_support": {"format": SUPPORT_FORMAT},
        "save": False,
        "save_reason": "Independent original variant tissue-context saved reading is not implemented.",
    }


@dataclass(frozen=True)
class VariantResult:
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
        if self.value(key, column) is not None:
            return "present"
        variant = self.options["mode"] == "variants"
        applicable = column not in (
            ("isoform_ref", "own_coding_bases", "own_bases_complete")
            if variant
            else ("variant_ref", "transcript", "genomic_position")
        )
        return "unknown" if applicable else "not_applicable"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        return (
            None
            if state == "present"
            else "The native scoped reader retains no value for this field."
            if state == "unknown"
            else "This field belongs to the other variant/isoform row grain."
        )

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
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
            "payload_location": access._location(
                self.location("rows", entry.key, "item")
            ),
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


def _field(access, path):
    node = access._focal.data.get("sections", {})
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _location(access, path, index=None):
    segments = [
        {"type": "Key", "value": key} for key in ("sections", *path.split("."), "value")
    ]
    if index is not None:
        segments.append({"type": "Index", "value": index})
    return access._card_location(segments=segments)


def _support(access, explanation):
    """Validate original input membership without manufacturing finer lineage."""
    stored = {r["id"]: r for r in access._focal.data["source_assertion_store"]}
    identifier = access._focal.data["meta"].get("card_id")
    subjects = {identifier}
    if isinstance(identifier, str) and identifier.startswith("sabueso:"):
        subjects.add(identifier.split(":", 2)[2])
    records, inputs, gaps = [], [], []

    def bind(ref, field, role, accepted=None):
        record = stored.get(ref)
        state = (
            "not_retained"
            if record is None
            else "field_mismatch"
            if record.get("field_path") != field
            else "subject_mismatch"
            if record.get("subject_ref") not in subjects
            else "value_mismatch"
            if accepted is not None
            and not any(
                canonical_json(assertion_value(record)) == canonical_json(v)
                for v in accepted
            )
            else "present"
        )
        records.append(
            {
                "id": ref,
                "state": state,
                "role": role,
                "field_path": field,
                "location": access._card_location(
                    segments=[
                        {"type": "Key", "value": "source_assertion_store"},
                        {"type": "Record", "value": ref},
                    ]
                )
                if record
                else None,
            }
        )

    def visit(value):
        if isinstance(value, list):
            for member in value:
                visit(member)
        elif isinstance(value, dict):
            locator = value.get("locator")
            if (
                isinstance(locator, dict)
                and "field_path" in locator
                and "value" in value
            ):
                path = locator["field_path"]
                node = _field(access, path)
                refs = [r["id"] for r in value.get("source_assertions", [])]
                matched = bool(refs)
                if not refs:
                    refs = (node or {}).get("source_assertion_ids", [])
                    gaps.append(
                        {
                            "reason": "no_native_input_assertion",
                            "locator": deepcopy(locator),
                        }
                    )
                inputs.append(
                    {
                        "locator": deepcopy(locator),
                        "location": _location(access, path, locator.get("index")),
                        "support_basis": value.get("support_basis"),
                        "native_membership_matched": matched,
                    }
                )
                for ref in refs:
                    bind(
                        ref,
                        path,
                        "original_input",
                        [value["value"], (node or {}).get("value")],
                    )
                return
            # Source-backed isoform text is retained independently of selected fields.
            if "item" in value and isinstance(value.get("source_assertions"), list):
                for record in value["source_assertions"]:
                    bind(
                        record["id"],
                        "annotations.tissue_specificity",
                        "native_isoform_text",
                    )
                return
            for key, member in value.items():
                if key not in ("item", "source_assertions"):
                    visit(member)

    visit(explanation)
    seen, unique = set(), []
    for record in records:
        key = canonical_json(record)
        if key not in seen:
            seen.add(key)
            unique.append(record)
    complete = (
        bool(inputs)
        and bool(unique)
        and not gaps
        and all(r["state"] == "present" for r in unique)
    )
    return {
        "format": SUPPORT_FORMAT,
        "basis": "native_exact_or_aggregate_input_membership",
        "state": "retained" if complete else "partial",
        "source_assertions": unique,
        "inputs": inputs,
        "gaps": gaps,
        "qualifier_conflicts": [],
        "quality_location": access._card_location(
            segments=[{"type": "Key", "value": "quality"}]
        ),
        "whole_card_context_location": access._card_location(),
    }


def materialize(access, options=None):
    options = options_for_variants(options)
    if access.mode != "live":
        raise ArgumentError(
            "Independent original variant tissue-context saved reading is not implemented."
        )
    if access.profile != "protein":
        raise ArgumentError("variants requires a protein Card.")
    key = (ADAPTER, access._focal_key, canonical_json(options))
    if key in access._scientific_cache:
        return access._scientific_cache[key]
    from .explanation import (
        explain_isoform_tissue_usage,
        explain_variant_tissue_usage,
    )
    from .inputs import _CapturedCard

    card = _CapturedCard(access._focal)
    explain = (
        explain_variant_tissue_usage
        if options["mode"] == "variants"
        else explain_isoform_tissue_usage
    )
    explanation = explain(card, options["threshold"])
    native = deepcopy(explanation["view"])
    coverage = {
        "rows": [
            {
                "area": f["field_path"],
                "state": "retained" if f["stored"] else "not_retained",
                "basis": "original_explanation_field_state",
            }
            for f in explanation["fields"]
        ],
        "gaps": deepcopy(explanation["gaps"]),
        "context": deepcopy(explanation["context"]),
        "scope_note": "Original native input and request context only; missing stored data, absent source values and failed/unobserved requests are distinct. No source completeness or external absence is inferred.",
    }
    coverage["field_conflicts"] = [
        {"field_path": f["field_path"], "conflicts": deepcopy(f["conflicts"])}
        for f in explanation["fields"]
        if f.get("conflicts")
    ]
    coverage["field_alternatives"] = [
        {
            "field_path": f["field_path"],
            "alternatives": deepcopy(f.get("selection_alternatives", [])),
            "unselected_source_count": len(f.get("alternatives", [])),
        }
        for f in explanation["fields"]
        if f.get("selection_alternatives") or f.get("alternatives")
    ]
    rows, support = {}, {}
    for index, (item, why) in enumerate(
        zip(native["items"], explanation["items"], strict=True)
    ):
        row_key = f"{options['mode']}:{index}"
        membership = _support(access, why)
        variant = options["mode"] == "variants"
        axis = (
            item.get("coordinate_scope", {})
            if variant
            else explanation.get("coordinate_scope", {})
        )
        pext = item.get("pext", {})
        values = pext.get("by_tissue")
        label = item.get("variant_id") if variant else item.get("isoform")
        row = {
            **dict.fromkeys(COLUMNS),
            "kind": "population_variant" if variant else "isoform_tissue_context",
            "label": label or f"Original {options['mode']} occurrence {index}",
            "variant_ref": item.get("variant_id") if variant else None,
            "isoform_ref": item.get("isoform") if not variant else None,
            "transcript": item.get("transcript") if variant else None,
            "assembly": axis.get("assembly"),
            "chromosome": axis.get("chromosome"),
            "genomic_position": axis.get("position") if variant else None,
            "own_coding_bases": item.get("own_coding_bases") if not variant else None,
            "own_bases_complete": item.get("own_bases_complete")
            if not variant
            else None,
            "pext_basis": pext.get("basis"),
            "tissue_count": sum(v is not None for v in values.values())
            if isinstance(values, dict)
            else None,
            "support_state": membership["state"],
            "state": "partial" if membership["state"] != "retained" else "retained",
            "item": deepcopy(item),
            "interpretation": {
                "scope": SCOPE,
                "row_grain": "native occurrence; equal identifiers do not merge rows",
                "native_rule": deepcopy(native["rule"]),
                "coordinate_scope": deepcopy(axis),
                "tissue_scope": "Per-tissue missing/conflicting bases and denominators remain in native_payload; a cutoff is not pathogenicity and missing pext is not zero expression.",
                "support_state": membership["state"],
                "mapping_lineage": "native exact or aggregate source membership; finer mapping lineage is not reconstructed",
                "source_conflicts": deepcopy(coverage["field_conflicts"]),
                "source_alternatives": deepcopy(coverage["field_alternatives"]),
            },
        }
        rows[row_key], support[row_key] = row, membership
    ref = _handle(
        "XR_",
        {
            "format": ADAPTER,
            "focal": access._focal_key,
            "options": options,
            "native": native,
            "explanation": explanation,
            "support": support,
        },
    )
    partial = bool(explanation["gaps"] or coverage["field_conflicts"]) or any(
        s["state"] != "retained" for s in support.values()
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": deepcopy(options),
            "used_captures": [access._focal_key],
            "grain": "native population-variant or isoform occurrence",
        },
        "native_payload": native,
        "original_explanation": deepcopy(explanation),
        "rows": rows,
        "support": support,
        "coverage": coverage,
        "scope": SCOPE,
        "schema": descriptor(),
        "exclusions": [],
        "outcome": {
            "status": "missing_prerequisite"
            if explanation["status"] == "not_on_card"
            else "partial"
            if partial
            else "ok"
            if rows
            else "empty",
            "reason": "Original native gaps or unverified input support remain; inspect coverage and complete explanations."
            if partial or explanation["status"] == "not_on_card"
            else None,
        },
        "explanations": {
            k: {
                "native_explanation": deepcopy(why),
                "support": deepcopy(support[k]),
                "interpretation": deepcopy(rows[k]["interpretation"]),
            }
            for k, why in zip(rows, explanation["items"], strict=True)
        },
    }
    shell = VariantResult(ref, wire, (), options)
    result = VariantResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", k), k, row) for k, row in rows.items()),
        options,
    )
    access._objects[ref] = wire
    access._scientific_cache[key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
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
