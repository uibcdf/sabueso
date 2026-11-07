"""Original bioactivity exploration @17 binding over frozen retained inputs.

Expected values validate the recorded knowledge; they never replace it. The
reader uses no current Card, scientific reader, source client or live explorer.
"""

from copy import copy, deepcopy
from dataclasses import replace

from ._bioactivity_history_v1.selection import (
    COLUMNS,
    QUANTITY_FIELD,
    active,
    equal,
    evaluate,
    normalize,
    projection,
    selection_ref,
    sorted_entries,
    validate_equality,
)
from ._bioactivity_history_v1.selection import (
    FORMAT as SELECTION_FORMAT,
)
from .card_access import _Entry, _handle, _type
from .card_bioactivity_history_v1 import (
    ADAPTER,
    TOPIC,
    expected_publication,
    expected_result,
    options_for_bioactivities,
    restore_result,
)
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@17"
VERIFIER = "bioactivity_exploration_binding@1"
LINK_RULE = "bioactivity_context_links@1"
ADAPTERS = (
    "structure_exploration@1",
    "knowledge_coverage_exploration@1",
    "ligand_site_exploration@1",
    "quaternary_exploration@1",
    "assembly_generation_exploration@1",
    "assembly_generation_exploration@2",
    "chemical_classification_exploration@1",
    ADAPTER,
)
SCHEMA = {
    "kind": "bioactivity_exploration",
    "grain": "one original molecule, native measurement group or source activity record for the exact focused request",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        f"Saved {scope} differs from its original binding.",
    )


def is_result(result):
    return (
        result is not None and result.wire.get("context", {}).get("adapter") == ADAPTER
    )


def is_view(view):
    return view._record_panel == TOPIC or is_result(view._selection._scientific)


def is_context(view):
    return (
        isinstance(view._context_override, dict)
        and view._context_override.get("adapter") == LINK_RULE
    )


def result_location(view):
    access = view._explorer.access
    _, full = access._resolve(view._selection._target["location"])
    if full["kind"] != "result" or full["result_ref"] in access._metadata_refs:
        return None
    wire = access._objects[full["result_ref"]]
    return (
        full
        if isinstance(wire, dict)
        and "native_payload" in wire
        and wire.get("context", {}).get("adapter") == ADAPTER
        else None
    )


def is_explanation(view):
    full = result_location(view)
    return (
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "explanations"}
    )


def register_bundle(bundle, objects, access):
    retained = {
        ref: wire
        for ref, wire in objects.items()
        if ref not in access._metadata_refs
        and isinstance(wire, dict)
        and "native_payload" in wire
        and wire.get("context", {}).get("adapter") == ADAPTER
    }
    if not retained:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    for ref, wire in retained.items():
        focal = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == wire["context"]["card_ref"]
            and capture.snapshot == wire["context"]["snapshot_id"]
        )
        bundle.setdefault("scientific_results", {})[ref] = {"focal": focal}


def verify_objects(bundle, accesses):
    from .card_exploration_chemical import verify_objects as older_objects

    older = {}
    for ref, record in bundle["scientific_results"].items():
        require(
            ref in bundle["objects"] and isinstance(record, dict),
            "Missing scientific result or manifest.",
        )
        wire = bundle["objects"][ref]
        require(
            isinstance(wire, dict)
            and wire.get("context", {}).get("adapter") in ADAPTERS,
            "Unsupported scientific manifest adapter.",
        )
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Unknown bioactivity manifest member or focal capture.",
        )
        options = options_for_bioactivities(wire["context"]["options"])
        same(wire["context"]["options"], options, "bioactivity effective options")
        expected = expected_result(accesses[record["focal"]], options, original=wire)
        require(
            ref == expected.result_ref,
            "Bioactivity result identity differs from its original inputs/options.",
        )
        same(
            wire,
            expected.wire,
            "bioactivity source records, grouping, quantities, classifications and citation context",
        )
    older_objects({**bundle, "scientific_results": older}, accesses)


def _literal_context(access, mode="live"):
    return {**access.context, "mode": mode, "adapter": "literal_access@1"}


