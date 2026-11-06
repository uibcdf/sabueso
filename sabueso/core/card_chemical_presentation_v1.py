"""Original chemical human presentation and selected original input helpers."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry
from .card_chemical_selection_v1 import FLAGS, equal, validate_equality

LINK_RULE = "chemical_classification_links@1"
HEADERS = ("Index", "Term", "Kind", "Assignment", "Support")
ASSIGNMENTS = {
    "class_membership": "Chemical class membership",
    "direct": "Directly assigned role",
    "inherited": "Inherited role",
    "not_stated": "Assignment not stated",
    "unrecognized": "Unrecognized assignment",
    "unknown": "Assignment unknown",
}
STATES = {
    "source_supported": "Source-supported",
    "support_unknown": "Original support not established",
    "unrecognized_term": "Unrecognized retained term",
}
REASONS = {
    "exact_original_field_member": "Exact member of a selected original statement with a coherent source-stated molecular identity.",
    "invalid_chebi_term": "The retained identifier cannot be admitted as a ChEBI term; inspect its original value.",
    "selected_support_not_declared": "Selected original source support is not declared.",
    "no_eligible_original_member": "No exact selected original member with a coherent focal identity supports this retained value.",
}


def payload(item):
    return item._view.explorer.access._objects[item._entry.location["result_ref"]]


def support(item):
    return [deepcopy(payload(item)["support"][item._entry.key])]


def explain(item):
    explorer = item._view.explorer
    result = item._view._selection._scientific
    location = result.location("explanations", item._entry.key)
    captured = explorer._inspect(
        location, item._view, title=f"Original support · {item.label}"
    )
    entries = tuple(
        _Entry(
            statement["location"],
            statement["id"],
            explorer.access._resolve(statement["location"])[0],
        )
        for statement in support(item)[0]["source_assertions"]
        if statement["state"] == "present"
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(captured._selection, _entries=entries),
        _selected=entries,
        _native_override=result.wire["explanations"][item._entry.key],
        _reason="Original selected field and identity statements. Full field checks, alternatives, conflicts and missing references remain available through native_payload destinations.",
    )


def links(item):
    from .card_context_navigation import _link, _link_view

    explorer, basis = item._view.explorer, support(item)
    rows = []
    for statement in basis[0]["source_assertions"]:
        if statement["state"] == "present":
            link = _link(
                explorer,
                "source",
                statement["id"],
                basis,
                location=statement["location"],
            )
            original = explorer.access._resolve(statement["location"])[0]
            source = original.get("source", {})
            source = source if isinstance(source, dict) else {}
            field_label = {
                "annotations.chemical_classes": "Chemical classes",
                "annotations.chemical_roles": "Chemical roles",
                "relationships.same_as": "Explicit molecular identity",
            }.get(original.get("field_path"), "Original source statement")
            link["label"] = " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    field_label,
                )
                if value is not None
            )
            rows.append(link)
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Unavailable original input · " + statement["id"],
                    "target_ref": statement["id"],
                    "support": deepcopy(basis),
                    "rule": LINK_RULE,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    for role, label, location in (
        (
            "original_member",
            "Original retained class or role",
            basis[0]["original_field_member_location"],
        ),
        (
            "original_field",
            "Field support checks, alternatives and original node",
            basis[0]["field_context_location"],
        ),
        (
            "identity_context",
            "Original source-stated molecular identity",
            basis[0]["identity_bindings_location"],
        ),
        (
            "source_request_context",
            "Source coverage and stored quality",
            explorer._location("quality"),
        ),
    ):
        link = _link(explorer, role, label, basis, location=location)
        link["label"] = label
        rows.append(link)
    return _link_view(
        explorer,
        [{**row, "rule": LINK_RULE} for row in rows],
        item._view,
        f"Original context · {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
    )


def display_filter(view, column, equals):
    validate_equality(column, equals)
    entries = tuple(
        item._entry for item in view.items() if equal(item.cells[column]._value, equals)
    )
    # An empty display selection cannot turn unknown science into an empty source.
    unavailable = view._status not in ("ok", "empty")
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=view._status if unavailable else "ok" if entries else "empty",
        _reason=view._reason
        if unavailable
        else None
        if entries
        else "No items match this display selection.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
            "filter_policy": "chemical_classification_selection@1",
        },
    )


def display_row(item, index, preview):
    row = item._entry.value
    return (
        str(index),
        preview(f"{item.label} · {row['term_ref']}"),
        "Chemical class" if row["kind"] == "chemical_class" else "Source-stated role",
        ASSIGNMENTS[row["assignment"]],
        STATES[row["state"]],
    )


def opening(view, preview):
    native = view._selection._scientific.wire["native_payload"]
    names = view._explorer.access._focal.data.get("sections", {}).get("names")
    name = names.get("canonical_name") if isinstance(names, dict) else None
    name = name.get("value") if isinstance(name, dict) else None
    name = name if isinstance(name, str) and name else "Name not retained"
    identity = native["focal_ref"] or "Focal chemical identity not established"
    lines = [
        f"Molecule: {preview(name)} · {preview(identity)}",
        "Retained source chemical classes and roles, not target-specific activity, mechanism or therapeutic effect.",
        "Direct/inherited labels follow retained source assignments. Missing entries or support do not establish source-wide absence.",
    ]
    status = {
        "ok": "Retained source statements support these entries and assignments",
        "partial": "Partly supported or incompletely stated",
        "empty": "Explicitly retained empty class and role lists",
        "unknown": "Retained context insufficient for interpretation",
        "missing_prerequisite": "Focal chemical identity unavailable or inconsistent",
        "not_applicable": "Chemical classification does not apply to this Card nature",
    }
    lines.append("Interpretation status: " + status[native["status"]] + ".")
    field_states = {
        "not_retained": "not retained",
        "retained_null": "retained null",
        "retained_empty": "explicitly retained empty list",
        "unrecognized_shape": "unrecognized retained shape",
        "retained": "retained list",
    }
    lines.append(
        "Retained fields: "
        + "; ".join(
            f"{label}: {field_states[native['fields'][path]['state']]}"
            for label, path in (
                ("classes", "annotations.chemical_classes"),
                ("roles", "annotations.chemical_roles"),
            )
        )
    )
    if native["stored_conflicts"] or native["stored_alternatives"]:
        lines.append(
            "Stored conflicts or alternatives are retained; inspect native_payload and each item's original field context."
        )
    lines.append(
        "Open an item for its original value and category flags; explain() shows source statements, related() opens original fields/identity/coverage, and back() returns to your selection."
    )
    lines.append(
        "Support refers to original whole-field statements and exact member positions."
    )
    lines.append(
        "Saving preserves the original chemical interpretation, source statements and visited navigation for independent reading."
    )
    if view.presentation == "detail" and view._selected:
        row = view._selected[0].value
        lines.append(REASONS[row["reason"]])
        if row["kind"] == "chemical_role":
            labels = {
                "biological_role": "Biological role",
                "chemical_role": "Chemical role",
                "application": "Application",
            }
            lines.append(
                "Retained source category flags: "
                + "; ".join(
                    f"{labels[flag]}: {'unknown' if row[flag] is None else 'yes' if row[flag] else 'no'}"
                    for flag in FLAGS
                )
            )
        lines.append(
            "Complete original selected value: "
            + preview(row["item"]["value"], limit=480)
        )
    return lines
