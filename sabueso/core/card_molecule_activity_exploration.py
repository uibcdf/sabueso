"""Human navigation over exact molecule joins into supplied activity contexts."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_molecule_activity_access import TOPIC, materialize
from .card_molecule_activity_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)
from .errors import ArgumentError

LINK_RULE = "molecule_activity_context_links@1"


def view(explorer, origin, options=None):
    """Open one shared result without changing its original scientific scope."""
    result = materialize(explorer.access, options)
    title = {
        "target": "Targets, measurements and assay context",
        "group": "Native measurement groups in the exact target context",
        "record": "Original source activity records in the exact target context",
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
                    "format": "molecule_activity_human_selection@1",
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
    """Drill down through an exact target pin, native group and original record."""
    parent, row = item._view, item._entry.value
    options = deepcopy(parent._selection._scientific.options)
    if row["kind"] == "activity_context_target":
        options.update(target_card_ref=row["target_card_ref"], measurement_ref=None)
        return view(parent._explorer, parent, options)
    if row["kind"] == "activity_context_group":
        options.update(
            target_card_ref=row["target_card_ref"],
            molecule_ref=row["molecule_ref"],
            measurement_ref=row["measurement_ref"],
        )
        return view(parent._explorer, parent, options)
    return replace(
        parent,
        _selected=(item._entry,),
        _origin=parent,
        _display_request=None,
        _native_override=deepcopy(row["item"]),
        _context_override={**parent.context, "target_card_ref": row["target_card_ref"]},
        title=f"Original source activity record · {row['label']}",
        presentation="detail",
    )


def support(item):
    """Retain complete identity/native support and unavailable references."""
    return [
        deepcopy(item._view._selection._scientific.wire["support"][item._entry.key])
    ]


def _root_view(origin):
    """Find the actual target selection from which this drill-down started."""
    seen = set()
    while origin is not None and id(origin) not in seen:
        seen.add(id(origin))
        if origin._record_panel == TOPIC:
            result = origin._selection._scientific
            if result.wire["context"]["grain"] == "target":
                return origin
        origin = origin._origin
    return None


def _navigation(item):
    parent, row = item._view, item._entry.value
    result = parent._selection._scientific
    root = _root_view(parent)
    return {
        "rule": LINK_RULE,
        "source_result_ref": result.result_ref,
        "source_row_key": item._entry.key,
        "source_location": deepcopy(item.payload_location),
        "molecule_card_ref": row["molecule_card_ref"],
        "target_card_ref": row["target_card_ref"],
        "molecule_root_view_ref": root.view_ref if root is not None else None,
        "molecule_root_selection": _selection_binding(root)
        if root is not None
        else None,
        "parent_selection": _selection_binding(parent),
        "original_request": parent.request,
        "scientific_options": deepcopy(result.options),
        "identity_edges": deepcopy(support(item)[0]["identity_edges"]),
    }


def _selection_binding(view):
    return {
        "view_ref": view.view_ref,
        "selection_ref": view._selection.selection_ref,
        "selected_locations": [deepcopy(entry.location) for entry in view._selected],
        "display_request": deepcopy(view._display_request),
        "request": view.request,
        "outcome": view.outcome,
        "presentation": view.presentation,
    }


def _context(parent, navigation, role):
    return {
        **parent.context,
        "adapter": LINK_RULE,
        "activity_context": role,
        "molecule_card_ref": navigation["molecule_card_ref"],
        "target_card_ref": navigation["target_card_ref"],
        "molecule_activity_navigation": deepcopy(navigation),
    }


def explain(item):
    """Inspect original identity and activity support at its recorded grain."""
    parent, result = item._view, item._view._selection._scientific
    explorer = parent._explorer
    captured = explorer._inspect(
        result.location("explanations", item._entry.key),
        parent,
        title=f"Original molecule and target activity support · {item.label}",
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
        _context_override=_context(parent, _navigation(item), "support"),
        _request=parent.request,
        _reason=(
            "Exact retained identity relationships and native activity/assay support; "
            "missing references and original source outcomes remain explicit. "
            "Citation metadata does not imply article reading or independent evidence."
        ),
    )


def _located_link(explorer, role, label, location, basis, navigation):
    from .card_context_navigation import _link

    row = _link(explorer, role, label, basis, location=location)
    row.update(
        label=label, rule=LINK_RULE, molecule_activity_navigation=deepcopy(navigation)
    )
    if location["kind"] == "card":
        capture = next(
            key
            for key, captured in explorer.access._captures.items()
            if captured.pin == location["card_ref"]
            and captured.snapshot == location["snapshot_id"]
        )
        row["candidates"][0]["capture"] = capture
    return row


def links(item):
    """Expose exact join, source, assay, record and full target destinations."""
    from .card_context_navigation import _link_view

    parent, explorer = item._view, item._view._explorer
    result, basis = parent._selection._scientific, support(item)
    original, navigation = basis[0], _navigation(item)
    rows = []
    for statement in original["source_assertions"]:
        if statement["state"] == "present":
            node = explorer.access._resolve(statement["location"])[0]
            source = node.get("source", {})
            source = source if isinstance(source, dict) else {}
            label = "Original source statement · " + " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    node.get("field_path"),
                    statement["id"],
                )
                if value is not None
            )
            row = _located_link(
                explorer, "source", label, statement["location"], basis, navigation
            )
            row["target_ref"] = statement["id"]
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
                "rule": LINK_RULE,
                "molecule_activity_navigation": deepcopy(navigation),
            }
        rows.append(row)
    destinations = [
        (
            "molecule_context",
            "Original focal molecule and exact identity anchor",
            original["whole_card_context_location"],
        ),
        (
            "target_context",
            "Original supplied protein context · " + str(navigation["target_card_ref"]),
            original["target_card_location"],
        ),
        (
            "target_card",
            "Open the supplied protein Card explicitly · "
            + str(navigation["target_card_ref"]),
            original["target_card_location"],
        ),
        (
            "identity_context",
            "Complete retained molecule identity joins and diagnostics",
            result.location("native_payload", "identity"),
        ),
        (
            "original_record",
            "Complete retained activity item",
            result.location("rows", item._entry.key, "item"),
        ),
    ]
    for location in original["relationship_locations"]:
        relationship = explorer.access._resolve(location)[0]
        destinations.append(
            (
                "original_relationship",
                "Original identity or activity relationship · "
                + str(relationship["id"]),
                location,
            )
        )
    for member, native_member in zip(
        original["native_supports"], result.native_members(item._entry.key), strict=True
    ):
        native_access, native_result, native_entry = native_member
        native_support = member["support"]
        destinations.extend(
            (
                (
                    "native_record",
                    "Complete original native activity item · "
                    + member["molecule_ref"],
                    native_result.location("rows", native_entry.key, "item"),
                ),
                (
                    "assay_context",
                    "Retained original target assay context",
                    native_support["assay_context_location"],
                ),
                (
                    "citation_context",
                    "Retained original target citation context",
                    native_support["citation_context_location"],
                ),
                (
                    "measurement_context",
                    "Whole native grouping and interpretation context",
                    native_support["context_location"],
                ),
                (
                    "source_request_context",
                    "Original target source coverage and quality",
                    native_result.wire["context"]["quality_location"],
                ),
            )
        )
        for location in native_support["publication_context_locations"]:
            publication = native_access._resolve(location)[0]
            destinations.append(
                (
                    "publication_context",
                    "Full original target publication context · "
                    + str(publication["publication_ref"]),
                    location,
                )
            )
    for role, label, location in destinations:
        if location is not None:
            rows.append(
                _located_link(explorer, role, label, location, basis, navigation)
            )
    rows.append(
        {
            "role": "native_ligand_crossing",
            "label": "Original native molecule/target crossing and all input occurrences",
            "target_ref": navigation["target_card_ref"],
            "support": deepcopy(basis),
            "availability": "available",
            "candidates": [],
            "paths": [],
            "blocked_paths": [],
            "rule": LINK_RULE,
            "molecule_activity_navigation": deepcopy(navigation),
        }
    )
    if navigation["molecule_root_view_ref"] is not None:
        rows.append(
            {
                "role": "molecule_root",
                "label": "Return to the originating molecule target selection",
                "target_ref": navigation["molecule_card_ref"],
                "support": deepcopy(basis),
                "availability": "available",
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
                "rule": LINK_RULE,
                "molecule_activity_navigation": deepcopy(navigation),
            }
        )
    captured = _link_view(
        explorer,
        rows,
        parent,
        f"Original molecule and target activity context · {item.label}",
        source_location=item.payload_location,
        support_location=result.location("support", item._entry.key),
        rule=LINK_RULE,
        reason=(
            "Exact retained molecule/target pins, identity statements and native activity destinations. "
            "Publication context retains its complete target scope; source silence does not establish inactivity or efficacy."
        ),
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(captured, _context_override=_context(parent, navigation, "links"))


def _target_access(explorer, pin):
    matches = [
        key for key, capture in explorer.access._captures.items() if capture.pin == pin
    ]
    if len(matches) != 1:
        raise ArgumentError(
            "An exact retained target pin is required for this context."
        )
    return explorer.access._for_capture(matches[0])


def follow(item):
    """Open one explicit destination with both pins and the actual parent intact."""
    from .card_exploration import CardView

    parent, explorer, link = item._view, item._view._explorer, item._entry.value
    navigation, role = link["molecule_activity_navigation"], link["role"]
    if role == "native_ligand_crossing":
        result = next(
            (
                value
                for value in explorer.access._scientific_cache.values()
                if getattr(value, "result_ref", None) == navigation["source_result_ref"]
            ),
            None,
        )
        if result is None:
            raise ArgumentError("The original molecule-target result is not retained.")
        node, location = result.native_crossing(navigation["target_card_ref"])
        selection = explorer.access.read(location)
        return CardView(
            explorer,
            selection,
            selection._entries,
            link["label"],
            parent,
            _native_override=node,
            _request=parent.request,
            _context_override=_context(parent, navigation, role),
        )
    if role == "molecule_root":
        matches = [
            candidate
            for candidate in explorer._session["views"].values()
            if candidate.view_ref == navigation["molecule_root_view_ref"]
            and _selection_binding(candidate) == navigation["molecule_root_selection"]
        ]
        if not matches:
            raise ArgumentError("The originating molecule selection is not retained.")
        return replace(matches[0], _origin=parent, _request=parent.request)
    if len(link["candidates"]) == 1:
        if role == "target_card":
            from .card_context_navigation import _destination

            destination = _destination(
                explorer, link["candidates"][0], parent, title=link["label"]
            )
            destination._explorer._session["views"].pop(id(destination), None)
            return replace(
                destination,
                title=link["label"],
                _request=parent.request,
                _context_override={
                    **destination.context,
                    "adapter": LINK_RULE,
                    "activity_context": role,
                    "molecule_card_ref": navigation["molecule_card_ref"],
                    "target_card_ref": navigation["target_card_ref"],
                    "molecule_activity_navigation": deepcopy(navigation),
                },
            )
        location = link["candidates"][0]["location"]
        node, location = explorer.access._resolve(location)
        if role == "publication_context":
            from .card_bioactivity_access import _native

            summary = deepcopy(node)
            node = _native(
                _target_access(explorer, navigation["target_card_ref"]),
                "explain_literature",
                summary["publication_ref"],
            )
            location = explorer.access._object_location(
                {
                    "original_summary": summary,
                    "original_explanation": node,
                    "publication_ref": summary["publication_ref"],
                }
            )
        selection = explorer.access.read(location)
        return CardView(
            explorer,
            selection,
            selection._entries,
            link["label"],
            parent,
            _native_override=node,
            _request=parent.request,
            _context_override=_context(parent, navigation, role),
        )
    captured = explorer._metadata(
        {"link": link}, "Original source statement unavailable", parent
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _request=parent.request,
        _status=link["availability"],
        _reason=(
            "The referenced original source statement is unavailable. Its retained identity relationship and missing support "
            "remain visible; no replacement or attribution is inferred."
        ),
        _context_override=_context(parent, navigation, role),
    )


def display_filter(view, column, equals):
    """Filter displayed members while keeping the complete original result."""
    validate_equality(column, equals)
    result = view._selection._scientific
    if view._status not in ("ok", "empty") and not result.entries:
        raise ArgumentError(
            "This activity context has no retained rows for display filtering."
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
        else "No displayed items match; the original supplied contexts and scientific outcomes are unchanged.",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
            "filter_policy": FORMAT,
        },
    )


def display_sort(view, column, descending=False, unit=None):
    """Order retained members using the shared typed selection policy."""
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
