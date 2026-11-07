"""Original literature exploration @19 binding over frozen retained inputs.

Expected values validate the recorded knowledge; they never replace it. The
reader uses no current Card, scientific reader, source client or live explorer.
"""

from copy import copy, deepcopy
from dataclasses import replace

from ._literature_history_v1.selection import (
    COLUMNS,
    active,
    equal,
    evaluate,
    normalize,
    projection,
    selection_ref,
    sorted_entries,
    validate_equality,
)
from ._literature_history_v1.selection import (
    FORMAT as SELECTION_FORMAT,
)
from .card_access import _Entry, _handle, _type
from .card_literature_history_v1 import (
    ADAPTER,
    TOPIC,
    expected_result,
    options_for_literature,
    restore_result,
)
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@19"
VERIFIER = "literature_exploration_binding@1"
LINK_RULE = "literature_context_links@1"
ADAPTERS = (
    "structure_exploration@1",
    "knowledge_coverage_exploration@1",
    "ligand_site_exploration@1",
    "quaternary_exploration@1",
    "assembly_generation_exploration@1",
    "assembly_generation_exploration@2",
    "chemical_classification_exploration@1",
    "bioactivity_exploration@1",
    ADAPTER,
)
SCHEMA = {
    "kind": "literature_exploration",
    "grain": "one exact native publication identity on the focal captured Card",
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
    session = getattr(access, "_exploration_session", None)
    sdk202_bioactivity = access.mode == "live" or (
        access.mode == "saved"
        and isinstance(session, dict)
        and session.get("format") == FORMAT
    )
    admitted = {ADAPTER}
    if sdk202_bioactivity:
        admitted.add("bioactivity_exploration@1")
    retained = {
        ref: wire
        for ref, wire in objects.items()
        if ref not in access._metadata_refs
        and isinstance(wire, dict)
        and "native_payload" in wire
        and isinstance(wire.get("context"), dict)
        and wire["context"].get("adapter") in admitted
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
    from .card_exploration_bioactivity_v2 import verify_objects as older_objects

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
            "Unknown literature manifest member or focal capture.",
        )
        options = options_for_literature(wire["context"]["options"])
        same(wire["context"]["options"], options, "literature effective options")
        expected = expected_result(accesses[record["focal"]], options, original=wire)
        require(
            ref == expected.result_ref,
            "Literature result identity differs from its original inputs/options.",
        )
        same(
            wire,
            expected.wire,
            "literature publication identities, all native roles, exact source membership and citation context",
        )
    older_objects({**bundle, "scientific_results": older}, accesses)


def _literal_context(access, mode="live"):
    return {**access.context, "mode": mode, "adapter": "literal_access@1"}


def _literal_selection(view, full, *, entries=None, result_override=None):
    """Verify the existing literal request grammar without interpreting opaque keys."""
    access, selection = view._explorer.access, view._selection
    node, bound = access._resolve(selection._target["location"])
    same(bound, full, "literature literal target location")
    request = {"operation": "read", "location": full, "text_slice": None}
    context = access._resolve(selection._context_location)[0]
    mode = context["context"].get("mode")
    require(mode in ("live", "saved"), "Unknown retained literal request mode.")
    same(
        context,
        {"context": _literal_context(access, mode), "request": request},
        "literature literal request",
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
        "Foreign literature literal selection operation.",
    )
    if result_override is None:
        require(
            selection.result_ref == ref, "Literature literal result identity differs."
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
        "Literature literal selection identity differs.",
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
        "literature literal target ownership",
    )
    expected_entries = access._children(node, full) if entries is None else entries
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in expected_entries],
        "literature literal child membership",
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
            active(query), "An unrestricted literature selection has a foreign policy."
        )
        entries, expected = evaluate(result, query)
        same(spec, expected, "literature exact membership, order and exclusions")
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
        "literature machine request",
    )
    require(
        selection.selection_ref == ref and selection._operation == "select:" + TOPIC,
        "Literature machine request identity differs.",
    )
    same(
        selection._target,
        {
            "node_type": "scientific_result",
            "location": selection._target["location"],
            "size": len(result.entries),
        },
        "literature machine target",
    )
    same(
        access._resolve(selection._target["location"])[1],
        result.location("native_payload"),
        "literature machine native target",
    )
    return entries


