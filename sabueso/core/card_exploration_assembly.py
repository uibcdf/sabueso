"""Explicit exploration @5 and independent original assembly binding (#148/#173)."""

from dataclasses import replace

from .card_access import _handle
from .card_assembly_selection_v1 import COLUMNS, DEFAULT_FIELDS
from .card_exploration_history import _require_matches
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@5"
VERIFIER = "assembly_generation_exploration_binding@1"
TOPIC = "assembly_generation"
ADAPTER = "assembly_generation_exploration@1"
LINK_RULE = "assembly_generation_links@1"
ADAPTERS = (
    "structure_exploration@1",
    "knowledge_coverage_exploration@1",
    "ligand_site_exploration@1",
    "quaternary_exploration@1",
    ADAPTER,
)
HUMAN_SCHEMA = {
    "kind": "assembly_generation_finding",
    "grain": "one original generator, unavailable source/parent scope, acquisition gap or unplaced declaration",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def register_bundle(bundle, objects, access):
    assemblies = {
        ref: obj
        for ref, obj in objects.items()
        if isinstance(obj, dict)
        and "native_payload" in obj
        and ref not in access._metadata_refs
        and obj.get("context", {}).get("adapter") == ADAPTER
    }
    if not assemblies:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    for ref, wire in assemblies.items():
        context = wire["context"]
        focal = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == context["card_ref"]
            and capture.snapshot == context["snapshot_id"]
        )
        bundle["scientific_results"][ref] = {"focal": focal}


def verification_report(bundle):
    from .card_exploration_science import _verification_report

    assemblies = {
        ref
        for ref in bundle["scientific_results"]
        if bundle["objects"][ref].get("context", {}).get("adapter") == ADAPTER
    }
    older = {
        ref: rec
        for ref, rec in bundle["scientific_results"].items()
        if ref not in assemblies
    }
    report = _verification_report({**bundle, "scientific_results": older})
    rules = set(report["verified_scientific_rules"])
    for ref in assemblies:
        native = bundle["objects"][ref]["native_payload"]
        for key in (
            "rule",
            "operator_binding_rule",
            "component_binding_rule",
            "occurrence_rule",
        ):
            if isinstance(native.get(key), str):
                rules.add(native[key])
    return {
        **report,
        "verifier": VERIFIER,
        "verified_scientific_rules": sorted(rules),
        "scientific_classifications": "historical_consistency_verified"
        if rules
        else "not_evaluated",
    }


def verify_objects(bundle, accesses):
    from .card_assembly_history_v1 import expected_result, options_for_assembly
    from .card_exploration_quaternary import verify_objects as original_objects

    older = {
        ref: record
        for ref, record in bundle["scientific_results"].items()
        if bundle["objects"][ref].get("context", {}).get("adapter") != ADAPTER
    }
    original_objects({**bundle, "scientific_results": older}, accesses)
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire.get("context", {}).get("adapter") != ADAPTER:
            continue
        require(
            record == {"focal": record["focal"]}, "Unknown assembly manifest member."
        )
        options = options_for_assembly(wire["context"]["options"])
        _require_matches(
            wire["context"]["options"], options, "normalized original assembly options"
        )
        expected = expected_result(accesses[record["focal"]], options)
        require(
            ref == expected.result_ref, "Original assembly result identity differs."
        )
        _require_matches(
            wire,
            expected.wire,
            "assembly original inputs, findings, scope, rules, counts, source closure and presentation",
        )
        accesses[record["focal"]]._scientific_cache[(VERIFIER, ref)] = expected


