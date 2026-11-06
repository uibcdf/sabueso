"""Original chemical exploration @15 binding, independent of current readers."""

from copy import deepcopy

from .card_access import _Entry, _handle
from .card_chemical_history_v1 import ADAPTER, TOPIC, expected_result, restore_result
from .card_chemical_selection_v1 import (
    COLUMNS,
    active,
    equal,
    evaluate,
    normalize,
    projection,
    selection_ref,
)
from .card_exploration_history import _require_matches
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@15"
VERIFIER = "chemical_classification_exploration_binding@1"
LINK_RULE = "chemical_classification_links@1"
ADAPTERS = (
    "structure_exploration@1",
    "knowledge_coverage_exploration@1",
    "ligand_site_exploration@1",
    "quaternary_exploration@1",
    "assembly_generation_exploration@1",
    "assembly_generation_exploration@2",
    ADAPTER,
)
SCHEMA = {
    "kind": "chemical_classification",
    "grain": "one retained original field-member position, including duplicates",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
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


def register_bundle(bundle, objects, access):
    chemical = {
        ref: value
        for ref, value in objects.items()
        if ref not in access._metadata_refs
        and isinstance(value, dict)
        and "native_payload" in value
        and value.get("context", {}).get("adapter") == ADAPTER
    }
    if not chemical:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    for ref, wire in chemical.items():
        focal = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == wire["context"]["card_ref"]
            and capture.snapshot == wire["context"]["snapshot_id"]
        )
        bundle.setdefault("scientific_results", {})[ref] = {"focal": focal}


def verify_objects(bundle, accesses):
    from .card_exploration_assembly_v2 import verify_objects as original_objects

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
            record == {"focal": record["focal"]}, "Unknown chemical manifest member."
        )
        expected = expected_result(accesses[record["focal"]])
        require(
            ref == expected.result_ref,
            "Chemical result differs from original input identity.",
        )
        _require_matches(
            wire,
            expected.wire,
            "chemical fields, original source/identity support, uncertainty and interpretation",
        )


def _machine(selection, access, result):
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
        query = normalize(spec["where"], spec["item_refs"], spec["order_by"])
        require(active(query), "Unrestricted chemical selection has a foreign policy.")
        entries, expected = evaluate(result, query)
        _require_matches(
            spec, expected, "chemical selection membership, order and exclusions"
        )
        ref = selection_ref(result, fields, expected)
    expected_request = {"topic": TOPIC, "fields": list(fields), "options": {}}
    if spec is not None:
        expected_request["selection"] = spec
    _require_matches(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "original chemical machine request",
    )
    require(
        selection.selection_ref == ref and selection._operation == "select:" + TOPIC,
        "Chemical machine selection identity/operation differs.",
    )
    _require_matches(
        selection._target,
        {
            "node_type": "scientific_result",
            "location": selection._target["location"],
            "size": len(result.entries),
        },
        "chemical machine target",
    )
    require(
        access._resolve(selection._target["location"])[1]
        == result.location("native_payload"),
        "Chemical machine target location differs.",
    )
    return entries