def _question(view, result=None):
    request, parent = view.request, view._origin
    inherited = parent is not None and (
        is_view(parent)
        or is_context(parent)
        or (parent._link_panel and parent.native_payload.get("rule") == LINK_RULE)
    )
    if inherited:
        require(
            parent._explorer.access._focal_key == view._explorer.access._focal_key,
            "Literature inherited navigation has a foreign focal capture.",
        )
        same(request, parent.request, "literature original question continuity")
    if request is None:
        return
    require(
        isinstance(request, dict)
        and set(request) == {"question", "topic", "options"}
        and request["question"] == "publications"
        and request["topic"] == TOPIC,
        "Unsupported literature human question.",
    )
    same(
        request["options"],
        options_for_literature(request["options"]),
        "literature question options",
    )
    if result is not None and not inherited:
        # Following a supplied Card's generic link creates a destination
        # explorer. A fresh explicit question belongs to that Card and may
        # differ from the originating link's request; it is not a publication
        # drill-down inheriting an earlier publication question.
        same(request["options"], result.options, "literature question/result scope")
        if parent is not None and parent._link_panel:
            access = view._explorer.access
            require(
                any(
                    candidate["capture"] == access._focal_key
                    for link in parent.native_payload["links"]
                    for candidate in link["candidates"]
                ),
                "Literature question has no retained originating Card destination.",
            )


def _view_state(view, record, result, entries):
    state = record["state"]
    same(state["schema"], SCHEMA, "literature schema")
    require(
        state["context"].get("mode") in ("live", "saved"),
        "Unknown literature saved display mode.",
    )
    same(
        state["context"],
        {**result.wire["context"], "mode": state["context"]["mode"]},
        "literature captured context",
    )
    same(
        state["coverage"], result.wire["coverage"], "literature source/request coverage"
    )
    items = {}
    for entry in entries:
        row, proof = entry.value, result.wire["support"][entry.key]
        items[
            _handle(
                "XI_", {"result_ref": result.result_ref, "location": entry.location}
            )
        ] = {
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
    same(state["items"], items, "literature labels, typed values and original support")


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
        "Foreign literature presentation flags.",
    )
    result = restore_result(view.result_ref, access._objects[view.result_ref])
    require(
        result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Literature view has a foreign focal capture.",
    )
    require(
        selection._slice is None
        and selection._outcome_override is None
        and view.presentation in SCHEMA["presentations"],
        "Unsupported literature selection/presentation options.",
    )
    if selection._operation.startswith("select:"):
        entries = _machine(selection, access, result)
    else:
        entries = result.entries
        human_ref = _handle(
            "XA_",
            {"format": "literature_human_selection@1", "result_ref": result.result_ref},
        )
        _literal_selection(
            view, result.location(), entries=entries, result_override=human_ref
        )
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in entries],
        "literature original row membership",
    )
    same(view._context_override, result.wire["context"], "literature context override")
    _view_state(view, record, result, entries)
    _question(view, result)
    require(
        view._machine_ref
        == (
            selection.selection_ref
            if selection._operation.startswith("select:")
            else None
        ),
        "Foreign literature machine-origin binding.",
    )
    operation, parent = view._display_request, view._origin
    if operation is not None:
        require(
            parent is not None
            and is_view(parent)
            and parent.result_ref == view.result_ref
            and parent._selection.selection_ref == selection.selection_ref,
            "Literature display crossed its original result/request.",
        )
        if operation.get("operation") == "filter":
            require(
                set(operation) == {"operation", "column", "equals", "filter_policy"}
                and operation["filter_policy"] == SELECTION_FORMAT,
                "Unsupported literature filter policy.",
            )
            expected_entries, expected_outcome = _filter_result(
                parent, operation["column"], operation["equals"]
            )
        elif operation.get("operation") == "sort":
            require(
                set(operation)
                == {"operation", "column", "descending", "unit", "selection_policy"}
                and operation["selection_policy"] == SELECTION_FORMAT,
                "Unsupported literature ordering policy.",
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
                "Unsupported literature display operation.",
            )
            expected_entries, expected_outcome = parent._selected, parent.outcome
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in expected_entries],
            "literature display order/membership",
        )
        same(view.outcome, expected_outcome, "literature display outcome")
    else:
        expected_presentation = (
            "summary"
            if selection._operation.startswith("select:")
            else "detail"
            if result.options["publication_ref"] is not None
            else "table"
        )
        require(
            view.presentation == expected_presentation,
            "Literature initial presentation differs from its original request.",
        )
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in entries],
            "literature unrestricted selection",
        )
        same(
            view.outcome,
            {key: result.wire["outcome"][key] for key in ("status", "reason")},
            "literature original outcome",
        )
        _verify_focus_origin(view, result)
    require(
        record.get("native_encoding", "json") == "json",
        "Unsupported literature native encoding.",
    )
    same(
        record["native_payload"],
        result.wire["native_payload"],
        "complete original literature native payload",
    )


