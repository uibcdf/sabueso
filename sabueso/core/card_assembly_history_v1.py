"""Frozen original assembly findings from 77fd770 / SDK135, used only for validation.

Expected values never replace retained scientific output. Native predicates read
sealed source records; no Card construction, current readers or catalog runs.
"""

import re
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, replace
from types import SimpleNamespace

from .card_access import _Entry, _handle
from .card_assembly_selection_v1 import (
    COLUMNS as ALL_COLUMNS,
)
from .card_assembly_selection_v1 import (
    DEFAULT_FIELDS,
    NULLABLE,
    item_ref,
)
from .card_exploration_history import _ExpectedRule, _HistoricalInput
from .card_ligand_site_history_v1 import _Context, _link_view, _location, _statement
from .card_quaternary_history_v1 import _link
from .errors import ArgumentError


def options_for_assembly(options):
    """Original receiving grammar, independent of the current public digesters."""
    from ._assembly_history_v1.assembly_requests import budget

    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - {
        "structure_ref",
        "relationship_id",
        "expand_operations",
        "expand_occurrences",
        "operation_budget",
    }:
        raise ArgumentError("Unsupported original assembly options.")
    result = {
        "structure_ref": options.get("structure_ref"),
        "relationship_id": options.get("relationship_id"),
        "expand_operations": options.get("expand_operations", False),
        "expand_occurrences": options.get("expand_occurrences", False),
        "operation_budget": budget(options.get("operation_budget", 100_000)),
    }
    ref, relationship = result["structure_ref"], result["relationship_id"]
    if ref is not None and (
        not isinstance(ref, str) or re.fullmatch(r"pdb:[A-Z0-9]{4}", ref) is None
    ):
        raise ArgumentError("Invalid original structure reference.")
    if relationship is not None and (
        not isinstance(relationship, str) or not relationship.strip() or ref is None
    ):
        raise ArgumentError("Invalid original relationship selector.")
    if any(
        type(result[k]) is not bool for k in ("expand_operations", "expand_occurrences")
    ):
        raise ArgumentError("Original expansion flags require booleans.")
    return result


class _CapturedCard(_HistoricalInput):
    def __init__(self, capture):
        super().__init__(capture)
        for name in ("source_assertion_store", "relationship_store"):
            records = getattr(self, name)
            records.store = {r["id"]: r for r in records.to_list()}


def restore_result(ref, wire):
    """Expose retained rows in their original native order after JSON key sorting."""
    shell = _AssemblyResult(ref, wire, wire["context"]["options"], ())
    keys = list(_rows(wire["native_payload"])) if wire["native_payload"] else []
    entries = tuple(
        _Entry(shell.location("rows", key), key, wire["rows"][key]) for key in keys
    )
    return replace(shell, entries=entries)


def expected_result(access, options):
    from .card_exploration_storage import _access

    original = _access(access._captures, access._inputs, {}, {}, access._focal_key)
    original._mode = "live"
    ref = _materialize(original, options)
    result = restore_result(ref, original._objects[ref])
    if result.wire["native_payload"]:
        result.wire["native_payload"] = _ExpectedRule(result.wire["native_payload"])
    return result


def expected_links(access, result, key):
    from .card_exploration_storage import _access

    original = _access(
        access._captures,
        access._inputs,
        {result.result_ref: result.wire},
        {},
        access._focal_key,
    )
    original._mode = "live"
    explorer = _Context(original)
    item = SimpleNamespace(
        _view=SimpleNamespace(
            explorer=explorer,
            _selection=SimpleNamespace(_scientific=result),
            result_ref=result.result_ref,
        ),
        _entry=SimpleNamespace(
            key=key,
            value=result.wire["rows"][key],
            location=result.location("rows", key),
        ),
        label=result.wire["rows"][key]["label"],
        payload_location=result.location("rows", key),
    )
    return links(item)


TOPIC = "assembly_generation"

ADAPTER = "assembly_generation_exploration@1"

LINK_RULE = "assembly_generation_links@1"

COLUMNS = ALL_COLUMNS[2:]

HEADERS = (
    "Index",
    "Structure",
    "Assembly",
    "Declaration",
    "Operators",
    "Components",
    "Declared combinations",
    "Context",
)

SCOPE = (
    "Original assembly component and operation declarations, with their exact source "
    "contexts and key bindings. Counts describe declared positions, including repeats; "
    "they do not count distinct physical molecules. Ligand-neighbor references are "
    "not complete instance records. Physical membership, geometry and assembly contacts "
    "remain uncomputed. Missing retained input is not source absence. Browsing fetches nothing."
)

