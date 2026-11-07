"""Human publication reading over captured native literature and original support."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_literature_access import SUPPORT_FORMAT, TOPIC, materialize
from .card_literature_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)
from .errors import ArgumentError

LINK_RULE = "literature_context_links@1"


def view(explorer, origin, options=None):
    """Read the shared catalog or one exact retained publication."""
    result = materialize(explorer.access, options)
    focused = result.options["publication_ref"] is not None
    title = (
        "Retained publication · " + result.options["publication_ref"]
        if focused
        else "Publications linked to the captured Card"
    )
    captured = explorer._inspect(result.location(), origin, title=title)
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(
            captured._selection,
            _result_ref=result.result_ref,
            _selection_ref=_handle(
                "XA_",
                {
                    "format": "literature_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel=TOPIC,
        _native_override=result.wire["native_payload"],
        _context_override=result.wire["context"],
        _request=origin.request if origin is not None else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"].get("reason"),
        presentation="detail" if focused else "table",
    )


def open_item(item):
    """Open the complete cached native explanation of this publication."""
    return view(
        item._view._explorer,
        item._view,
        {"publication_ref": item._entry.value["publication_ref"]},
    )


def support(item):
    """Return original membership, keeping each citation route's support grain."""
    result = item._view._selection._scientific
    return [deepcopy(result.wire["support"][item._entry.key])]


def explain(item):
    """Inspect native publication support and its retained original assertions."""
    explorer, result = item._view._explorer, item._view._selection._scientific
    original = result.wire["support"][item._entry.key]
    native = result.wire["explanations"][item._entry.key]
    captured = explorer._inspect(
        original["explanation_location"],
        item._view,
        title=f"Original publication support · {item.label}",
    )
    entries = tuple(
        _Entry(
            statement["location"],
            statement["id"],
            explorer.access._resolve(statement["location"])[0],
        )
        for statement in original["source_assertions"]
        if statement["state"] == "present"
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(captured._selection, _entries=entries),
        _selected=entries,
        _native_override=native,
        _request=item._view.request,
        _status="partial" if native["status"] == "partial" else "ok",
        _reason=(
            "Some referenced original support is not retained; missing references and all available records remain inspectable."
            if native["status"] == "partial"
            else "Original publication links and source statements. ECO support, mentions, curation and measurement links retain their distinct meanings."
        ),
        _context_override={
            **result.wire["context"],
            "adapter": LINK_RULE,
            "literature_context": "publication_explanation",
            "native_status": native["status"],
            "native_reason": native["reason"],
        },
    )


def _membership(location, statement_id=None):
    """Keep complete membership once instead of repeating it for every link."""
    return [
        {
            "basis": "retained_support_membership",
            "rule": SUPPORT_FORMAT,
            "support_location": deepcopy(location),
            "statement_id": statement_id,
        }
    ]


def _missing(role, target, label, membership):
    return {
        "role": role,
        "label": label,
        "target_ref": target,
        "support": membership,
        "availability": "missing_prerequisite",
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
    }