def verify_view(view, record):
    from .card_assembly_history_v1 import restore_result
    from .card_assembly_selection_v1 import validate_equality

    access, selection = view._explorer.access, view._selection
    require(
        view._record_panel == TOPIC
        and is_result(selection._scientific)
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
        "Unsupported original assembly presentation.",
    )
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Assembly result has a foreign focal capture.",
    )
    entries = verify_machine(view, result)
    _require_matches(
        [e.__dict__ for e in selection._entries],
        [e.__dict__ for e in entries],
        "original assembly entry membership",
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown assembly native encoding.",
    )
    state = record["state"]
    require(state["context"]["mode"] in ("live", "saved"), "Invalid assembly mode.")
    _require_matches(
        {**state["context"], "mode": "live"},
        result.wire["context"],
        "assembly captured context",
    )
    _require_matches(
        view._context_override, result.wire["context"], "assembly presentation context"
    )
    _require_matches(state["schema"], HUMAN_SCHEMA, "assembly schema")
    _require_matches(
        state["coverage"], result.wire["coverage"], "assembly coverage scope"
    )
    expected_items = {}
    for entry in entries:
        ref = _handle(
            "XI_", {"result_ref": result.result_ref, "location": entry.location}
        )
        row, proof = result.wire["rows"][entry.key], result.wire["support"][entry.key]
        expected_items[ref] = {
            "label": row["label"],
            "kind": row["kind"],
            "support": [proof],
            "cells": {
                column: {
                    "value": row[column],
                    "state": result.cell_state(entry.key, column),
                    "reason": result.cell_reason(entry.key, column),
                    "support": [proof],
                    "encoding": "json",
                }
                for column in COLUMNS
            },
        }
    _require_matches(
        state["items"],
        expected_items,
        "assembly typed labels, cells, count states and support",
    )
    if view.request is not None:
        _require_matches(
            view.request,
            {"question": TOPIC, "topic": TOPIC, "options": result.options},
            "original typed assembly question",
        )
    require(
        view._machine_ref in (None, selection.selection_ref),
        "Assembly machine origin differs.",
    )
    operation, previous = view._display_request, view._origin
    detail = (
        view.presentation == "detail" and previous is not None and operation is None
    )
    if operation is not None:
        require(
            previous is not None
            and previous.result_ref == view.result_ref
            and previous._record_panel == TOPIC
            and previous._selection.selection_ref == selection.selection_ref,
            "Assembly display lost its original request.",
        )
        column = operation.get("column")

        def value(entry):
            return result.value(entry.key, column)

        if operation.get("operation") == "filter":
            require(
                set(operation) == {"operation", "column", "equals"},
                "Invalid assembly equality.",
            )
            validate_equality(column, operation["equals"])
            selected = tuple(
                e for e in previous._selected if value(e) == operation["equals"]
            )
            status = "ok" if selected else "empty"
        elif operation.get("operation") == "sort":
            require(
                set(operation) == {"operation", "column", "descending", "unit"}
                and column in COLUMNS
                and type(operation["descending"]) is bool
                and operation["unit"] is None,
                "Invalid assembly order.",
            )
            present = [e for e in previous._selected if value(e) is not None]
            missing = [e for e in previous._selected if value(e) is None]
            selected = tuple(
                sorted(present, key=value, reverse=operation["descending"]) + missing
            )
            status = previous._status
        else:
            require(
                operation == {"operation": "presentation"},
                "Unknown assembly display operation.",
            )
            selected, status = previous._selected, previous._status
        native = previous.native_payload
    elif detail:
        require(
            previous.result_ref == view.result_ref
            and previous._record_panel == TOPIC
            and len(view._selected) == 1
            and view._selected[0] in previous._selection._entries
            and previous._selection.selection_ref == selection.selection_ref,
            "Assembly detail lost its exact original item.",
        )
        selected, status = view._selected, previous._status
        native = result.wire["rows"][selected[0].key]["item"]
    else:
        selected, status = entries, result.wire["outcome"]["status"]
        native = result.wire["native_payload"]
    require(
        view._selected == selected and view._status == status,
        "Original assembly display membership or outcome differs.",
    )
    _require_matches(
        record["native_payload"], native, "original assembly native payload"
    )


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_assembly_history_v1 import options_for_assembly
    from .card_assembly_selection_v1 import active, evaluate, normalize, projection
    from .card_exploration_storage import missing_selection

    options, fields = options_for_assembly(options), projection(fields)
    query = normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if (
            not is_result(selection._scientific)
            or selection._scientific.options != options
        ):
            continue
        request = access._resolve(selection._context_location)[0]["request"]
        expected = evaluate(selection._scientific, query)[1] if active(query) else None
        if selection._fields == fields and canonical_json(
            request.get("selection")
        ) == canonical_json(expected):
            return selection
    return missing_selection(
        access, TOPIC, options, fields, query if active(query) else None
    )


def saved_human(explorer, options, origin, *, question):
    from .card_assembly_history_v1 import options_for_assembly
    from .card_exploration_storage import not_saved

    options = options_for_assembly(options)
    request = (
        {"question": TOPIC, "topic": TOPIC, "options": options} if question else None
    )
    for view in list(explorer._session["views"].values()):
        if (
            view._saved_state is not None
            and view._record_panel == TOPIC
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view.context["options"] == options
            and unrestricted(view._selection)
            and view._selection._fields == DEFAULT_FIELDS
            and view.request == request
            and view._selected == view._selection._entries
            and view._display_request is None
            and view.presentation != "detail"
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
            )
    return not_saved(
        explorer,
        "This exact assembly request was not saved; the captured Card remains inspectable.",
        origin,
    )


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


def verify_machine(view, result):
    from .card_assembly_selection_v1 import (
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
            spec.get("format") == "assembly_generation_access_selection@1",
            "Unknown saved assembly selection policy.",
        )
        query = normalize(spec["where"], spec["item_refs"], spec["order_by"])
        require(
            active(query),
            "Unrestricted assembly request must use its original format.",
        )
        entries, expected = evaluate(result, query)
        _require_matches(spec, expected, "assembly display selection decisions")
        ref = selection_ref(result, fields, expected)
    expected_request = {
        "topic": TOPIC,
        "fields": list(fields),
        "options": result.options,
    }
    if spec is not None:
        expected_request["selection"] = spec
    _require_matches(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "assembly request context",
    )
    require(
        selection.selection_ref == ref and selection.result_ref == result.result_ref,
        "Assembly selection identity differs.",
    )
    require(
        selection._operation == "select:" + TOPIC
        and selection._slice is None
        and selection._outcome_override is None,
        "Unsupported original assembly operation.",
    )
    target = selection._target
    require(
        set(target) == {"node_type", "location", "size"}
        and target["node_type"] == "scientific_result"
        and type(target["size"]) is int
        and target["size"] == len(result.entries),
        "Assembly target scope differs.",
    )
    require(
        access._resolve(target["location"])[1] == result.location("native_payload"),
        "Assembly native target differs.",
    )
    return entries


def verify_explanation(view):
    access = view._explorer.access
    full = result_location(access, view._selection._target["location"])
    key = full["segments"][1]["value"]
    wire = access._objects[full["result_ref"]]
    _require_matches(
        view.native_payload,
        wire["explanations"][key],
        "original assembly explanation",
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
    require(direct or literal, "Assembly explanation assertion membership differs.")
    return view.native_payload


def verify_links(view):
    from .card_assembly_history_v1 import expected_links

    access, native = view._explorer.access, view.native_payload
    full = result_location(access, native["source_location"])
    require(
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "rows"},
        "Assembly links have no original comparison row.",
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
        "Assembly links lost their actual origin.",
    )
    expected = access._scientific_cache.get((VERIFIER, full["result_ref"]))
    require(
        expected is not None,
        "Original assembly result was not independently verified.",
    )
    _require_matches(
        native,
        expected_links(access, expected, full["segments"][1]["value"]),
        "original assembly contextual links",
    )
