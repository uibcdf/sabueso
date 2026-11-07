"""Human drill-down over captured bioactivity results and original source context."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_bioactivity_access import TOPIC, materialize
from .card_bioactivity_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)
from .errors import ArgumentError

LINK_RULE = "bioactivity_context_links@1"


def view(explorer, origin, options=None):
    result = materialize(explorer.access, options)
    title = {
        "molecule": "Molecules with retained bioactivity measurements",
        "group": "Native measurement groups",
        "record": "Original source activity records",
    }[result.wire["context"]["grain"]]
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
                    "format": "bioactivity_human_selection@1",
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
        presentation="table",
    )


def open_item(item):
    parent, row = item._view, item._entry.value
    options = deepcopy(parent._selection._scientific.options)
    if row["kind"] == "bioactivity_molecule":
        options.update(molecule_ref=row["molecule_ref"], measurement_ref=None)
        return view(parent._explorer, parent, options)
    if row["kind"] == "bioactivity_group":
        options.update(
            molecule_ref=row["molecule_ref"], measurement_ref=row["measurement_ref"]
        )
        return view(parent._explorer, parent, options)
    return replace(
        parent,
        _selected=(item._entry,),
        _origin=parent,
        _display_request=None,
        _native_override=row["item"],
        title=f"Original source activity record · {row['label']}",
        presentation="detail",
    )


def payload(item):
    return item._view._selection._scientific.wire


def support(item):
    return [deepcopy(payload(item)["support"][item._entry.key])]


def explain(item):
    explorer, result = item._view._explorer, item._view._selection._scientific
    captured = explorer._inspect(
        result.location("explanations", item._entry.key),
        item._view,
        title=f"Original bioactivity support · {item.label}",
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
        _request=item._view.request,
        _reason=(
            "Original activity/assay statements and retained native interpretation. "
            "Missing references remain explicit through support_location. Citation "
            "fields do not imply a separate document SourceAssertion or article reading."
        ),
    )


def links(item):
    from .card_context_navigation import _link, _link_view

    explorer, result = item._view._explorer, item._view._selection._scientific
    basis = support(item)
    original, rows = basis[0], []
    for statement in original["source_assertions"]:
        if statement["state"] == "present":
            row = _link(
                explorer,
                "source",
                statement["id"],
                basis,
                location=statement["location"],
            )
            record = explorer.access._resolve(statement["location"])[0]
            source = record.get("source", {})
            source = source if isinstance(source, dict) else {}
            row["label"] = "Original source statement · " + " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    record.get("field_path"),
                    statement["id"],
                )
                if value is not None
            )
        else:
            row = {
                "role": "source",
                "label": "Unavailable original source statement · " + statement["id"],
                "target_ref": statement["id"],
                "support": deepcopy(basis),
                "availability": "missing_prerequisite",
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
            }
        rows.append(row)
    destinations = [
        (
            "original_record",
            "Complete retained native item",
            result.location("rows", item._entry.key, "item"),
        ),
        ("assay_context", "Retained assay context", original["assay_context_location"]),
        (
            "citation_context",
            "Retained citation context",
            original["citation_context_location"],
        ),
        (
            "measurement_context",
            "Whole native grouping and interpretation context",
            original["context_location"],
        ),
        (
            "whole_card_context",
            "Original captured Card and molecule glossary",
            original["whole_card_context_location"],
        ),
        (
            "source_request_context",
            "Retained source coverage and quality",
            result.wire["context"]["quality_location"],
        ),
    ]
    for location in original["relationship_locations"]:
        record = explorer.access._resolve(location)[0]
        destinations.append(
            (
                "original_relationship",
                "Original bioactivity relationship · " + str(record["id"]),
                location,
            )
        )
    for location in original["publication_context_locations"]:
        publication = explorer.access._resolve(location)[0]
        destinations.append(
            (
                "publication_context",
                "Exact retained publication context · "
                + str(publication["publication_ref"]),
                location,
            )
        )
    for role, label, location in destinations:
        row = _link(explorer, role, label, basis, location=location)
        row["label"] = label
        rows.append(row)
    return _link_view(
        explorer,
        [{**row, "rule": LINK_RULE} for row in rows],
        item._view,
        f"Retained activity context · {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
        reason="Exact retained activity, assay and citation destinations; citation context is not a document SourceAssertion, article content or independent evidence.",
    )


def follow(item):
    """Open exact retained context with its original label and return path."""
    explorer, link = item._view._explorer, item._entry.value
    if len(link["candidates"]) == 1:
        location = link["candidates"][0]["location"]
        node = explorer.access._resolve(location)[0]
        if link["role"] == "publication_context" and explorer.mode == "live":
            from .card_bioactivity_access import _native

            original_summary = node
            node = _native(
                explorer.access, "explain_literature", node["publication_ref"]
            )
            location = explorer.access._object_location(
                {
                    "original_summary": original_summary,
                    "original_explanation": node,
                    "publication_ref": original_summary["publication_ref"],
                }
            )
        captured = explorer._inspect(location, item._view, title=link["label"])
        return replace(
            captured,
            _native_override=node,
            _request=item._view.request,
            _context_override={
                **explorer.context,
                "adapter": LINK_RULE,
                "bioactivity_context": link["role"],
            },
        )
    captured = explorer._metadata(
        {"link": link}, "Original source statement unavailable", item._view
    )
    return replace(
        captured,
        _request=item._view.request,
        _status=link["availability"],
        _reason="The referenced original source statement is not retained; no replacement or attribution is inferred.",
        _context_only=True,
        _context_override={
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": LINK_RULE,
            "bioactivity_context": link["role"],
            "captures": explorer.context["captures"],
        },
    )


def display_filter(view, column, equals):
    validate_equality(column, equals)
    result = view._selection._scientific
    if view._status not in ("ok", "empty") and not result.entries:
        raise ArgumentError(
            "This bioactivity view has no retained rows available for display filtering."
        )
    entries = tuple(
        entry
        for entry in view._selected
        if equal(result.value(entry.key, column), equals)
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
        else "No items match this display selection; the original source scope is unchanged.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
            "filter_policy": FORMAT,
        },
    )


def display_sort(view, column, descending=False, unit=None):
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