def links(item):
    """List every original endpoint with one shared complete support membership."""
    from .card_context_navigation import _link, _link_view

    explorer, result = item._view._explorer, item._view._selection._scientific
    key = item._entry.key
    original = result.wire["support"][key]
    membership_location = result.location("support", key)
    rows = []
    for statement in original["source_assertions"]:
        identifier = statement["id"]
        membership = _membership(membership_location, identifier)
        if statement["state"] == "present":
            record = explorer.access._resolve(statement["location"])[0]
            source = record.get("source") or {}
            row = _link(
                explorer,
                "source",
                identifier,
                membership,
                location=statement["location"],
            )
            row["label"] = "Original source statement · " + " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    record.get("field_path"),
                    identifier,
                )
                if value is not None
            )
        else:
            row = _missing(
                "source",
                identifier,
                "Unavailable original source statement · " + identifier,
                membership,
            )
        rows.append(row)

    destinations = [
        (
            "publication_summary",
            "Complete original publication summary",
            original["summary_location"],
        ),
        (
            "publication_explanation",
            "Complete native publication explanation",
            original["explanation_location"],
        ),
        (
            "source_request_context",
            "Retained source coverage and quality",
            original["quality_location"],
        ),
        (
            "whole_card_context",
            "Complete original captured Card",
            original["whole_card_context_location"],
        ),
        (
            "literature_context",
            "Publication catalog scope and source coverage",
            original["context_location"],
        ),
        (
            "unresolved_eco",
            "Original unresolved ECO reference links",
            original["unresolved_eco_location"],
        ),
    ]
    for relationship in original["relationships"]:
        identifier = relationship["id"]
        if relationship["state"] == "present":
            location = relationship["location"]
            record = explorer.access._resolve(location)[0]
            destinations.append(
                (
                    "original_relationship",
                    "Original relationship · "
                    + str(record["predicate"])
                    + " · "
                    + identifier,
                    location,
                )
            )
        else:
            rows.append(
                _missing(
                    "original_relationship",
                    identifier,
                    "Unavailable original relationship · " + identifier,
                    _membership(membership_location),
                )
            )
    for locator in original["locator_locations"]:
        destinations.append((locator["role"], locator["label"], locator["location"]))
    for role, label, location in destinations:
        row = _link(
            explorer, role, label, _membership(membership_location), location=location
        )
        row["label"] = label
        rows.append(row)
    captured = _link_view(
        explorer,
        [{**row, "rule": LINK_RULE, "publication_ref": key} for row in rows],
        item._view,
        f"Original publication context · {item.label}",
        source_location=item.payload_location,
        support_location=membership_location,
        rule=LINK_RULE,
        reason="Each destination retains its original relationship, source-statement or locator grain. All publication links remain available, including unavailable original references.",
    )
    return replace(
        captured,
        _context_override={
            **result.wire["context"],
            "literature_context": "related",
        },
    )


def follow(item):
    """Open an exact retained endpoint and preserve its originating return path."""
    explorer, link = item._view._explorer, item._entry.value
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
                "literature_context": link["role"],
                "publication_ref": link["publication_ref"],
            },
        )
    captured = explorer._metadata(
        {"link": link}, "Original publication input unavailable", item._view
    )
    return replace(
        captured,
        _request=item._view.request,
        _status=link["availability"],
        _context_only=True,
        _reason="The referenced original record is not retained. Its reference remains inspectable; no replacement statement or article content is inferred.",
        _context_override={
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": LINK_RULE,
            "literature_context": link["role"],
            "publication_ref": link["publication_ref"],
            "captures": explorer.context["captures"],
        },
    )


def display_filter(view, column, equals):
    """Select original publications without changing their native source scope."""
    validate_equality(column, equals)
    result = view._selection._scientific
    unavailable = view._status not in ("ok", "empty")
    if unavailable and not result.entries:
        raise ArgumentError(
            "This literature view has no retained rows available for display filtering."
        )
    entries = tuple(
        entry
        for entry in view._selected
        if equal(result.value(entry.key, column), equals)
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=view._status if unavailable else "ok" if entries else "empty",
        _reason=view._reason
        if unavailable
        else None
        if entries
        else "No publications match this display selection; the original catalog and source scope are unchanged.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
            "filter_policy": FORMAT,
        },
    )


def display_sort(view, column, descending=False, unit=None):
    """Order the current display subset with original membership unchanged."""
    entries = sorted_entries(
        view._selected,
        view._selection._scientific,
        column,
        descending=descending,
        unit=unit,
    )
    return replace(
        view,
        _selected=tuple(entries),
        _origin=view,
        _display_request={
            "operation": "sort",
            "column": column,
            "descending": descending,
            "unit": unit,
            "selection_policy": FORMAT,
        },
    )