def _literal_selection(view, full, *, entries=None, result_override=None):
    """Verify the existing literal request grammar without interpreting opaque keys."""
    access, selection = view._explorer.access, view._selection
    node, bound = access._resolve(selection._target["location"])
    same(bound, full, "bioactivity literal target location")
    request = {"operation": "read", "location": full, "text_slice": None}
    context = access._resolve(selection._context_location)[0]
    mode = context["context"].get("mode")
    require(mode in ("live", "saved"), "Unknown retained literal request mode.")
    same(
        context,
        {"context": _literal_context(access, mode), "request": request},
        "bioactivity literal request",
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
        selection._operation == "read"
        and selection._slice is None
        and not selection._fields
        and selection._outcome_override is None,
        "Foreign bioactivity literal selection operation.",
    )
    if result_override is None:
        require(
            selection.result_ref == ref, "Bioactivity literal result identity differs."
        )
        expected_ref = _handle(
            "XA_",
            {
                "format": "card_access_selection@1",
                "result_ref": ref,
                "request": request,
            },
        )
    else:
        expected_ref = result_override
    require(
        selection.selection_ref == expected_ref,
        "Bioactivity literal selection identity differs.",
    )
    same(
        selection._target,
        {
            "node_type": _type(node),
            "size": len(node) if isinstance(node, (dict, list, str)) else None,
            "location": selection._target["location"],
            "owner": {
                key: full[key]
                for key in ("card_ref", "snapshot_id", "result_ref")
                if key in full
            },
        },
        "bioactivity literal target ownership",
    )
    expected_entries = access._children(node, full) if entries is None else entries
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in expected_entries],
        "bioactivity literal child membership",
    )
    return node


def _machine(selection, access, result):
    context = access._resolve(selection._context_location)[0]
    request = context["request"]
    fields, spec = projection(selection._fields), request.get("selection")
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
        require(
            active(query), "An unrestricted bioactivity selection has a foreign policy."
        )
        entries, expected = evaluate(result, query)
        same(spec, expected, "bioactivity exact membership, order and exclusions")
        ref = selection_ref(result, fields, expected)
    expected_request = {
        "topic": TOPIC,
        "fields": list(fields),
        "options": result.options,
    }
    if spec is not None:
        expected_request["selection"] = spec
    same(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "bioactivity machine request",
    )
    require(
        selection.selection_ref == ref and selection._operation == "select:" + TOPIC,
        "Bioactivity machine request identity differs.",
    )
    same(
        selection._target,
        {
            "node_type": "scientific_result",
            "location": selection._target["location"],
            "size": len(result.entries),
        },
        "bioactivity machine target",
    )
    same(
        access._resolve(selection._target["location"])[1],
        result.location("native_payload"),
        "bioactivity machine native target",
    )
    return entries


def _question(view, result=None):
    request, parent = view.request, view._origin
    if parent is not None and (
        is_view(parent) or parent._link_panel or is_context(parent)
    ):
        same(request, parent.request, "bioactivity original question continuity")
    if request is None:
        return
    require(
        isinstance(request, dict)
        and set(request) == {"question", "topic", "options"}
        and request["question"] == "measured_molecules"
        and request["topic"] == TOPIC,
        "Unsupported bioactivity human question.",
    )
    same(
        request["options"],
        options_for_bioactivities(request["options"]),
        "bioactivity question options",
    )
    if result is not None and not (
        parent is not None
        and (is_view(parent) or parent._link_panel or is_context(parent))
    ):
        same(request["options"], result.options, "bioactivity question/result scope")