def verify_view(view, record):
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
                view._component_navigation,
            )
        ),
        "Foreign chemical presentation flags.",
    )
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Chemical view has a foreign focal capture.",
    )
    require(
        selection._slice is None and selection._outcome_override is None,
        "Chemical selection has unsupported literal options.",
    )
    if selection._operation.startswith("select:"):
        entries = _machine(selection, access, result)
    else:
        entries = result.entries
        require(
            selection.selection_ref
            == _handle(
                "XA_",
                {
                    "format": "chemical_classification_human@1",
                    "result_ref": result.result_ref,
                },
            )
            and selection._operation == "read"
            and not selection._fields,
            "Original human chemical selection differs.",
        )
        request = access._resolve(selection._context_location)[0]
        expected_context = {
            k: v
            for k, v in result.wire["context"].items()
            if k not in ("options", "used_captures")
        }
        expected_context["adapter"] = "literal_access@1"
        _require_matches(
            request,
            {
                "context": expected_context,
                "request": {
                    "operation": "read",
                    "location": result.location(),
                    "text_slice": None,
                },
            },
            "human chemical request",
        )
        target = {
            "node_type": "object",
            "size": len(result.wire),
            "location": selection._target["location"],
            "owner": {"result_ref": result.result_ref},
        }
        _require_matches(selection._target, target, "human chemical target")
        require(
            access._resolve(selection._target["location"])[1] == result.location(),
            "Chemical human target location differs.",
        )
    _require_matches(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in entries],
        "original chemical row membership",
    )
    _require_matches(
        view._context_override, result.wire["context"], "chemical context override"
    )
    state = record["state"]
    _require_matches(state["schema"], SCHEMA, "chemical schema")
    require(
        state["context"].get("mode") in ("live", "saved"),
        "Unknown chemical display mode.",
    )
    _require_matches(
        state["context"],
        {**result.wire["context"], "mode": state["context"]["mode"]},
        "chemical context",
    )
    _require_matches(
        state["coverage"], result.wire["coverage"], "chemical retained coverage"
    )
    expected_items = {}
    for entry in entries:
        row = entry.value
        proof = result.wire["support"][entry.key]
        ref = _handle(
            "XI_", {"result_ref": result.result_ref, "location": entry.location}
        )
        expected_items[ref] = {
            "label": row["label"],
            "kind": row["kind"],
            "support": [proof],
            "cells": {
                column: {
                    "value": row[column],
                    "state": "unknown" if row[column] is None else "present",
                    "reason": None,
                    "support": [proof],
                    "encoding": "json",
                }
                for column in COLUMNS
            },
        }
    _require_matches(
        state["items"], expected_items, "chemical typed labels, values and support"
    )
    if view.request is not None:
        _require_matches(
            view.request,
            {"question": "classification", "topic": "classification", "options": {}},
            "original chemical human question",
        )
    require(
        view._machine_ref
        == (
            selection.selection_ref
            if selection._operation.startswith("select:")
            else None
        ),
        "Foreign chemical machine origin.",
    )
    operation, previous = view._display_request, view._origin
    detail = (
        view.presentation == "detail" and previous is not None and operation is None
    )
    native = result.wire["native_payload"]
    if operation is not None:
        require(
            previous is not None
            and previous.result_ref == view.result_ref
            and previous._record_panel == TOPIC
            and previous._selection.selection_ref == selection.selection_ref,
            "Chemical display lost its original request.",
        )
        column = operation.get("column")
        if operation.get("operation") == "filter":
            from .card_chemical_selection_v1 import validate_equality

            require(
                set(operation) == {"operation", "column", "equals", "filter_policy"}
                and operation["filter_policy"] == "chemical_classification_selection@1",
                "Unknown chemical filter policy.",
            )
            validate_equality(column, operation["equals"])
            selected = tuple(
                entry
                for entry in previous._selected
                if equal(entry.value[column], operation["equals"])
            )
            unavailable = previous._status not in ("ok", "empty")
            status = previous._status if unavailable else "ok" if selected else "empty"
            reason = (
                previous._reason
                if unavailable
                else None
                if selected
                else "No items match this display selection."
            )
            require(
                view._status == status and view._reason == reason,
                "Chemical filtering changed scientific scope/outcome.",
            )
        elif operation.get("operation") == "sort":
            require(
                set(operation) == {"operation", "column", "descending", "unit"}
                and column in COLUMNS
                and type(operation["descending"]) is bool
                and operation["unit"] is None,
                "Unknown chemical sort request.",
            )
            present = [e for e in previous._selected if e.value[column] is not None]
            missing = [e for e in previous._selected if e.value[column] is None]
            selected = tuple(
                sorted(
                    present,
                    key=lambda e: e.value[column],
                    reverse=operation["descending"],
                )
                + missing
            )
            require(
                view.outcome == previous.outcome,
                "Chemical sorting changed scientific scope.",
            )
        else:
            require(
                operation == {"operation": "presentation"},
                "Unknown chemical display operation.",
            )
            selected = previous._selected
            require(
                view.outcome == previous.outcome,
                "Chemical presentation changed scientific scope.",
            )
        require(view._selected == selected, "Chemical display membership differs.")
    elif detail:
        require(
            previous.result_ref == view.result_ref
            and previous._record_panel == TOPIC
            and len(view._selected) == 1
            and view._selected[0] in previous._selected,
            "Chemical detail is not an original selected member.",
        )
        require(
            view.outcome == previous.outcome,
            "Chemical detail changed scientific scope.",
        )
        native = view._selected[0].value["item"]
    else:
        require(
            view._selected == entries and view.outcome == result.wire["outcome"],
            "Unexplained chemical selection or outcome.",
        )
    if operation is not None:
        base = view
        seen = set()
        while (
            base._display_request is not None
            and base._origin is not None
            and id(base) not in seen
        ):
            seen.add(id(base))
            require(
                base._origin.result_ref == view.result_ref
                and base._origin._selection.selection_ref == selection.selection_ref,
                "Chemical presentation crossed its original result/request.",
            )
            base = base._origin
        if base.presentation == "detail" and len(base._selected) == 1:
            native = base._selected[0].value["item"]
    require(
        record.get("native_encoding", "json") == "json",
        "Foreign chemical payload encoding.",
    )
    _require_matches(record["native_payload"], native, "original chemical payload")