STATES = {
    "planned": "Declaration plan available",
    "parsed": "Operation plan available",
    "retained": "Original input retained",
    "retained_empty": "Original list is empty",
    "retained_null": "Original value is null",
    "not_retained": "Original input not retained",
    "unavailable": "Plan unavailable",
    "unrecognized_shape": "Unrecognized original shape",
    "source_scope_unbound": "Source identity not bound",
    "unplaced": "Declaration not admitted",
    "resolved": "Keys matched",
    "partial": "Some references incomplete",
    "unresolved": "Keys unresolved",
    "not_reconciled": "Not evaluated",
    "referenced": "Ligand reference only",
    "ambiguous": "Ambiguous keys",
    "unrecognized_label": "Label not interpretable",
}

REASONS = {
    "not_retained": "The original component list is not retained.",
    "retained_null": "The original component list is null.",
    "unrecognized_shape": "The original component list has an unsupported shape.",
    "unrecognized_component_labels": "At least one component label is invalid; no valid generator prefix is substituted.",
    "unsupported": "The original operation expression is not supported by this rule.",
    "parent_scope_unbound": "The generator does not bind to its original assembly parent.",
}


def _generator_reason(parent, item):
    plan = item["occurrence_plan"]
    if plan["status"] == "unavailable":
        return REASONS.get(
            plan["reason"],
            "The original generator cannot be interpreted; inspect its input and reason code.",
        )
    if plan["status"] == "retained_empty":
        return "The component list is explicitly empty; this does not establish an empty molecular system."
    counts = Counter(r["state"] for r in item["component_bindings"])
    reasons = [
        f"{counts[state]} {label}"
        for state, label in [
            ("referenced", "ligand-only component references"),
            ("unresolved", "unresolved component keys"),
            ("ambiguous", "ambiguous component keys"),
        ]
        if counts[state]
    ]
    if item["operator_scope"] != "resolved":
        reasons.append(
            "Operator key binding is incomplete; inspect each original reference"
        )
    if parent.get("parent_identity") == "ambiguous":
        reasons.append(
            "The native assembly ID is repeated; original parent positions remain separate"
        )
    if plan["count_state"] == "factored":
        reasons.append("Exact factors are retained instead of a scalar count")
    return (
        ". ".join(reasons) + "."
        if reasons
        else "Native keys are matched in the retained input; physical uniqueness and biological relevance are not established."
    )


def _rows(native):
    rows = {}

    def add(key, kind, rid, structure, item, source_index=None, parent=None, **values):
        rows[key] = {
            "label": values.pop("label", str(structure or "Unplaced structure")),
            "kind": kind,
            "structure_ref": structure,
            "assembly_id": None,
            "status": "not_retained",
            "operator_scope": None,
            "component_scope": None,
            "declaration_count": None,
            "count_state": "not_applicable",
            "finding": "Original generation inputs are unavailable",
            "reason": "Inspect original declarations and source/request coverage; browsing does not fetch missing inputs.",
            "item": deepcopy(item),
            "relationship_id": rid,
            "source_index": source_index,
            "parent_index": None if parent is None else parent["assembly_index"],
            **values,
        }

    for si, source in enumerate(native["sources"]):
        prefix = f"source:{si}"
        if not source["assemblies"]:
            add(
                prefix,
                "assembly_source_state",
                source["relationship_id"],
                source["structure_ref"],
                source,
                si,
                status=source["status"],
                finding=STATES.get(
                    source["status"], "Original source scope unavailable"
                ),
            )
        for parent in source["assemblies"]:
            ai, aid = parent["assembly_index"], parent.get("assembly_id")
            if not parent["generators"]:
                add(
                    f"{prefix}:parent:{ai}",
                    "assembly_parent_state",
                    source["relationship_id"],
                    source["structure_ref"],
                    parent,
                    si,
                    parent,
                    assembly_id=aid,
                    status=parent["status"],
                    finding=STATES.get(
                        parent["status"], "Original generator scope unavailable"
                    ),
                )
            for item in parent["generators"]:
                plan = item["occurrence_plan"]
                count = plan["declared_occurrence_count"]
                finding = (
                    f"{count} declared positions"
                    if count is not None
                    else "Exact count retained as factors"
                    if plan["count_state"] == "factored"
                    else "Declaration count unavailable"
                )
                label = (
                    f"{source['structure_ref']} · assembly {aid}"
                    if aid
                    else f"{source['structure_ref']} · assembly position {ai + 1}"
                )
                label += f" · generator position {item['generator_index'] + 1} · source {si + 1}"
                add(
                    f"{prefix}:parent:{ai}:generator:{item['generator_index']}",
                    "assembly_generator",
                    source["relationship_id"],
                    source["structure_ref"],
                    item,
                    si,
                    parent,
                    label=label,
                    assembly_id=aid,
                    status=plan["status"],
                    operator_scope=item.get("operator_scope"),
                    component_scope=item.get("component_scope"),
                    declaration_count=count,
                    count_state=plan["count_state"],
                    finding=finding,
                    reason=_generator_reason(parent, item),
                )
    for index, item in enumerate(native["gaps"]):
        add(
            f"gap:{index}",
            "assembly_generation_gap",
            item["relationship_id"],
            None,
            item,
        )
    for index, item in enumerate(native["unplaced"]):
        add(
            f"unplaced:{index}",
            "assembly_unplaced",
            item["relationship_id"],
            None,
            item,
            status="unplaced",
            finding="Original structure declaration is not admitted",
            reason="The original declaration does not bind to the captured protein; inspect its admission and original support.",
        )
    return rows