def _verify_focus_origin(view, result):
    parent = view._origin
    if parent is None or not is_view(parent):
        return
    require(
        parent._explorer.access._focal_key == view._explorer.access._focal_key,
        "Literature drill-down has a foreign focal capture.",
    )
    same(
        {
            key: value
            for key, value in parent._selection._scientific.wire["context"].items()
            if key != "options"
        },
        {
            key: value
            for key, value in result.wire["context"].items()
            if key != "options"
        },
        "literature drill-down original capture context",
    )
    if parent.result_ref == view.result_ref:
        return
    focus = result.options["publication_ref"]
    require(
        focus is not None
        and any(
            entry.value["publication_ref"] == focus
            for entry in parent._selection._entries
        ),
        "Literature drill-down lost its selected original publication.",
    )


def verify_explanation(view, record=None):
    access, full = view._explorer.access, result_location(view)
    require(
        full is not None and is_explanation(view),
        "Missing original literature explanation result.",
    )
    key, wire = full["segments"][1]["value"], access._objects[full["result_ref"]]
    require(key in wire["rows"], "Foreign literature explanation row.")
    native, anchor, seen = wire["explanations"][key], view, set()
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen
            and anchor._origin is not None
            and is_explanation(anchor._origin),
            "Literature explanation display has a cyclic/foreign origin.",
        )
        seen.add(id(anchor))
        require(
            anchor.result_ref == anchor._origin.result_ref
            and anchor._selection.selection_ref
            == anchor._origin._selection.selection_ref,
            "Literature explanation display changed its original request.",
        )
        anchor = anchor._origin
    parent = anchor._origin
    require(
        parent is not None
        and is_view(parent)
        and parent.result_ref == full["result_ref"]
        and any(entry.key == key for entry in parent._selection._entries),
        "Literature explanation has a foreign original item/back context.",
    )
    entries = tuple(
        _Entry(row["location"], row["id"], access._resolve(row["location"])[0])
        for row in wire["support"][key]["source_assertions"]
        if row["state"] == "present"
    )
    _literal_selection(anchor, full, entries=entries)
    if view is not anchor:
        _literal_selection(view, full, entries=entries)
    expected_context = {
        **wire["context"],
        "adapter": LINK_RULE,
        "literature_context": "publication_explanation",
        "native_status": native["status"],
        "native_reason": native["reason"],
    }
    same(
        anchor._context_override,
        expected_context,
        "literature explanation original context",
    )
    same(
        view._context_override,
        expected_context,
        "literature explanation display context",
    )
    require(
        not any(
            (
                view._record_panel,
                view._field_panel,
                view._link_panel,
                view._route_catalog,
                view._question_catalog,
                view._context_only,
                view._focus,
                view._component_navigation,
            )
        )
        and view._selection._scientific is None
        and view._machine_ref is None,
        "Foreign literature explanation flags.",
    )
    reason = (
        "Some referenced original support is not retained; missing references and all available records remain inspectable."
        if native["status"] == "partial"
        else "Original publication links and source statements. ECO support, mentions, curation and measurement links retain their distinct meanings."
    )
    require(
        anchor._status == ("partial" if native["status"] == "partial" else "ok")
        and anchor._reason == reason,
        "Literature explanation changed its original availability.",
    )
    same(view.native_payload, native, "literature explanation full original inputs")
    _question(view)
    if record is not None:
        same(record["native_payload"], native, "literature recorded explanation")
        require(
            record.get("native_encoding", "json") == "json",
            "Unknown literature explanation encoding.",
        )
        same(
            record["state"]["context"],
            {**expected_context, "mode": record["state"]["context"]["mode"]},
            "literature saved explanation context",
        )
        require(
            record["state"]["context"]["mode"] in ("live", "saved"),
            "Unknown literature explanation mode.",
        )
        _literal_state(view, record)
    return native


