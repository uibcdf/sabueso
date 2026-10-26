"""Explicit saved exploration @3 dispatch and original comparison binding (#148)."""

from .card_access import _handle
from .card_exploration_history import _require_matches
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@3"
VERIFIER = "site_exploration_binding@1"
TOPIC = "ligand_site_comparisons"
ADAPTER = "ligand_site_exploration@1"
LINK_RULE = "ligand_site_context_links@1"
ADAPTERS = ("structure_exploration@1", "knowledge_coverage_exploration@1", ADAPTER)
HUMAN_COLUMNS = (
    "label",
    "kind",
    "ligand_ref",
    "comparison_status",
    "outcome",
    "matched_sites",
    "reason",
)
HUMAN_SCHEMA = {
    "kind": "ligand_contact_comparison",
    "grain": "one retained protein–ligand contact declaration, not a physical ligand occurrence",
    "columns": list(HUMAN_COLUMNS),
    "presentations": ["summary", "table"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def is_result(result):
    return (
        result is not None and result.wire.get("context", {}).get("adapter") == ADAPTER
    )


def is_view(view):
    return view._record_panel == TOPIC or is_result(view._selection._scientific)


def unrestricted(selection):
    return selection._scientific is None or (
        is_result(selection._scientific)
        and selection.selection_ref
        == _handle(
            "XA_",
            {
                "format": "scientific_access_selection@1",
                "result_ref": selection.result_ref,
                "fields": selection._fields,
            },
        )
    )


def result_location(access, location):
    _, full = access._resolve(location)
    if (
        full["kind"] == "result"
        and isinstance(access._objects[full["result_ref"]], dict)
        and access._objects[full["result_ref"]].get("context", {}).get("adapter")
        == ADAPTER
    ):
        return full
    return None


def is_explanation(view):
    full = result_location(view._explorer.access, view._selection._target["location"])
    return (
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "explanations"}
    )


def verify_objects(bundle, accesses):
    from .card_exploration_science import _verify_objects
    from .card_ligand_site_history_v1 import expected_result

    original = {
        ref: record
        for ref, record in bundle["scientific_results"].items()
        if bundle["objects"][ref].get("context", {}).get("adapter") != ADAPTER
    }
    _verify_objects({**bundle, "scientific_results": original}, accesses)
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire.get("context", {}).get("adapter") != ADAPTER:
            continue
        require(
            record == {"focal": record["focal"]}, "Unknown site result manifest member."
        )
        expected = expected_result(accesses[record["focal"]])
        require(
            ref == expected.result_ref, "Original comparison result identity differs."
        )
        _require_matches(
            wire,
            expected.wire,
            "site admission, classification, source closure and original presentation",
        )
        accesses[record["focal"]]._scientific_cache[(VERIFIER, ref)] = expected


def verify_machine(view, result):
    from .card_ligand_site_selection_v1 import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )

    selection, access = view._selection, view._explorer.access
    context = access._resolve(selection._context_location)[0]
    request = context["request"]
    fields = projection(selection._fields)
    spec = request.get("selection")
    if spec is None:
        entries = result.entries
        ref = _handle(
            "XA_",
            {
                "format": "scientific_access_selection@1",
                "result_ref": result.result_ref,
                "fields": fields,
            },
        )
    else:
        require(
            spec.get("format") == "ligand_site_access_selection@1",
            "Unknown saved site selection policy.",
        )
        query = normalize(spec["where"], spec["item_refs"], spec["order_by"])
        require(
            active(query), "Unrestricted site request must use its original format."
        )
        entries, expected = evaluate(result, query)
        _require_matches(spec, expected, "site display selection decisions")
        ref = selection_ref(result, fields, expected)
    expected_request = {"topic": TOPIC, "fields": list(fields), "options": {}}
    if spec is not None:
        expected_request["selection"] = spec
    _require_matches(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "site request context",
    )
    require(
        selection.selection_ref == ref and selection.result_ref == result.result_ref,
        "Site selection identity differs.",
    )
    require(
        selection._operation == "select:" + TOPIC
        and selection._slice is None
        and selection._outcome_override is None,
        "Unsupported original site operation.",
    )
    target = selection._target
    require(
        set(target) == {"node_type", "location", "size"}
        and target["node_type"] == "scientific_result"
        and type(target["size"]) is int
        and target["size"] == len(result.entries),
        "Site target scope differs.",
    )
    require(
        access._resolve(target["location"])[1] == result.location("native_payload"),
        "Site native target differs.",
    )
    return entries