def result_location(view):
    access = view._explorer.access
    _, full = access._resolve(view._selection._target["location"])
    if (
        full["kind"] == "result"
        and full["result_ref"] not in access._metadata_refs
        and isinstance(access._objects[full["result_ref"]], dict)
        and "native_payload" in access._objects[full["result_ref"]]
        and access._objects[full["result_ref"]].get("context", {}).get("adapter")
        == ADAPTER
    ):
        return full
    return None


def is_explanation(view):
    full = result_location(view)
    return (
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "explanations"}
    )


def verify_explanation(view):
    access, selection = view._explorer.access, view._selection
    full = result_location(view)
    key = full["segments"][1]["value"]
    wire = access._objects[full["result_ref"]]
    require(key in wire["rows"], "Foreign chemical explanation item.")
    native = wire["explanations"][key]
    _require_matches(
        view.native_payload, native, "chemical explanation original inputs"
    )
    context = access._resolve(selection._context_location)[0]
    request = {
        "operation": "read",
        "location": full,
        "text_slice": None,
    }
    expected_context = {**wire["context"], "adapter": "literal_access@1"}
    expected_context.pop("options")
    expected_context.pop("used_captures")
    _require_matches(
        context,
        {"context": expected_context, "request": request},
        "chemical explanation literal request",
    )
    ref = _handle(
        "XR_",
        {
            "format": "literal_access_result@1",
            "inputs": sorted(access._captures),
            "request": request,
        },
    )
    require(
        selection.result_ref == ref
        and selection.selection_ref
        == _handle(
            "XA_",
            {
                "format": "card_access_selection@1",
                "result_ref": ref,
                "request": request,
            },
        )
        and selection._operation == "read"
        and not selection._fields
        and selection._slice is None
        and selection._outcome_override is None,
        "Chemical explanation request identity differs.",
    )
    sources = wire["support"][key]["source_assertions"]
    entries = tuple(
        _Entry(row["location"], row["id"], access._resolve(row["location"])[0])
        for row in sources
        if row["state"] == "present"
    )
    _require_matches(
        [vars(e) for e in selection._entries],
        [vars(e) for e in entries],
        "chemical explanation original source membership",
    )
    return native


def expected_links(access, wire, key):
    basis = [wire["support"][key]]
    links = []

    def link(role, label, target, location):
        return {
            "role": role,
            "label": label,
            "target_ref": target,
            "support": deepcopy(basis),
            "rule": LINK_RULE,
            "candidates": [
                {
                    "location": location,
                    "capture": access._focal_key,
                    "basis": "exact_retained_node",
                }
            ],
            "paths": [],
            "blocked_paths": [],
            "availability": "available",
        }

    for source in basis[0]["source_assertions"]:
        if source["state"] == "present":
            original = access._resolve(source["location"])[0]
            record = original.get("source", {})
            record = record if isinstance(record, dict) else {}
            field = {
                "annotations.chemical_classes": "Chemical classes",
                "annotations.chemical_roles": "Chemical roles",
                "relationships.same_as": "Explicit molecular identity",
            }.get(original.get("field_path"), "Original source statement")
            label = " · ".join(
                str(v)
                for v in (record.get("name"), record.get("record_id"), field)
                if v is not None
            )
            links.append(link("source", label, source["id"], source["location"]))
        else:
            links.append(
                {
                    "role": "source",
                    "label": "Unavailable original input · " + source["id"],
                    "target_ref": source["id"],
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
            access._card_location(segments=[{"type": "Key", "value": "quality"}]),
        ),
    ):
        links.append(link(role, label, label, location))
    return links