def expected_links(access, wire, key):
    ref = next(ref for ref, value in access._objects.items() if value is wire)
    result = restore_result(ref, wire)
    original, membership_location = (
        wire["support"][key],
        result.location("support", key),
    )
    rows = []

    def membership(statement_id=None):
        return [
            {
                "basis": "retained_support_membership",
                "rule": "literature_support_membership@1",
                "support_location": deepcopy(membership_location),
                "statement_id": statement_id,
            }
        ]

    def link(role, label, target, location, statement_id=None):
        return {
            "role": role,
            "label": label,
            "target_ref": target,
            "support": membership(statement_id),
            "rule": LINK_RULE,
            "publication_ref": key,
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

    def missing(role, target, label, statement_id=None):
        return {
            "role": role,
            "label": label,
            "target_ref": target,
            "support": membership(statement_id),
            "rule": LINK_RULE,
            "publication_ref": key,
            "availability": "missing_prerequisite",
            "candidates": [],
            "paths": [],
            "blocked_paths": [],
        }

    for statement in original["source_assertions"]:
        identifier = statement["id"]
        if statement["state"] == "present":
            record = access._resolve(statement["location"])[0]
            source = record.get("source") or {}
            label = "Original source statement · " + " · ".join(
                str(value)
                for value in (
                    source.get("name"),
                    source.get("record_id"),
                    record.get("field_path"),
                    identifier,
                )
                if value is not None
            )
            rows.append(
                link("source", label, identifier, statement["location"], identifier)
            )
        else:
            rows.append(
                missing(
                    "source",
                    identifier,
                    "Unavailable original source statement · " + identifier,
                    identifier,
                )
            )
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
            record = access._resolve(location)[0]
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
                missing(
                    "original_relationship",
                    identifier,
                    "Unavailable original relationship · " + identifier,
                )
            )
    destinations.extend(
        (locator["role"], locator["label"], locator["location"])
        for locator in original["locator_locations"]
    )
    rows.extend(
        link(role, label, label, location) for role, label, location in destinations
    )
    return rows