def verify_view(view, record):
    from .card_ligand_site_history_v1 import restore_result

    access, selection = view._explorer.access, view._selection
    require(
        view._record_panel == TOPIC
        and not any(
            (
                view._field_panel,
                view._link_panel,
                view._route_catalog,
                view._question_catalog,
                view._context_only,
                view._focus,
            )
        ),
        "Unsupported site presentation flags.",
    )
    require(view.result_ref in access._objects, "Missing original site result.")
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["adapter"] == ADAPTER, "Site view has a foreign adapter."
    )
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Site result has a foreign focal capture.",
    )
    if is_result(selection._scientific):
        entries = verify_machine(view, result)
        coverage = result.wire["coverage"]
    else:
        entries = result.entries
        require(
            selection.selection_ref
            == _handle(
                "XA_",
                {
                    "format": "ligand_site_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            "Human site selection identity differs.",
        )
        require(
            selection._operation == "read"
            and not selection._fields
            and selection._slice is None
            and selection._outcome_override is None,
            "Human site request differs.",
        )
        context = access._resolve(selection._context_location)[0]
        require(
            context["request"]
            == {"operation": "read", "location": result.location(), "text_slice": None},
            "Human site request binding differs.",
        )
        expected_context = {
            k: v
            for k, v in result.wire["context"].items()
            if k not in ("options", "used_captures")
        }
        expected_context["adapter"] = "literal_access@1"
        _require_matches(context["context"], expected_context, "human site capture")
        require(
            access._resolve(selection._target["location"])[1] == result.location(),
            "Human site target differs.",
        )
        target = {
            "node_type": "object",
            "size": len(result.wire),
            "location": selection._target["location"],
            "owner": {"result_ref": result.result_ref},
        }
        require(selection._target == target, "Human site node scope differs.")
        coverage = {
            "classification": "not_evaluated",
            "basis": "stored_literal",
            "quality_location": access._card_location(
                segments=[{"type": "Key", "value": "quality"}]
            ),
            "reason": "Inspect the stored quality records; no source coverage is inferred.",
        }
    _require_matches(
        [e.__dict__ for e in selection._entries],
        [e.__dict__ for e in entries],
        "site entry membership",
    )
    require(
        record.get("native_encoding", "json") == "json", "Unknown site native encoding."
    )
    state = record["state"]
    require(
        state["context"].get("mode") in ("live", "saved"), "Invalid original site mode."
    )
    _require_matches(
        {**state["context"], "mode": "live"},
        result.wire["context"],
        "site captured context",
    )
    _require_matches(
        view._context_override, result.wire["context"], "site presentation context"
    )
    _require_matches(state["schema"], HUMAN_SCHEMA, "site human schema")
    _require_matches(state["coverage"], coverage, "site coverage claims")
    expected_items = {}
    for entry in entries:
        ref = _handle(
            "XI_", {"result_ref": result.result_ref, "location": entry.location}
        )
        row, proof = result.wire["rows"][entry.key], result.wire["support"][entry.key]
        kind, label = "ligand_contact_comparison", row["label"]
        expected_items[ref] = {
            "label": label,
            "kind": kind,
            "support": [proof],
            "cells": {
                column: {
                    "value": label
                    if column == "label"
                    else kind
                    if column == "kind"
                    else row[column],
                    "state": "present",
                    "reason": None,
                    "support": [proof],
                    "encoding": "json",
                }
                for column in HUMAN_COLUMNS
            },
        }
    _require_matches(state["items"], expected_items, "site labels, cells and support")
    request = view.request
    require(
        request is None
        or request == {"question": TOPIC, "topic": TOPIC, "options": {}},
        "Original site question differs.",
    )
    operation = view._display_request
    detail = (
        view.presentation == "detail" and view._origin is not None and operation is None
    )
    if detail:
        require(
            view._origin.result_ref == view.result_ref
            and len(view._selected) == 1
            and view._selected[0] in view._origin._selection._entries,
            "Site detail lost its original item.",
        )
        native = result.native_item(view._selected[0].key)
    else:
        native = result.wire["native_payload"]
    _require_matches(record["native_payload"], native, "original site native payload")
    if operation:
        previous = view._origin
        require(
            previous is not None
            and previous.result_ref == view.result_ref
            and previous._record_panel == TOPIC,
            "Site display lost its original result.",
        )
        column = operation.get("column")

        def value(entry):
            return expected_items[
                _handle(
                    "XI_", {"result_ref": result.result_ref, "location": entry.location}
                )
            ]["cells"][column]["value"]

        if operation["operation"] == "filter":
            require(
                set(operation) == {"operation", "column", "equals"}
                and column in HUMAN_COLUMNS
                and isinstance(operation["equals"], str),
                "Invalid saved site equality.",
            )
            selected = tuple(
                e for e in previous._selected if value(e) == operation["equals"]
            )
            require(
                view._status == ("ok" if selected else "empty"),
                "Site filter outcome differs.",
            )
        elif operation["operation"] == "sort":
            require(
                set(operation) == {"operation", "column", "descending", "unit"}
                and column in HUMAN_COLUMNS
                and type(operation["descending"]) is bool
                and operation["unit"] is None,
                "Invalid saved site order.",
            )
            selected = tuple(
                sorted(previous._selected, key=value, reverse=operation["descending"])
            )
            require(
                view._status == previous._status,
                "Site order changed the scientific outcome.",
            )
        else:
            require(
                operation == {"operation": "presentation"},
                "Unknown site display operation.",
            )
            selected = previous._selected
        require(view._selected == selected, "Original site display membership differs.")
    elif not detail:
        require(
            view._selected == entries
            and view._status == result.wire["outcome"]["status"],
            "Unexplained site display exclusion or outcome.",
        )


def verify_explanation(view):
    access = view._explorer.access
    full = result_location(access, view._selection._target["location"])
    key = full["segments"][1]["value"]
    wire = access._objects[full["result_ref"]]
    _require_matches(
        view.native_payload, wire["explanations"][key], "original site explanation"
    )
    expected = [
        (s["location"], s["id"])
        for s in wire["support"][key]["source_assertions"]
        if s["state"] == "present"
    ]
    direct = [
        (e.location, e.key) for e in view._selection._entries
    ] == expected and all(e.ordinal is None for e in view._selection._entries)
    literal = view._selection._entries == access._children(view.native_payload, full)
    require(direct or literal, "Site explanation assertion membership differs.")
    return view.native_payload


def verify_links(view):
    from .card_ligand_site_history_v1 import expected_links

    access, native = view._explorer.access, view.native_payload
    full = result_location(access, native["source_location"])
    require(
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "rows"},
        "Site links have no original comparison row.",
    )
    anchor = view
    while (
        anchor._origin is not None
        and anchor._origin._link_panel
        and anchor._origin.result_ref == view.result_ref
    ):
        anchor = anchor._origin
    require(
        anchor._origin is not None
        and anchor._origin.result_ref == full["result_ref"]
        and any(e.location == full for e in anchor._origin._selection._entries),
        "Site links lost their actual origin.",
    )
    expected = access._scientific_cache.get((VERIFIER, full["result_ref"]))
    require(
        expected is not None, "Original site result was not independently verified."
    )
    _require_matches(
        native,
        expected_links(access, expected, full["segments"][1]["value"]),
        "original site contextual links",
    )


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_exploration_storage import missing_selection
    from .card_ligand_site_selection_v1 import active, evaluate, normalize, projection

    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError("ligand_site_comparisons has no scientific options.")
    fields, query = projection(fields), normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if not is_result(selection._scientific):
            continue
        request = access._resolve(selection._context_location)[0]["request"]
        expected = evaluate(selection._scientific, query)[1] if active(query) else None
        if selection._fields == fields and canonical_json(
            request.get("selection")
        ) == canonical_json(expected):
            return selection
    return missing_selection(
        access, TOPIC, {}, fields, query if active(query) else None
    )