def _materialize(access, options):
    from ._assembly_history_v1.assembly_generation_v4 import generation

    native, rows = {}, {}
    outcome = {
        "status": "not_applicable",
        "reason": "Assembly generation requires a protein Card.",
    }
    if access.profile == "protein" and not access._focal.pin:
        outcome = {
            "status": "missing_prerequisite",
            "reason": "A captured protein identity is required; inspect the original content.",
        }
    elif access.profile == "protein":
        card = _CapturedCard(access._focal)
        native = generation(
            card,
            options["structure_ref"],
            options["relationship_id"],
            options["expand_operations"],
            options["operation_budget"],
            options["expand_occurrences"],
        )
        rows = _rows(native)
        for row in rows.values():
            if row["structure_ref"] is None:
                original = card.relationship_store.get(row["relationship_id"])
                candidate = original.get("object_ref")
                row["structure_ref"] = candidate if isinstance(candidate, str) else None
                row["label"] = str(row["structure_ref"] or "Unplaced structure")
        outcome = {
            "status": "missing_prerequisite"
            if native["status"] == "missing_prerequisite"
            else "ok"
            if rows
            else "empty",
            "reason": "A consistent focal protein identity is unavailable; inspect the original inputs."
            if native["status"] == "missing_prerequisite"
            else None
            if rows
            else "No matching assembly-generation declarations are retained. Inspect source/request coverage; this is not evidence of no assembly.",
        }
    identity = {k: v for k, v in native.items() if k != "sabueso_version"}
    ref = _handle(
        "XR_",
        {
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "options": options,
            "native": identity,
        },
    )

    supports, explanations = {}, {}
    for key, row in rows.items():
        rid = row["relationship_id"]
        relationship = card.relationship_store.get(rid)
        si = row["source_index"]
        refs = (
            [native["sources"][si]["source_assertion_id"]]
            if si is not None
            else relationship.get("source_assertion_ids")
        )
        valid = isinstance(refs, list) and all(isinstance(r, str) for r in refs)
        supports[key] = {
            "basis": "original_assembly_generation"
            if si is not None
            else "original_structure_declaration_only",
            "source_reference_state": "retained"
            if valid
            else "unavailable_or_unrecognized",
            "source_assertions": [_statement(access, r) for r in sorted(set(refs))]
            if valid
            else [],
            "relationship_locations": [_location(access, "relationship_store", rid)],
            "scope": SCOPE,
        }
        rules = [
            native[k]
            for k in (
                "rule",
                "operator_binding_rule",
                "component_binding_rule",
                "occurrence_rule",
            )
        ]
        supports[key]["rule_names"] = rules
        item = row["item"]
        factors = (
            item.get("occurrence_plan", {}).get("factors")
            if row["kind"] == "assembly_generator"
            else None
        )
        row["interpretation"] = {
            "scope": SCOPE,
            "rule_names": rules,
            "physical_membership": native["physical_membership"],
            "status": row["status"],
            "operator_scope": row["operator_scope"],
            "component_scope": row["component_scope"],
            "count_state": row["count_state"],
            "count_basis": "source_declaration_positions_not_distinct_molecules",
            "exact_factors_location": result_location(
                ref, "rows", key, "item", "occurrence_plan", "factors"
            )
            if factors is not None
            else None,
            "original_context_location": result_location(ref, "rows", key, "item"),
        }
        row["support_location"] = result_location(ref, "support", key)
        explanations[key] = {
            "interpretation": deepcopy(row["interpretation"]),
            "finding": row["finding"],
            "reason": row["reason"],
            "request": deepcopy(options),
            "original_input_location": deepcopy(item.get("input_location")),
            "source_context_location": result_location(
                ref, "native_payload", "sources", si
            )
            if si is not None
            else None,
            "source_request_context_location": deepcopy(native["quality_location"]),
            "native_result_location": result_location(ref, "native_payload"),
            "scope": SCOPE,
        }
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": deepcopy(options),
            "native_rule": "rcsb_assembly_generation@4",
            "used_captures": [access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "support": supports,
        "explanations": explanations,
        "scope": SCOPE,
        "outcome": outcome,
        "coverage": {
            "basis": "original_assembly_generation_inputs",
            "scope": SCOPE,
            "quality_location": deepcopy(native.get("quality_location")),
            "source_request_classification": "not_evaluated_by_this_adapter",
        },
    }
    access._objects[ref] = wire
    return ref