def _view_state(view, record, result, entries):
    from pyunitwizard import QuantityRecord

    from .quantities import to_quantity

    state = record["state"]
    same(state["schema"], SCHEMA, "bioactivity schema")
    require(
        state["context"].get("mode") in ("live", "saved"),
        "Unknown bioactivity saved display mode.",
    )
    same(
        state["context"],
        {**result.wire["context"], "mode": state["context"]["mode"]},
        "bioactivity captured context",
    )
    same(
        state["coverage"],
        result.wire["coverage"],
        "bioactivity source/request coverage",
    )
    items = {}
    for entry in entries:
        row, proof = entry.value, result.wire["support"][entry.key]
        cells = {}
        for column in COLUMNS:
            value = row[column]
            cell = {
                "value": value,
                "state": result.cell_state(entry.key, column),
                "reason": result.cell_reason(entry.key, column),
                "support": [proof],
                "encoding": "json",
            }
            if column == "measurement" and value is not None:
                cell.update(
                    value=QuantityRecord.from_quantity(
                        to_quantity(value), field=QUANTITY_FIELD, unit=value["unit"]
                    ).to_dict(),
                    encoding="quantity_record",
                    field=QUANTITY_FIELD,
                    unit=value["unit"],
                )
            cells[column] = cell
        ref = _handle(
            "XI_", {"result_ref": result.result_ref, "location": entry.location}
        )
        items[ref] = {
            "label": row["label"],
            "kind": row["kind"],
            "support": [proof],
            "cells": cells,
        }
    same(
        state["items"],
        items,
        "bioactivity labels, typed quantities and original support",
    )


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
        "Foreign bioactivity presentation flags.",
    )
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Bioactivity view has a foreign focal capture.",
    )
    require(
        selection._slice is None
        and selection._outcome_override is None
        and view.presentation in SCHEMA["presentations"],
        "Unsupported bioactivity selection/presentation options.",
    )
    if selection._operation.startswith("select:"):
        entries = _machine(selection, access, result)
    else:
        entries = result.entries
        human_ref = _handle(
            "XA_",
            {
                "format": "bioactivity_human_selection@1",
                "result_ref": result.result_ref,
            },
        )
        _literal_selection(
            view, result.location(), entries=entries, result_override=human_ref
        )
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in entries],
        "bioactivity original row membership",
    )
    same(view._context_override, result.wire["context"], "bioactivity context override")
    _view_state(view, record, result, entries)
    _question(view, result)
    require(
        view._machine_ref
        == (
            selection.selection_ref
            if selection._operation.startswith("select:")
            else None
        ),
        "Foreign bioactivity machine-origin binding.",
    )
    operation, parent = view._display_request, view._origin
    native = result.wire["native_payload"]
    if operation is not None:
        require(
            parent is not None
            and parent.result_ref == view.result_ref
            and parent._record_panel == TOPIC
            and parent._selection.selection_ref == selection.selection_ref,
            "Bioactivity display crossed its original result/request.",
        )
        if operation.get("operation") == "filter":
            require(
                set(operation) == {"operation", "column", "equals", "filter_policy"}
                and operation["filter_policy"] == SELECTION_FORMAT,
                "Unsupported bioactivity filter policy.",
            )
            expected_entries, expected_outcome = _filter_result(
                parent, operation["column"], operation["equals"]
            )
        elif operation.get("operation") == "sort":
            require(
                set(operation)
                == {"operation", "column", "descending", "unit", "selection_policy"}
                and operation["selection_policy"] == SELECTION_FORMAT,
                "Unsupported bioactivity ordering policy.",
            )
            expected_entries = sorted_entries(
                parent._selected,
                result,
                operation["column"],
                descending=operation["descending"],
                unit=operation["unit"],
            )
            expected_outcome = parent.outcome
        else:
            require(
                operation == {"operation": "presentation"},
                "Unsupported bioactivity display operation.",
            )
            expected_entries, expected_outcome = parent._selected, parent.outcome
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in expected_entries],
            "bioactivity display order/membership",
        )
        same(view.outcome, expected_outcome, "bioactivity display outcome")
        base, seen = view, set()
        while base._display_request is not None and base._origin is not None:
            require(id(base) not in seen, "Cyclic bioactivity display origin.")
            seen.add(id(base))
            base = base._origin
            require(
                base.result_ref == view.result_ref
                and base._selection.selection_ref == selection.selection_ref,
                "Bioactivity display lost its original request.",
            )
        if base.presentation == "detail" and len(base._selected) == 1:
            native = base._selected[0].value["item"]
    elif view.presentation == "detail":
        require(
            parent is not None
            and is_view(parent)
            and parent.result_ref == view.result_ref
            and len(view._selected) == 1
            and view._selected[0] in parent._selection._entries
            and view._selected[0].value["kind"] == "bioactivity_record",
            "Bioactivity detail is not an original selected source record.",
        )
        same(view.outcome, parent.outcome, "bioactivity detail outcome")
        native = view._selected[0].value["item"]
    else:
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in entries],
            "bioactivity unrestricted selection",
        )
        same(view.outcome, result.wire["outcome"], "bioactivity original outcome")
        _verify_focus_origin(view, result)
    require(
        record.get("native_encoding", "json") == "json",
        "Unsupported bioactivity native encoding.",
    )
    same(
        record["native_payload"], native, "complete original bioactivity native payload"
    )