def verify_links(view, record=None):
    access, native = view._explorer.access, view.native_payload
    require(
        view._link_panel
        and isinstance(native, dict)
        and native.get("rule") == LINK_RULE,
        "Unsupported literature navigation rule.",
    )
    _, full = access._resolve(native["source_location"])
    require(
        full["kind"] == "result"
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "rows"}
        and full["result_ref"] not in access._metadata_refs,
        "Literature links have no original row location.",
    )
    wire, key = access._objects[full["result_ref"]], full["segments"][1]["value"]
    require(
        wire.get("context", {}).get("adapter") == ADAPTER and key in wire["rows"],
        "Foreign literature navigation result.",
    )
    anchor, seen = view, set()
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen
            and anchor._origin is not None
            and anchor._origin._link_panel,
            "Literature navigation display has a cyclic/foreign origin.",
        )
        seen.add(id(anchor))
        require(
            anchor.result_ref == anchor._origin.result_ref
            and anchor._selection.selection_ref
            == anchor._origin._selection.selection_ref,
            "Literature navigation display changed its original request.",
        )
        anchor = anchor._origin
    parent = anchor._origin
    require(
        parent is not None
        and is_view(parent)
        and parent.result_ref == full["result_ref"]
        and any(entry.key == key for entry in parent._selection._entries),
        "Literature navigation lost its original selected row/back context.",
    )
    expected = {
        "rule": LINK_RULE,
        "inputs": access.context["captures"],
        "focal": access._focal_key,
        "source_location": full,
        "support_location": restore_result(full["result_ref"], wire).location(
            "support", key
        ),
        "links": expected_links(access, wire, key),
    }
    same(
        native,
        expected,
        "literature exact original source/relationship/locator destinations",
    )
    expected_context = {**wire["context"], "literature_context": "related"}
    if view._context_override is None:
        # The original LIVE _link_view retained its intermediate literal panel
        # before assigning the topic-specific readable context.
        expected_context = {**access.context, "mode": "live", "adapter": LINK_RULE}
    else:
        same(
            view._context_override,
            expected_context,
            "literature related original context",
        )
    _question(view)
    if record is not None:
        same(
            record["native_payload"],
            expected,
            "literature recorded related destinations",
        )
        require(
            record.get("native_encoding", "json") == "json",
            "Unknown literature navigation encoding.",
        )
        root = access._resolve(view._selection._target["location"])[1]
        entries = tuple(
            _Entry(
                {
                    **root,
                    "segments": [
                        {"type": "Key", "value": "links"},
                        {"type": "Index", "value": i},
                    ],
                },
                str(i),
                row,
            )
            for i, row in enumerate(expected["links"])
        )
        _literal_selection(view, root, entries=entries)
        same(
            record["state"]["context"],
            {**expected_context, "mode": record["state"]["context"]["mode"]},
            "literature saved related context",
        )
        require(
            record["state"]["context"]["mode"] in ("live", "saved"),
            "Unknown literature related mode.",
        )
        _literal_state(view, record)


