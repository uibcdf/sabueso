"""Human clinical reading and exact retained source navigation."""

from copy import deepcopy
from dataclasses import replace

from ..card_access import _Entry, _handle
from .adapter import SUPPORT_FORMAT, materialize
from .selection import FORMAT, equal, sorted_entries, validate_equality

LINK_RULE = "clinical_context_links@1"


def view(explorer, origin, options=None):
    result = materialize(explorer.access, options)
    captured = explorer._inspect(
        result.location(), origin, title="Indications and clinical studies"
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
                    "format": "clinical_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel="clinical",
        _native_override=result.native,
        _context_override=result.wire["context"],
        _request=origin.request if origin else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def open_item(item):
    explorer, result = item._view.explorer, item._view._selection._scientific
    captured = explorer._inspect(
        result.location("rows", item._entry.key, "item"), item._view, title=item.label
    )
    return replace(
        captured,
        _native_override=deepcopy(item._entry.value["item"]),
        _request=item._view.request,
        _context_override={
            **result.wire["context"],
            "adapter": LINK_RULE,
            "clinical_context": "original_item",
        },
    )


def explain(item):
    explorer, result, key = (
        item._view.explorer,
        item._view._selection._scientific,
        item._entry.key,
    )
    original = result.wire["support"][key]
    captured = explorer._inspect(
        result.location("explanations", key),
        item._view,
        title="Original clinical support · " + item.label,
    )
    entries = tuple(
        _Entry(
            record["location"],
            record["id"],
            explorer.access._resolve(record["location"])[0],
        )
        for record in original["source_assertions"]
        if record["location"] is not None
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(captured._selection, _entries=entries),
        _selected=entries,
        _native_override=result.explanations[key],
        _request=item._view.request,
        _status="ok" if original["state"] == "retained" else "partial",
        _reason="Original role-bound source membership; each assertion keeps its own subject. Unverified support remains explicitly labelled in native_payload.",
        _context_override={
            **result.wire["context"],
            "adapter": LINK_RULE,
            "clinical_context": "explanation",
        },
    )


def links(item):
    from .navigation import _link, _link_view

    explorer, result, key = (
        item._view.explorer,
        item._view._selection._scientific,
        item._entry.key,
    )
    original = result.wire["support"][key]
    membership = [
        {
            "basis": "retained_support_membership",
            "rule": SUPPORT_FORMAT,
            "support_location": result.location("support", key),
        }
    ]
    rows = []
    destinations = [
        (
            "original_item",
            "Complete native clinical item",
            result.location("rows", key, "item"),
        ),
        (
            "clinical_context",
            "Complete native clinical view",
            result.location("native_payload"),
        ),
        (
            "source_request_context",
            "Original clinical request coverage",
            result.location("coverage"),
        ),
        (
            "original_quality",
            "Original stored request outcomes and limits",
            original["quality_location"],
        ),
        (
            "whole_card_context",
            "Complete captured Card",
            original["whole_card_context_location"],
        ),
    ]
    for record in original["source_assertions"]:
        label = f"Source · {record['role']} · {record['state']} · {record['id']}"
        if record["location"] is not None:
            destinations.append(("source", label, record["location"]))
        else:
            rows.append(
                {
                    "role": "source",
                    "label": label,
                    "target_ref": record["id"],
                    "support": membership,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    for record in original["relationships"]:
        destinations.append(
            (
                "original_relationship",
                "Original clinical relationship · " + record["id"],
                record["location"],
            )
        )
    if "indication_row_key" in original:
        destinations.append(
            (
                "original_indication",
                "Complete original indication and cited trial list",
                result.location("rows", original["indication_row_key"], "item"),
            )
        )
    for destination in original.get("registry_row_keys", []):
        destinations.append(
            (
                "registry_record",
                "Exact retained trial context · "
                + result.value(destination, "trial_ref"),
                result.location("rows", destination, "item"),
            )
        )
    for role, label, location in destinations:
        row = _link(explorer, role, label, membership, location=location)
        row["label"] = label
        rows.append(row)
    captured = _link_view(
        explorer,
        [{**row, "rule": LINK_RULE} for row in rows],
        item._view,
        "Original clinical context · " + item.label,
        source_location=item.payload_location,
        support_location=result.location("support", key),
        rule=LINK_RULE,
        reason="Exact retained clinical items, role-bound assertions and original request scope; no source acquisition or name-based trial matching.",
    )
    return replace(
        captured,
        _context_override={
            **result.wire["context"],
            "adapter": LINK_RULE,
            "clinical_context": "related",
        },
    )


def follow(item):
    explorer, link = item._view.explorer, item._entry.value
    if len(link["candidates"]) == 1:
        location = link["candidates"][0]["location"]
        node = explorer.access._resolve(location)[0]
        captured = explorer._inspect(location, item._view, title=link["label"])
        return replace(
            captured,
            _native_override=node,
            _request=item._view.request,
            _context_override={
                **explorer.context,
                "adapter": LINK_RULE,
                "clinical_context": link["role"],
            },
        )
    captured = explorer._metadata(
        {"link": link}, "Original clinical input unavailable", item._view
    )
    return replace(
        captured,
        _request=item._view.request,
        _status="missing_prerequisite",
        _context_only=True,
        _reason="The original support record is not retained; its reference is preserved without a replacement statement.",
        _context_override={
            **explorer.context,
            "adapter": LINK_RULE,
            "clinical_context": "missing_source",
        },
    )


def display_filter(view, column, equals):
    validate_equality(column, equals)
    result = view._selection._scientific
    entries = tuple(
        e for e in view._selected if equal(result.value(e.key, column), equals)
    )
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
        else "No retained clinical rows match; original source and request scope are unchanged.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
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