def _verify_focus_origin(view, result):
    parent = view._origin
    if parent is None or not is_view(parent) or parent.result_ref == view.result_ref:
        return
    old = parent._selection._scientific.options
    same(
        {
            key: value
            for key, value in old.items()
            if key not in ("molecule_ref", "measurement_ref")
        },
        {
            key: value
            for key, value in result.options.items()
            if key not in ("molecule_ref", "measurement_ref")
        },
        "bioactivity drill-down scientific policies",
    )
    grain = result.wire["context"]["grain"]
    if grain == "group":
        require(
            result.options["measurement_ref"] is None
            and any(
                entry.value["kind"] == "bioactivity_molecule"
                and entry.value["molecule_ref"] == result.options["molecule_ref"]
                for entry in parent._selection._entries
            ),
            "Bioactivity molecule drill-down lost its selected original member.",
        )
    elif grain == "record":
        require(
            any(
                entry.value["kind"] == "bioactivity_group"
                and entry.value["molecule_ref"] == result.options["molecule_ref"]
                and entry.value["measurement_ref"] == result.options["measurement_ref"]
                for entry in parent._selection._entries
            ),
            "Bioactivity group drill-down lost its selected original group.",
        )
    else:
        raise StorageError("Unsupported bioactivity drill-down origin.")


def verify_explanation(view):
    access, full = view._explorer.access, result_location(view)
    require(full is not None, "Missing original bioactivity explanation result.")
    key, wire = full["segments"][1]["value"], access._objects[full["result_ref"]]
    require(key in wire["rows"], "Foreign bioactivity explanation row.")
    native, parent = wire["explanations"][key], view._origin
    entries = None
    if parent is not None and is_view(parent):
        require(
            parent.result_ref == full["result_ref"]
            and any(entry.key == key for entry in parent._selection._entries),
            "Bioactivity explanation has a foreign original item/back context.",
        )
        entries = tuple(
            _Entry(row["location"], row["id"], access._resolve(row["location"])[0])
            for row in wire["support"][key]["source_assertions"]
            if row["state"] == "present"
        )
    _literal_selection(view, full, entries=entries)
    same(view.native_payload, native, "bioactivity explanation full original inputs")
    _question(view)
    return native


def expected_links(access, wire, key):
    ref = next(ref for ref, value in access._objects.items() if value is wire)
    result, basis = restore_result(ref, wire), [wire["support"][key]]
    rows = []

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

    for statement in basis[0]["source_assertions"]:
        if statement["state"] == "present":
            original = access._resolve(statement["location"])[0]
            source = original.get("source", {})
            source = source if isinstance(source, dict) else {}
            label = "Original source statement · " + " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    original.get("field_path"),
                    statement["id"],
                )
                if value is not None
            )
            rows.append(link("source", label, statement["id"], statement["location"]))
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Unavailable original source statement · "
                    + statement["id"],
                    "target_ref": statement["id"],
                    "support": deepcopy(basis),
                    "rule": LINK_RULE,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    destinations = [
        (
            "original_record",
            "Complete retained native item",
            result.location("rows", key, "item"),
        ),
        ("assay_context", "Retained assay context", basis[0]["assay_context_location"]),
        (
            "citation_context",
            "Retained citation context",
            basis[0]["citation_context_location"],
        ),
        (
            "measurement_context",
            "Whole native grouping and interpretation context",
            basis[0]["context_location"],
        ),
        (
            "whole_card_context",
            "Original captured Card and molecule glossary",
            basis[0]["whole_card_context_location"],
        ),
        (
            "source_request_context",
            "Retained source coverage and quality",
            wire["context"]["quality_location"],
        ),
    ]
    for location in basis[0]["relationship_locations"]:
        original = access._resolve(location)[0]
        destinations.append(
            (
                "original_relationship",
                "Original bioactivity relationship · " + str(original["id"]),
                location,
            )
        )
    for location in basis[0]["publication_context_locations"]:
        publication = access._resolve(location)[0]
        destinations.append(
            (
                "publication_context",
                "Exact retained publication context · "
                + str(publication["publication_ref"]),
                location,
            )
        )
    rows.extend(
        link(role, label, label, location) for role, label, location in destinations
    )
    return rows