def _literal_state(view, record):
    """Reuse declared literal cell/quantity predicates after binding new context."""
    from .card_exploration import CardItem
    from .card_exploration_storage import _cell_record
    from .card_exploration_verification import _verify_cell, _verify_display

    plain = copy(view)
    object.__setattr__(plain, "_saved_state", None)
    state = record["state"]
    same(state["schema"], plain.schema, "literature destination literal schema")
    same(state["coverage"], plain.coverage, "literature destination literal coverage")
    expected_refs = {
        _handle("XI_", {"result_ref": view.result_ref, "location": entry.location})
        for entry in view._selection._entries
    }
    require(
        set(state["items"]) == expected_refs,
        "Literature destination item closure differs.",
    )
    for entry in view._selection._entries:
        actual_node = view._explorer.access._resolve(entry.location)[0]
        same(entry.value, actual_node, "literature destination original literal child")
        item = CardItem(plain, entry)
        frozen = state["items"][item.item_ref]
        require(
            isinstance(frozen, dict)
            and set(frozen) == {"label", "kind", "support", "cells"}
            and isinstance(frozen["label"], str),
            "Unknown destination item shape.",
        )
        require(
            frozen["kind"] == item.kind, "Literature destination literal kind differs."
        )
        same(frozen["support"], item.support, "literature destination literal support")
        require(
            set(frozen["cells"]) == set(item.cells),
            "Literature destination cell membership differs.",
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
    if is_explanation(view) and "native_status" in (view._context_override or {}):
        return verify_explanation(view, record)
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
        "Foreign literature destination presentation flags.",
    )
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen
            and anchor._origin is not None
            and is_context(anchor._origin),
            "Literature destination display has a cyclic/foreign origin.",
        )
        seen.add(id(anchor))
        require(
            anchor._selection.selection_ref == anchor._origin._selection.selection_ref
            and anchor.result_ref == anchor._origin.result_ref,
            "Literature destination display changed its original request.",
        )
        anchor = anchor._origin
    parent = anchor._origin
    if parent is not None and is_context(parent):
        return _verify_literal_descendant(view, record, anchor, parent)
    require(
        parent is not None
        and parent._link_panel
        and parent.native_payload.get("rule") == LINK_RULE,
        "Literature destination lost its original link/back context.",
    )
    verify_links(parent)
    role = anchor._context_override.get("literature_context")
    choices = [
        link
        for link in parent.native_payload["links"]
        if link["role"] == role
        and (
            link["label"] == anchor.title
            if link["candidates"]
            else anchor.title == "Original publication input unavailable"
        )
        and link["publication_ref"] == anchor._context_override.get("publication_ref")
    ]
    # Unavailable destinations share a readable title; the retained link binds
    # their exact identity even when several original references are missing.
    if anchor._context_only:
        retained = anchor.native_payload.get("link")
        choices = [
            link for link in choices if canonical_json(link) == canonical_json(retained)
        ]
    require(
        len(choices) == 1, "Literature destination has no unique exact retained link."
    )
    link = choices[0]
    require(
        len(link["candidates"]) <= 1, "Unsupported literature destination ambiguity."
    )
    if link["candidates"]:
        require(
            not anchor._context_only
            and link["candidates"][0]["capture"] == access._focal_key,
            "Literature context switched to a foreign capture.",
        )
        full = link["candidates"][0]["location"]
        native = access._resolve(full)[0]
        expected_context = {
            **access.context,
            "mode": "live",
            "adapter": LINK_RULE,
            "literature_context": role,
            "publication_ref": link["publication_ref"],
        }
        expected_status = "ok" if anchor._selection.count else "empty"
        expected_reason = (
            None if anchor._selection.count else "This retained container is empty."
        )
    else:
        require(
            anchor._context_only and link["availability"] == "missing_prerequisite",
            "Unavailable original literature context acquired a false focal identity.",
        )
        native = {"link": link}
        _, full = access._resolve(anchor._selection._target["location"])
        same(access._resolve(full)[0], native, "unavailable literature source context")
        require(
            full["kind"] == "result" and full["result_ref"] in access._metadata_refs,
            "Unavailable literature context has no literal metadata owner.",
        )
        expected_context = {
            "card_ref": None,
            "snapshot_id": None,
            "subject_ref": link["target_ref"],
            "profile": None,
            "mode": "live",
            "adapter": LINK_RULE,
            "literature_context": role,
            "publication_ref": link["publication_ref"],
            "captures": access.context["captures"],
        }
        expected_status = "missing_prerequisite"
        expected_reason = "The referenced original record is not retained. Its reference remains inspectable; no replacement statement or article content is inferred."
    _literal_selection(anchor, full)
    if view is not anchor:
        _literal_selection(view, full)
    require(
        view._context_only == anchor._context_only
        and view._machine_ref is None
        and anchor._machine_ref is None,
        "Literature destination display changed its retained availability/operation kind.",
    )
    require(
        anchor._status == expected_status and anchor._reason == expected_reason,
        "Literature destination changed its literal availability.",
    )
    same(
        anchor._context_override,
        expected_context,
        "literature destination original focal/role context",
    )
    same(
        view._context_override,
        expected_context,
        "literature destination display context",
    )
    same(
        anchor.native_payload, native, "literature destination complete native payload"
    )
    same(
        record["native_payload"],
        native,
        "literature destination recorded native payload",
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown literature destination encoding.",
    )
    context = record["state"]["context"]
    require(
        context.get("mode") in ("live", "saved"),
        "Unknown saved literature context mode.",
    )
    same(
        context,
        {**expected_context, "mode": context["mode"]},
        "literature destination saved focal context",
    )
    _question(view)
    _literal_state(view, record)
    return native


