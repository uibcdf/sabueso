"""Readable assembly-generation findings over one captured native @4 result."""

from collections import Counter
from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_assembly_selection_v1 import COLUMNS as ALL_COLUMNS
from .errors import ArgumentError

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


def options_for_assembly(options):
    from sabueso._private.argdigest.argument.relationship_id import (
        digest_relationship_id,
    )
    from sabueso._private.argdigest.argument.structure_ref import digest_structure_ref

    from .assembly_requests import DEFAULT_OPERATION_BUDGET, budget

    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - {
        "structure_ref",
        "relationship_id",
        "expand_operations",
        "expand_occurrences",
        "operation_budget",
    }:
        raise ArgumentError(
            "assembly_generation options: structure_ref, relationship_id, expand_operations, expand_occurrences and operation_budget only."
        )
    result = {
        "structure_ref": digest_structure_ref(options.get("structure_ref")),
        "relationship_id": digest_relationship_id(options.get("relationship_id")),
        "expand_operations": options.get("expand_operations", False),
        "expand_occurrences": options.get("expand_occurrences", False),
        "operation_budget": budget(
            options.get("operation_budget", DEFAULT_OPERATION_BUDGET)
        ),
    }
    for name in ("expand_operations", "expand_occurrences"):
        if type(result[name]) is not bool:
            raise ArgumentError(f"{name} requires a boolean.", argument=name)
    if result["relationship_id"] is not None and result["structure_ref"] is None:
        raise ArgumentError(
            "relationship_id requires structure_ref.", argument="relationship_id"
        )
    return result


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
    from .assembly_generation_v4 import generation
    from .card_ligand_site_exploration import _location, _statement
    from .card_scientific_access import _CapturedCard

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
    from .card_assembly_access import result_location

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


def view(explorer, origin, options):
    selection = explorer.access.select(TOPIC, options=options)
    result = selection._scientific
    base = explorer._inspect(
        result.location("native_payload"),
        origin,
        title="Assembly components and operations",
    )
    explorer._session["views"].pop(id(base), None)
    return replace(
        base,
        _selection=selection,
        _selected=result.entries,
        _record_panel=TOPIC,
        _native_override=result.wire["native_payload"],
        _context_override=result.wire["context"],
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def support(item):
    return [
        deepcopy(
            item._view.explorer.access._objects[item._view.result_ref]["support"][
                item._entry.key
            ]
        )
    ]


def explain(item):
    explorer = item._view.explorer
    result = item._view._selection._scientific
    body = result.wire["explanations"][item._entry.key]
    base = explorer._inspect(
        result.location("explanations", item._entry.key),
        item._view,
        title=f"Original assembly inputs · {item.label}",
    )
    entries = tuple(
        _Entry(s["location"], s["id"], explorer.access._resolve(s["location"])[0])
        for s in support(item)[0]["source_assertions"]
        if s["state"] == "present"
    )
    explorer._session["views"].pop(id(base), None)
    return replace(
        base,
        _selection=replace(base._selection, _entries=entries),
        _selected=entries,
        _native_override=body,
        _reason=item._entry.value["reason"]
        + " Complete original input and source/request destinations remain in native_payload.",
    )


def links(item):
    from .card_context_navigation import _link, _link_view

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