def verify_links(view):
    access, native = view._explorer.access, view.native_payload
    require(
        isinstance(native, dict) and native.get("rule") == LINK_RULE,
        "Unsupported bioactivity navigation rule.",
    )
    _, full = access._resolve(native["source_location"])
    require(
        full["kind"] == "result"
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "rows"}
        and full["result_ref"] not in access._metadata_refs,
        "Bioactivity links have no original row location.",
    )
    wire, key, parent = (
        access._objects[full["result_ref"]],
        full["segments"][1]["value"],
        view._origin,
    )
    require(
        wire.get("context", {}).get("adapter") == ADAPTER and key in wire["rows"],
        "Foreign bioactivity navigation result.",
    )
    require(
        parent is not None
        and is_view(parent)
        and parent.result_ref == full["result_ref"]
        and any(entry.key == key for entry in parent._selection._entries),
        "Bioactivity navigation lost its original selected row/back context.",
    )
    same(
        native,
        {
            "rule": LINK_RULE,
            "inputs": access.context["captures"],
            "focal": access._focal_key,
            "source_location": full,
            "links": expected_links(access, wire, key),
        },
        "bioactivity exact source/assay/citation destinations",
    )
    _question(view)


def _literal_state(view, record):
    """Reuse declared literal cell/quantity predicates after binding new context."""
    from .card_exploration import CardItem
    from .card_exploration_storage import _cell_record
    from .card_exploration_verification import _verify_cell, _verify_display

    plain = copy(view)
    object.__setattr__(plain, "_saved_state", None)
    state = record["state"]
    same(state["schema"], plain.schema, "bioactivity destination literal schema")
    same(state["coverage"], plain.coverage, "bioactivity destination literal coverage")
    expected_refs = {
        _handle("XI_", {"result_ref": view.result_ref, "location": entry.location})
        for entry in view._selection._entries
    }
    require(
        set(state["items"]) == expected_refs,
        "Bioactivity destination item closure differs.",
    )
    for entry in view._selection._entries:
        actual_node = view._explorer.access._resolve(entry.location)[0]
        same(entry.value, actual_node, "bioactivity destination original literal child")
        item = CardItem(plain, entry)
        frozen = state["items"][item.item_ref]
        require(
            isinstance(frozen, dict)
            and set(frozen) == {"label", "kind", "support", "cells"}
            and isinstance(frozen["label"], str),
            "Unknown destination item shape.",
        )
        require(
            frozen["kind"] == item.kind, "Bioactivity destination literal kind differs."
        )
        same(frozen["support"], item.support, "bioactivity destination literal support")
        require(
            set(frozen["cells"]) == set(item.cells),
            "Bioactivity destination cell membership differs.",
        )
        for column, cell in item.cells.items():
            expected, actual = (
                _cell_record(item, column, cell),
                dict(frozen["cells"][column]),
            )
            if column == "label":
                expected["value"] = frozen["label"]
            expected.pop("reason", None)
            actual.pop("reason", None)
            _verify_cell(actual, expected)
    _verify_display(view, record)