def support(item):
    return [
        deepcopy(
            item._view.explorer.access._objects[item._view.result_ref]["support"][
                item._entry.key
            ]
        )
    ]


def links(item):

    explorer = item._view.explorer
    result = item._view._selection._scientific
    basis = support(item)
    locations = [
        (
            "original_declaration",
            item.label,
            result.location("rows", item._entry.key, "item"),
        )
    ]
    locations += [
        ("source", s["id"], s["location"])
        for s in basis[0]["source_assertions"]
        if s["state"] == "present"
    ]
    locations += [
        ("structure_context", item._entry.value["relationship_id"], loc)
        for loc in basis[0]["relationship_locations"]
    ]
    body = result.wire["explanations"][item._entry.key]
    for role in ("original_input", "source_context", "source_request_context"):
        if body[role + "_location"] is not None:
            locations.append((role, role.replace("_", " "), body[role + "_location"]))
    rows = [
        _link(explorer, role, target, basis, location=location)
        for role, target, location in locations
    ]
    rows.extend(
        {
            "role": "source",
            "label": "Unavailable original source · " + s["id"],
            "target_ref": s["id"],
            "support": deepcopy(basis),
            "rule": LINK_RULE,
            "availability": "missing_prerequisite",
            "candidates": [],
            "paths": [],
            "blocked_paths": [],
        }
        for s in basis[0]["source_assertions"]
        if s["state"] != "present"
    )
    return _link_view(
        explorer,
        [{**r, "rule": LINK_RULE} for r in rows],
        item._view,
        f"Original context for {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
    )


def display_filter(view, column, value):
    from .card_assembly_selection_v1 import validate_equality

    validate_equality(column, value)
    if view._status not in ("ok", "empty"):
        return replace(view, _origin=view)
    entries = tuple(e for e in view._selected if e.value[column] == value)
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status="ok" if entries else "empty",
        _reason=None
        if entries
        else "No assembly findings match this display selection.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(value),
        },
    )


def display_row(item, index, preview):
    row = item._entry.value
    declaration = STATES.get(row["status"], row["status"])
    if row["kind"] == "assembly_generator":
        declaration = f"Generator position {row['item']['generator_index'] + 1} · source {row['source_index'] + 1} · {declaration}"
    return (
        str(index),
        preview(row["structure_ref"]),
        preview(row["assembly_id"])
        if row["assembly_id"] is not None
        else "Not identified",
        declaration,
        STATES.get(row["operator_scope"], row["operator_scope"] or "Not evaluated"),
        STATES.get(row["component_scope"], row["component_scope"] or "Not evaluated"),
        preview(row["finding"]),
        preview(row["reason"], 160),
    )


def detail_lines(view, preview):
    if view.presentation != "detail" or not view._selected:
        return []
    row = view._selected[0].value
    if row["kind"] != "assembly_generator":
        return [
            row["reason"],
            "Original source scope: native_payload. Complete source/request context: explain() and related().",
        ]
    item = row["item"]
    expression = item.get("plan", {}).get("expression")
    lines = [
        "Original operation expression: "
        + (
            preview(expression, 160)
            if expression is not None
            else "not retained in a supported string form"
        )
    ]
    components = item.get("component_bindings", [])
    values = [
        f"{preview(c.get('asym_id'), 40) if 'asym_id' in c else 'unrecognized label'}: {STATES.get(c['state'], c['state'])}"
        for c in components[:8]
    ]
    lines.append(
        f"Component positions (preview {len(values)} of {len(components)}): "
        + (
            "; ".join(values)
            if values
            else "none admitted; inspect original input state"
        )
    )
    plan = item["occurrence_plan"]
    if plan["count_state"] == "factored":
        factors = plan["factors"]
        groups = factors["operation_groups_decimal"]
        lines.append(
            "Exact count factors (text preview): "
            + factors["component_positions_decimal"]
            + " component positions × operation groups "
            + " × ".join(preview(g, 40) for g in groups[:8])
            + f" ({len(groups)} groups; full factors in native_payload)."
        )
    lines.extend(
        [
            row["reason"],
            "Full original bindings, exact factors and any explicitly expanded declarations: native_payload. Original sources and generator: related().",
        ]
    )
    return lines


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
            for k in ALL_COLUMNS
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