def _filter_result(view, column, equals):
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
    status = view._status if unavailable else "ok" if entries else "empty"
    reason = (
        view._reason
        if unavailable
        else None
        if entries
        else "No publications match this display selection; the original catalog and source scope are unchanged."
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

    options, fields = options_for_literature(options), projection(fields)
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
            and view._machine_ref is None
            and view._selection._operation == "read"
            and view._selected == view._selection._entries
            and canonical_json(view._selection._scientific.options)
            == canonical_json(options)
        ):
            return view
    return None


def saved_topic(explorer, origin, options=None):
    from .card_exploration_storage import not_saved

    options = options_for_literature(options)
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
        explorer, "This exact literature request and focus were not retained.", origin
    )


def open_item(item):
    """Open only the exact original focused publication retained in this file."""
    from .card_exploration_storage import not_saved

    parent, row = item._view, item._entry.value
    explorer = parent._explorer
    options = {"publication_ref": row["publication_ref"]}
    view = _saved_topic_view(explorer, options_for_literature(options))
    if view is None:
        return not_saved(
            explorer,
            "This exact literature request and focus were not retained.",
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
    """Return only a visited original endpoint with its exact link/back context."""
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
            and view._context_override.get("literature_context") == link["role"]
            and view._context_override.get("publication_ref") == link["publication_ref"]
            and origin is not None
            and origin._link_panel
            and canonical_json(origin.native_payload)
            == canonical_json(parent.native_payload)
        ):
            if view._context_only:
                if canonical_json(view.native_payload.get("link")) != canonical_json(
                    link
                ):
                    continue
            elif view.title != link["label"]:
                continue
            return replace(
                view,
                _explorer=explorer,
                _origin=parent,
                _display_request=None,
                _request=parent.request,
            )
    return not_saved(
        explorer, "This exact original literature context was not retained.", parent
    )


def validate_filters(bundle):
    from .card_exploration_bioactivity import validate_filters as older_filters

    older = {
        key: record
        for key, record in bundle["views"].items()
        if record["flags"]["_record_panel"] != TOPIC
    }
    return older_filters({**bundle, "views": older})


def verification_report(bundle):
    """Describe only manifest-owned predicates checked by this saved reader.

    Literal metadata may contain rule-like strings or adapter names. Those
    source values are never promoted to claims about scientific verification.
    Earlier formats keep their original reports unchanged.
    """
    rules, policies, adapters = set(), set(), set()

    def declared(value):
        if isinstance(value, dict) and isinstance(value.get("rule"), str):
            rules.add(value["rule"])

    for ref in bundle["scientific_results"]:
        wire = bundle["objects"][ref]
        adapter, native = wire["context"]["adapter"], wire["native_payload"]
        adapters.add(adapter)
        for rule in wire["context"].get("rules", []):
            declared(rule)
        declared(wire.get("coverage", {}).get("rule"))
        if adapter == "chemical_classification_exploration@1":
            rules.add("chemical_classification_context@1")
        if adapter == "bioactivity_exploration@1" and native:
            rules.update(
                wire["context"]["options"][key]
                for key in (
                    "classification_rule",
                    "measurement_rule",
                    "target_scope_rule",
                )
            )
        if adapter in (
            "assembly_generation_exploration@1",
            "assembly_generation_exploration@2",
        ):
            for key in (
                "rule",
                "operator_binding_rule",
                "component_binding_rule",
                "occurrence_rule",
            ):
                if isinstance(native.get(key), str):
                    rules.add(native[key])
        if adapter == "ligand_site_exploration@1":
            declared(native.get("classification"))
            declared(native.get("canonical_reference"))
            for annotation in native.get("annotated_sites", []):
                if isinstance(annotation.get("source_support_rule"), str):
                    rules.add(annotation["source_support_rule"])
            for item in native.get("items", []):
                if isinstance(item.get("instance_rule"), str):
                    rules.add(item["instance_rule"])
        if adapter == "quaternary_exploration@1":
            for rule in native.get("rules", []):
                declared(rule)
            declared(native.get("canonical_reference"))
            declared(wire.get("explanation", {}).get("rule"))
        if adapter == "knowledge_coverage_exploration@1":
            declared(native.get("rule"))
        for explanation in wire.get("explanations", {}).values():
            declared(explanation.get("rule"))

    for view in bundle["views"].values():
        selection = view["selection"]
        if selection.get("scientific_result_ref") not in bundle["scientific_results"]:
            continue
        location = selection["context_location"]
        if location["kind"] == "lookup":
            location = bundle["locations"][location["location_ref"]]
        request = bundle["objects"][location["result_ref"]]["request"]
        if request.get("selection") is not None:
            policies.add(request["selection"]["format"])

    report = {
        "verifier": VERIFIER,
        "bindings": "original captured snapshots, retained literal/scientific values, units, support, requests and display membership",
        "scientific_classifications": "historical_consistency_verified"
        if rules
        else "not_evaluated",
        "verified_scientific_adapters": [
            adapter for adapter in ADAPTERS if adapter in adapters
        ],
        "verified_scientific_rules": sorted(rules),
        "verified_selection_policies": sorted(policies),
        "explanations": "retained original explanations checked at their original scope",
        "historical_catalog": "frozen initial exploration v1 source/area declarations",
        "recorded_navigation_decisions": "Original publication identities, all citation/support roles, exact executed queries, native explanations, source/relationship membership, locators and original back context independently verified. Article reading, source authenticity and scientific truth remain unestablished.",
    }
    for adapter, key in (
        (ADAPTER, "literature"),
        ("bioactivity_exploration@1", "bioactivities"),
        ("chemical_classification_exploration@1", "chemical_classification"),
    ):
        if adapter in adapters:
            report[key] = (
                "original_frozen_v2_consistency_verified"
                if key == "bioactivities"
                else "original_frozen_v1_consistency_verified"
            )
    return report


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