def verify_context(view, record):
    access, anchor, seen = view._explorer.access, view, set()
    require(
        not any(
            (
                view._record_panel,
                view._field_panel,
                view._link_panel,
                view._route_catalog,
                view._question_catalog,
                view._focus,
                view._component_navigation,
            )
        )
        and view._selection._scientific is None,
        "Foreign bioactivity destination presentation flags.",
    )
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen
            and anchor._origin is not None
            and is_context(anchor._origin),
            "Bioactivity destination display has a cyclic/foreign origin.",
        )
        seen.add(id(anchor))
        require(
            anchor._selection.selection_ref == anchor._origin._selection.selection_ref
            and anchor.result_ref == anchor._origin.result_ref,
            "Bioactivity destination display changed its original request.",
        )
        anchor = anchor._origin
    parent = anchor._origin
    require(
        parent is not None
        and parent._link_panel
        and parent.native_payload.get("rule") == LINK_RULE,
        "Bioactivity destination lost its original link/back context.",
    )
    verify_links(parent)
    role = anchor._context_override.get("bioactivity_context")
    choices = [
        link
        for link in parent.native_payload["links"]
        if link["role"] == role and link["label"] == anchor.title
    ]
    require(
        len(choices) == 1, "Bioactivity destination has no unique exact retained link."
    )
    link = choices[0]
    require(
        len(link["candidates"]) <= 1, "Unsupported bioactivity destination ambiguity."
    )
    if link["candidates"]:
        require(
            not anchor._context_only
            and link["candidates"][0]["capture"] == access._focal_key,
            "Bioactivity context switched to a foreign capture.",
        )
        full = link["candidates"][0]["location"]
        native = access._resolve(full)[0]
        if role == "publication_context":
            actual, full = access._resolve(anchor._selection._target["location"])
            expected = expected_publication(
                access, native["publication_ref"], original=actual
            )
            same(
                actual,
                expected,
                "full original publication summary, links and source support",
            )
            require(
                full["kind"] == "result"
                and full["result_ref"] in access._metadata_refs,
                "Publication context lost its retained literal metadata owner.",
            )
            native = expected["original_explanation"]
        expected_context = {
            **_literal_context(access),
            "adapter": LINK_RULE,
            "bioactivity_context": role,
        }
        expected_status = "ok" if anchor._selection.count else "empty"
        expected_reason = (
            None if anchor._selection.count else "This retained container is empty."
        )
    else:
        require(
            anchor._context_only and link["availability"] == "missing_prerequisite",
            "Unavailable source context acquired a false focal identity.",
        )
        native = {"link": link}
        _, full = access._resolve(anchor._selection._target["location"])
        same(access._resolve(full)[0], native, "unavailable source context")
        require(
            full["kind"] == "result" and full["result_ref"] in access._metadata_refs,
            "Unavailable source context has no literal metadata owner.",
        )
        expected_context = {
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": LINK_RULE,
            "bioactivity_context": role,
            "captures": access.context["captures"],
        }
        expected_status = "missing_prerequisite"
        expected_reason = "The referenced original source statement is not retained; no replacement or attribution is inferred."
    _literal_selection(anchor, full)
    if view is not anchor:
        _literal_selection(view, full)
    require(
        view._context_only == anchor._context_only
        and view._machine_ref is None
        and anchor._machine_ref is None,
        "Bioactivity destination display changed its retained availability/operation kind.",
    )
    require(
        anchor._status == expected_status and anchor._reason == expected_reason,
        "Bioactivity destination changed its literal availability.",
    )
    same(
        anchor._context_override,
        expected_context,
        "bioactivity destination original focal/role context",
    )
    same(
        view._context_override,
        expected_context,
        "bioactivity destination display context",
    )
    same(
        anchor.native_payload, native, "bioactivity destination complete native payload"
    )
    same(
        record["native_payload"],
        native,
        "bioactivity destination recorded native payload",
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown bioactivity destination encoding.",
    )
    context = record["state"]["context"]
    require(
        context.get("mode") in ("live", "saved"),
        "Unknown saved bioactivity context mode.",
    )
    same(
        context,
        {**expected_context, "mode": context["mode"]},
        "bioactivity destination saved focal context",
    )
    _question(view)
    _literal_state(view, record)
    return native


def _filter_result(view, column, equals):
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
    status = view._status if unavailable else "ok" if entries else "empty"
    reason = (
        view._reason
        if unavailable
        else None
        if entries
        else "No items match this display selection; the original source scope is unchanged."
    )
    return entries, {"status": status, "reason": reason}


def display_filter(view, column, equals):
    entries, outcome = _filter_result(view, column, equals)
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=outcome["status"],
        _reason=outcome["reason"],
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(equals),
            "filter_policy": SELECTION_FORMAT,
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
        _selected=entries,
        _origin=view,
        _display_request={
            "operation": "sort",
            "column": column,
            "descending": descending,
            "unit": unit,
            "selection_policy": SELECTION_FORMAT,
        },
    )


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_exploration_storage import missing_selection

    options, fields = options_for_bioactivities(options), projection(fields)
    query = normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if (
            not is_result(selection._scientific)
            or selection._operation != "select:" + TOPIC
            or selection._fields != fields
        ):
            continue
        request = access._resolve(selection._context_location)[0]["request"]
        if canonical_json(request["options"]) != canonical_json(options):
            continue
        spec = request.get("selection")
        if (not active(query) and spec is None) or (
            spec is not None
            and canonical_json({key: spec[key] for key in query})
            == canonical_json(query)
        ):
            return selection
    return missing_selection(
        access, TOPIC, options, fields, query if active(query) else None
    )


