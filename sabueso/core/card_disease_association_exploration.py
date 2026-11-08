"""Human disease association navigation over explicitly retained input pins."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_disease_association_access import SUPPORT_FORMAT, materialize
from .card_disease_association_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)

LINK_RULE = "disease_association_context_links@1"


def view(explorer, origin, options=None):
    result = materialize(explorer.access, options)
    captured = explorer._inspect(
        result.location(), origin, title="Retained molecular and clinical associations"
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
                    "format": "disease_association_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel="associations",
        _native_override=result.native,
        _context_override=result.wire["context"],
        _request=origin.request if origin else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def _context(parent, role):
    return {
        **parent._explorer.context,
        "adapter": LINK_RULE,
        "association_context": role,
        "disease_card_ref": parent.context["disease_card_ref"],
    }


def open_item(item):
    explorer, result = item._view.explorer, item._view._selection._scientific
    captured = explorer._inspect(
        result.location("rows", item._entry.key, "item"), item._view, title=item.label
    )
    return replace(
        captured,
        _native_override=deepcopy(item._entry.value["item"]),
        _request=item._view.request,
        _context_override=_context(item._view, "original_item"),
    )


def explain(item):
    explorer, result, key = (
        item._view.explorer,
        item._view._selection._scientific,
        item._entry.key,
    )
    support = result.wire["support"][key]
    captured = explorer._inspect(
        result.location("explanations", key),
        item._view,
        title="Original association support · " + item.label,
    )
    entries = tuple(
        _Entry(
            record["location"],
            record["id"],
            explorer.access._resolve(record["location"])[0],
        )
        for record in support["source_assertions"]
        if record["location"] is not None
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(captured._selection, _entries=entries),
        _selected=entries,
        _native_override=result.explanations[key],
        _request=item._view.request,
        _status="ok" if support["state"] in ("retained", "context_only") else "partial",
        _reason="Association, chemical identity and disease equivalence sources retain separate roles and subjects.",
        _context_override=_context(item._view, "explanation"),
    )


def links(item):
    from .card_context_navigation import _link_view

    explorer, result, key = (
        item._view.explorer,
        item._view._selection._scientific,
        item._entry.key,
    )
    support = result.wire["support"][key]
    captured = support["context_capture"]
    owner = explorer.access._captures[captured]
    membership = [
        {
            "basis": "retained_support_membership",
            "rule": SUPPORT_FORMAT,
            "support_location": result.location("support", key),
        }
    ]
    destinations = [
        (
            "original_item",
            "Complete original association or context item",
            result.location("rows", key, "item"),
            explorer.access._focal_key,
        ),
        (
            "native_context",
            "Complete captured disease association scope",
            result.location("native_payload"),
            explorer.access._focal_key,
        ),
        (
            "source_request_context",
            "Original input knowledge and request states",
            result.location("coverage"),
            explorer.access._focal_key,
        ),
        (
            "original_location",
            "Exact original input occurrence",
            support["original_location"],
            captured,
        ),
        (
            "whole_card_context",
            "Complete original supplied Card",
            {**support["original_location"], "segments": []},
            captured,
        ),
        (
            "original_quality",
            "Original supplied Card request outcomes",
            {
                "format": "card_access_location@1",
                "kind": "card",
                "card_ref": owner.pin,
                "snapshot_id": owner.snapshot,
                "segments": [{"type": "Key", "value": "quality"}],
            },
            captured,
        ),
    ]
    rows = []
    for source in support["source_assertions"]:
        if source["location"] is not None:
            destinations.append(
                (
                    "source",
                    f"Source · {source['role']} · {source['state']} · {source['id']}",
                    source["location"],
                    source["capture"],
                )
            )
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Original source not retained · " + source["id"],
                    "target_ref": source["id"],
                    "support": membership,
                    "rule": LINK_RULE,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    for path in support.get("identity", {}).get("paths", []):
        for step in (path, path.get("terminal_identity", {})):
            location = step.get("relationship_location")
            if location is not None:
                owner_key = next(
                    key
                    for key, owner in explorer.access._captures.items()
                    if owner.pin == location["card_ref"]
                    and owner.snapshot == location["snapshot_id"]
                )
                destinations.append(
                    (
                        "identity_relationship",
                        "Exact original identity relationship",
                        location,
                        owner_key,
                    )
                )
    for role, label, location, capture in destinations:
        rows.append(
            {
                "role": role,
                "label": label,
                "target_ref": label,
                "support": deepcopy(membership),
                "rule": LINK_RULE,
                "availability": "available",
                "candidates": [
                    {
                        "location": deepcopy(location),
                        "capture": capture,
                        "basis": "exact_retained_node",
                    }
                ],
                "paths": [],
                "blocked_paths": [],
            }
        )
    linked = _link_view(
        explorer,
        rows,
        item._view,
        "Original association inputs · " + item.label,
        source_location=item.payload_location,
        support_location=result.location("support", key),
        rule=LINK_RULE,
        reason="Exact supplied captures and original source roles; no lookup, similarity identity or causal inference.",
    )
    return replace(linked, _context_override=_context(item._view, "related"))


def follow(item):
    from .card_exploration_storage import _explorer

    parent, link = item._view, item._entry.value
    explorer = parent._explorer
    if len(link["candidates"]) != 1:
        captured = explorer._metadata(
            {"link": deepcopy(link)}, "Original source unavailable", parent
        )
        return replace(
            captured,
            _request=parent.request,
            _status="missing_prerequisite",
            _context_only=True,
            _context_override=_context(parent, "missing_source"),
            _reason="The original reference is retained without a replacement source assertion.",
        )
    candidate = link["candidates"][0]
    destination = _explorer(
        explorer.access._for_capture(candidate["capture"]), explorer._session
    )
    destination._origin = parent
    node, full = destination.access._resolve(candidate["location"])
    captured = destination._inspect(full, parent, title=link["label"])
    return replace(
        captured,
        _native_override=node,
        _request=parent.request,
        _context_override={
            **destination.context,
            "adapter": LINK_RULE,
            "association_context": link["role"],
            "disease_card_ref": parent.context["disease_card_ref"],
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
        else "No retained association rows match; original source and input scope are unchanged.",
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