def verify_links(view):
    access, native = view._explorer.access, view.native_payload
    _, location = access._resolve(native["source_location"])
    require(
        location["kind"] == "result"
        and len(location["segments"]) == 2
        and location["segments"][0] == {"type": "Key", "value": "rows"},
        "Chemical links lost original row scope.",
    )
    wire = access._objects[location["result_ref"]]
    key = location["segments"][1]["value"]
    require(
        wire.get("context", {}).get("adapter") == ADAPTER and key in wire["rows"],
        "Foreign chemical links.",
    )
    parent = view._origin
    require(
        parent is not None
        and is_view(parent)
        and parent.result_ref == location["result_ref"]
        and any(entry.key == key for entry in parent._selection._entries),
        "Chemical source navigation lost its original result/row context.",
    )
    require(
        view.request is None
        or view.request
        == {"question": "classification", "topic": "classification", "options": {}},
        "Unsupported chemical source navigation question.",
    )
    _require_matches(
        native,
        {
            "rule": LINK_RULE,
            "inputs": access.context["captures"],
            "focal": access._focal_key,
            "source_location": location,
            "links": expected_links(access, wire, key),
        },
        "chemical original links and source destinations",
    )


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_chemical_history_v1 import options_for_chemical
    from .card_exploration_storage import missing_selection

    fields, options = projection(fields), options_for_chemical(options)
    query = normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if (
            not is_result(selection._scientific)
            or selection._operation != "select:" + TOPIC
            or selection._fields != fields
        ):
            continue
        original = access._resolve(selection._context_location)[0]["request"]
        spec = original.get("selection")
        if (not active(query) and spec is None) or (
            spec is not None
            and canonical_json({key: spec[key] for key in query})
            == canonical_json(query)
        ):
            return selection
    return missing_selection(
        access, TOPIC, options, fields, query if active(query) else None
    )


def validate_filters(bundle):
    from .card_display_filter_v2 import RULE, validate_records

    older = {
        key: record
        for key, record in bundle["views"].items()
        if record["flags"]["_record_panel"] != TOPIC
    }
    enabled = any(
        isinstance(op := record["flags"]["_display_request"], dict)
        and op.get("filter_policy") == RULE
        for record in older.values()
    )
    validate_records({**bundle, "views": older}, enabled)
    return enabled


def saved_topic(explorer, origin):
    from dataclasses import replace

    from .card_exploration_storage import not_saved

    for view in explorer._session["views"].values():
        if (
            view._saved_state is not None
            and view._record_panel == TOPIC
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view.presentation != "detail"
            and view._machine_ref is None
            and view._selection._operation == "read"
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
                _display_request=None,
            )
    return not_saved(
        explorer,
        "The unrestricted chemical classification topic was not retained.",
        origin,
    )


def verification_report(bundle):
    from .card_exploration_assembly_v2 import verification_report as older_report

    older = {
        ref: record
        for ref, record in bundle["scientific_results"].items()
        if bundle["objects"][ref].get("context", {}).get("adapter") != ADAPTER
    }
    report = older_report({**bundle, "scientific_results": older})
    return {
        **report,
        "verifier": VERIFIER,
        "chemical_classification": "original_frozen_v1_consistency_verified",
        "verified_scientific_rules": sorted(
            set(report.get("verified_scientific_rules", []))
            | {"chemical_classification_context@1"}
        ),
        "scientific_classifications": "historical_consistency_verified",
        "recorded_navigation_decisions": "Original chemical class/role sources, field/identity contexts and retained earlier navigation independently verified; source authenticity remains unknown.",
    }


def retain_machine_views(root):
    """Retain already executed chemical requests; never evaluate a new query."""
    from .card_exploration import CardView
    from .card_exploration_storage import _explorer

    session = root._explorer._session
    accesses = {
        id(view._explorer.access): view._explorer.access
        for view in session["views"].values()
    }
    existing = {view._machine_ref for view in session["views"].values()}
    for access in accesses.values():
        for selection in list(access._selections.values()):
            if (
                not is_result(selection._scientific)
                or selection._operation != "select:" + TOPIC
                or selection.selection_ref in existing
            ):
                continue
            wire = selection._scientific.wire
            CardView(
                _explorer(access, session),
                selection,
                selection._entries,
                "Saved machine selection",
                _machine_ref=selection.selection_ref,
                _record_panel=TOPIC,
                _native_override=wire["native_payload"],
                _context_override=wire["context"],
                _status=wire["outcome"]["status"],
                _reason=wire["outcome"]["reason"],
            )
            existing.add(selection.selection_ref)