def _saved_topic_view(explorer, options):
    for view in explorer._session["views"].values():
        if (
            view._saved_state is not None
            and is_view(view)
            and view._record_panel == TOPIC
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view.presentation != "detail"
            and view._machine_ref is None
            and view._selection._operation == "read"
            and canonical_json(view._selection._scientific.options)
            == canonical_json(options)
        ):
            return view
    return None


def saved_topic(explorer, origin, options=None):
    from .card_exploration_storage import not_saved

    options = options_for_bioactivities(options)
    view = _saved_topic_view(explorer, options)
    if view is not None:
        return replace(
            view,
            _explorer=explorer,
            _origin=explorer._origin if origin is None else origin,
            _display_request=None,
            _request=None,
        )
    return not_saved(
        explorer, "This exact bioactivity request and focus were not retained.", origin
    )


def open_item(item):
    """Open an exact retained focus or its original source record."""
    from .card_exploration_storage import not_saved

    parent, row = item._view, item._entry.value
    explorer = parent._explorer
    if row["kind"] == "bioactivity_record":
        return replace(
            parent,
            _selected=(item._entry,),
            _origin=parent,
            _display_request=None,
            _native_override=deepcopy(row["item"]),
            title=f"Original source activity record · {row['label']}",
            presentation="detail",
        )
    options = deepcopy(parent._selection._scientific.options)
    options.update(
        molecule_ref=row["molecule_ref"],
        measurement_ref=(
            row["measurement_ref"] if row["kind"] == "bioactivity_group" else None
        ),
    )
    view = _saved_topic_view(explorer, options_for_bioactivities(options))
    if view is None:
        return not_saved(
            explorer,
            "This exact bioactivity request and focus were not retained.",
            parent,
        )
    return replace(
        view,
        _explorer=explorer,
        _origin=parent,
        _display_request=None,
        _request=parent.request,
    )


def follow(item):
    """Return only a visited original destination with its exact link/back context."""
    from .card_exploration_storage import not_saved

    parent, link = item._view, item._entry.value
    explorer = parent._explorer
    for view in explorer._session["views"].values():
        origin = view._origin
        if (
            view._saved_state is not None
            and is_context(view)
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view._context_override.get("bioactivity_context") == link["role"]
            and view.title == link["label"]
            and origin is not None
            and origin._link_panel
            and canonical_json(origin.native_payload)
            == canonical_json(parent.native_payload)
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=parent,
                _display_request=None,
                _request=parent.request,
            )
    return not_saved(
        explorer, "This exact original bioactivity context was not retained.", parent
    )


def validate_filters(bundle):
    from .card_exploration_chemical import validate_filters as older_filters

    older = {
        key: record
        for key, record in bundle["views"].items()
        if record["flags"]["_record_panel"] != TOPIC
    }
    return older_filters({**bundle, "views": older})


def verification_report(bundle):
    from .card_exploration_chemical import verification_report as older_report

    older = {
        ref: item
        for ref, item in bundle["scientific_results"].items()
        if bundle["objects"][ref].get("context", {}).get("adapter") != ADAPTER
    }
    report = older_report({**bundle, "scientific_results": older})
    rules = set(report.get("verified_scientific_rules", []))
    for ref in bundle["scientific_results"]:
        wire = bundle["objects"][ref]
        if wire.get("context", {}).get("adapter") == ADAPTER and wire["native_payload"]:
            rules.update(
                wire["context"]["options"][key]
                for key in (
                    "classification_rule",
                    "measurement_rule",
                    "target_scope_rule",
                )
            )
    return {
        **report,
        "verifier": VERIFIER,
        "bioactivities": "original_frozen_v1_consistency_verified",
        "verified_scientific_rules": sorted(rules),
        "scientific_classifications": "historical_consistency_verified",
        "recorded_navigation_decisions": "Original molecule/group/source-record requests, typed quantities, activity/assay support and complete retained publication context independently verified. Source authenticity, article content and experimental independence remain unknown.",
    }


def retain_machine_views(root):
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