def saved_answer(explorer, options, origin):
    """Recover only the originally executed shared publication question."""
    from .card_exploration_storage import not_saved

    options = options_for_literature(options)
    request = {"question": "publications", "topic": TOPIC, "options": options}
    for view in explorer._session["views"].values():
        if (
            view._saved_state is not None
            and is_view(view)
            and view._record_panel == TOPIC
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view._machine_ref is None
            and view._selection._operation == "read"
            and view._selected == view._selection._entries
            and view._selection._scientific.options == options
            and view.request == request
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
                _display_request=None,
            )
    return not_saved(
        explorer,
        "This literature question and its effective options were not retained.",
        origin,
    )


def _verify_literal_descendant(view, record, anchor, parent):
    access = view._explorer.access
    full = access._resolve(anchor._selection._target["location"])[1]
    require(
        any(
            access._resolve(entry.location)[1] == full
            for entry in parent._selection._entries
        ),
        "Literature literal descendant was not an original selected child.",
    )
    same(
        anchor._context_override,
        parent._context_override,
        "literature descendant inherited context",
    )
    same(
        view._context_override,
        parent._context_override,
        "literature descendant display context",
    )
    require(
        anchor._context_only == parent._context_only
        and view._context_only == parent._context_only
        and anchor._machine_ref is None
        and view._machine_ref is None,
        "Literature descendant changed its original availability/operation kind.",
    )
    _literal_selection(anchor, full)
    if view is not anchor:
        _literal_selection(view, full)
    status = "ok" if anchor._selection.count else "empty"
    reason = None if anchor._selection.count else "This retained container is empty."
    require(
        anchor._status == status and anchor._reason == reason,
        "Literature descendant changed its literal availability.",
    )
    native = access._resolve(full)[0]
    same(
        record["native_payload"], native, "literature descendant complete original node"
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown literature descendant encoding.",
    )
    context = record["state"]["context"]
    require(
        context.get("mode") in ("live", "saved"),
        "Unknown saved literature descendant mode.",
    )
    same(
        context,
        {**parent._context_override, "mode": context["mode"]},
        "literature descendant saved context",
    )
    _question(view)
    _literal_state(view, record)
    return native
