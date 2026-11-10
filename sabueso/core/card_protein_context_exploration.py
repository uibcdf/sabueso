"""Human reading and exact captured-input navigation for protein context."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _handle
from .card_protein_context_access import materialize
from .card_protein_context_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)

PANEL = "protein_context"
LINK_RULE = "protein_context_links@1"
HEADERS = (
    "Index",
    "Retained context",
    "Recorded direction",
    "Basis / source channel",
    "Source support",
)


def inherited_request(origin):
    request = origin.request if origin is not None else None
    return (
        request
        if isinstance(request, dict)
        and request.get("question")
        in ("protein_associations", "related_proteins", "sequence_differences")
        and request.get("topic") in ("associations", "comparative_context")
        else None
    )


def view(explorer, topic, origin=None, options=None):
    result = materialize(explorer.access, topic, options)
    captured = explorer._inspect(
        result.location(), origin, title=result.wire["schema"]["label"]
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(
            captured._selection,
            _result_ref=result.result_ref,
            _selection_ref=_handle(
                "XA_",
                {
                    "format": "protein_context_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel=PANEL,
        _native_override=result.native,
        _context_override=result.wire["context"],
        _request=origin.request if origin else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def open_item(item):
    row = item._entry.value
    # Original items remain accessible through the local result even if the
    # original captured input belongs to another explicit focal context.
    result = item._view._selection._scientific
    opened = item._view.explorer._inspect(
        result.location("rows", item._entry.key, "item"), item._view, title=item.label
    )
    return replace(
        opened, _native_override=deepcopy(row["item"]), _request=item._view.request
    )


def explain(item):
    result, explorer, key = (
        item._view._selection._scientific,
        item._view.explorer,
        item._entry.key,
    )
    opened = explorer._inspect(
        result.location("explanations", key),
        item._view,
        title="Recorded source bindings · " + item.label,
    )
    # The source list is metadata with exact original locations. Following a
    # foreign source explicitly switches its focal access through related().
    return replace(
        opened,
        _native_override=deepcopy(result.explanations[key]),
        _request=item._view.request,
    )


def links(item):
    from .card_context_navigation import _link, _link_view
    from .card_protein_context_access import anchor, location

    explorer, result, key = (
        item._view.explorer,
        item._view._selection._scientific,
        item._entry.key,
    )
    row, support = result.wire["rows"][key], result.wire["support"][key]
    records = []

    def add(role, label, loc, capture=None):
        record = _link(explorer, role, label, [support], location=loc)
        if capture is None and loc["kind"] == "card":
            capture = loc["card_ref"] or loc["snapshot_id"]
        if capture is not None:
            record["candidates"][0]["capture"] = capture
        record.update(label=label, rule=LINK_RULE)
        records.append(record)

    add("original_item", "Complete original record", row["original_location"])
    add(
        "original_scope",
        "Original support and interpretation",
        result.location("explanations", key),
    )
    for statement in support["source_assertions"]:
        if statement["location"] is not None:
            add(
                "source",
                "Source · " + statement["state"] + " · " + str(statement["id"]),
                statement["location"],
                statement["capture"],
            )
        else:
            records.append(
                {
                    "role": "source",
                    "label": "Source not retained · " + str(statement["id"]),
                    "target_ref": statement["id"],
                    "support": [support],
                    "rule": LINK_RULE,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    for capture in dict.fromkeys(
        (explorer.access._focal_key, *[r["capture"] for r in support.get("inputs", [])])
    ):
        add(
            "whole_card_context",
            "Complete supplied Card · " + capture,
            location(explorer.access, capture),
            capture,
        )
    target = row["object_ref"]
    if row["kind"] == "relationship":
        candidates = [
            {
                "capture": capture,
                "location": location(explorer.access, capture),
                "basis": "exact_source_object_identifier",
            }
            for capture, c in sorted(explorer.access._captures.items())
            if anchor(c) == target
        ]
        records.append(
            {
                "role": "object",
                "label": "Original relationship object · " + str(target),
                "target_ref": target,
                "support": [support],
                "rule": LINK_RULE,
                "availability": "available"
                if len(candidates) == 1
                else "ambiguous"
                if candidates
                else "not_supplied",
                "candidates": candidates,
                "paths": [],
                "blocked_paths": [],
            }
        )
    if row["kind"] == "supplied_capture":
        add(
            "supplied_capture",
            "Explicit supplied comparator",
            row["original_location"],
            target,
        )
        records.append(
            {
                "role": "question",
                "label": "Compare these captured sequences at equal positions",
                "target_ref": target,
                "support": [support],
                "rule": LINK_RULE,
                "availability": "available",
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
                "comparison_request": {
                    "question": "sequence_differences",
                    "reason": "Explicit local comparison; alignment and residue correspondence remain unestablished.",
                    "options": {"other_ref": target},
                },
            }
        )
    return _link_view(
        explorer,
        records,
        item._view,
        "Original protein context · " + item.label,
        source_location=row["original_location"],
        support_location=result.location("support", key),
        rule=LINK_RULE,
    )


def display_filter(view, column, value):
    validate_equality(column, value)
    entries = tuple(
        e
        for e in view._selected
        if equal(view._selection._scientific.value(e.key, column), value)
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=view._status if entries else "empty",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(value),
            "filter_policy": FORMAT,
        },
    )


def display_sort(view, column, descending=False, unit=None):
    entries = sorted_entries(
        view._selected, view._selection._scientific, column, descending, unit
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _display_request={
            "operation": "sort",
            "column": column,
            "descending": descending,
            "unit": unit,
            "sort_policy": FORMAT,
        },
    )


def opening(view, preview):
    return [
        "Relationship rows preserve original subject → predicate → object direction, qualifiers, source channels, conflicts and recorded derivations.",
        "Source IDs are recorded bindings; this view does not independently revalidate a provider mapping. Supplied Card rows are explicit comparison inputs, not asserted relationships.",
        "Sequence comparisons require an explicit supplied capture. equal_length_positions@1 compares equal integer positions without alignment, residue correspondence or identity inference; different lengths and unstated sequences stay unavailable.",
        "Inspect complete original records with open(), source bindings with explain(), and exact captured destinations with related(). Missing source and destination Cards remain explicit.",
        "Independent original saving is pending a clean producer capture and frozen reader; captured Card export remains available."
        if view._selection._scientific.native["rule"]["sabueso_version"]
        == "0.14.0+239.g738a422"
        else "Original records and explicit comparison inputs remain inspectable; captured Card export is available.",
    ]


def display_row(item, index, preview):
    r = item._entry.value
    basis = preview(r["basis"]) + " · " + preview(r["channel"])
    if r["kind"] == "sequence_comparison":
        if r["state"] == "available":
            basis += (
                " · "
                + str(r["difference_count"])
                + " positional differences · identical="
                + str(r["identical"])
            )
        else:
            native = r["item"].get("native_result") or {}
            basis += " · Unavailable: " + preview(
                native.get("basis", "unrecognized_sequence_shape")
            )
    return (
        str(index),
        preview(item.label),
        preview(r["subject_ref"]) + " → " + preview(r["object_ref"]),
        basis,
        preview(r["support_state"]),
    )
