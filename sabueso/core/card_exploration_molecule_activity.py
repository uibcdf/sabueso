"""Private molecule activity binding prepared for logical exploration @21.

Only original retained values are exposed. Independent expected predicates
authenticate science, source membership, original order and native crossings.
Storage dispatch and public saving remain disabled until complete qualification.
"""

from copy import deepcopy
from dataclasses import replace

from ._molecule_activity_history_v1.selection import (
    COLUMNS,
    QUANTITY_FIELD,
    active,
    equal,
    normalize,
    projection,
    sorted_entries,
    validate_equality,
)
from ._molecule_activity_history_v1.selection import (
    FORMAT as SELECTION_FORMAT,
)
from .card_access import _Entry, _handle
from .card_exploration_literature import ADAPTERS as PREVIOUS_ADAPTERS
from .card_exploration_literature import _literal_selection, _literal_state
from .card_molecule_activity_history_v1 import (
    ADAPTER,
    TOPIC,
    expected_result,
    expected_selection,
    options_for_activity_context,
    restore_result,
)
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@21"
VERIFIER = "molecule_activity_exploration_binding@1"
LINK_RULE = "molecule_activity_context_links@1"
# The original producer used Python equality here, including 33 == 33.0.
# Preserve that historical interpretation; never rewrite either retained operand.
ROOT_RETURN_EQUALITY = "molecule_activity_root_selection_python_equality@1"
ADAPTERS = (*PREVIOUS_ADAPTERS, ADAPTER)
SCHEMA = {
    "kind": "molecule_activity_context",
    "grain": "one exact supplied target context, native group or source activity record under explicit molecule identity",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, label):
    require(
        canonical_json(actual) == canonical_json(expected),
        f"Saved {label} differs from its original molecule binding.",
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
    value = access._objects[full["result_ref"]]
    return (
        full
        if isinstance(value, dict)
        and value.get("context", {}).get("adapter") == ADAPTER
        else None
    )


def is_explanation(view):
    full = result_location(view)
    return (
        full is not None
        and len(full["segments"]) == 2
        and full["segments"][0] == {"type": "Key", "value": "explanations"}
    )


def _policies(options):
    return {
        key: value
        for key, value in options.items()
        if key not in ("target_card_ref", "molecule_ref", "measurement_ref")
    }


def register_bundle(bundle, objects, access):
    retained = {
        ref: wire
        for ref, wire in objects.items()
        if ref not in access._metadata_refs
        and isinstance(wire, dict)
        and isinstance(wire.get("context"), dict)
        and wire["context"].get("adapter") == ADAPTER
        and "native_payload" in wire
    }
    if not retained:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    manifest = bundle.setdefault("scientific_results", {})
    session = access._exploration_session or {}
    for ref, wire in retained.items():
        focal = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == wire["context"]["card_ref"]
            and capture.snapshot == wire["context"]["snapshot_id"]
        )
        results = [
            value
            for value in access._scientific_cache.values()
            if getattr(value, "result_ref", None) == ref
        ]
        if results:
            keys = [entry.key for entry in results[0].entries]
        else:
            require(
                access.mode == "saved" and session.get("format") == FORMAT,
                "Original molecule entry order is unavailable.",
            )
            witnesses = [
                view._selection._scientific
                for view in session.get("views", {}).values()
                if view.result_ref == ref and is_view(view)
            ]
            require(witnesses, "Original molecule entry order is unavailable.")
            keys = [entry.key for entry in witnesses[0].entries]
        manifest[ref] = {"focal": focal, "entry_keys": list(keys)}
    crossings = {}
    for view in session.get("views", {}).values():
        if (
            not is_context(view)
            or view._context_override.get("activity_context")
            != "native_ligand_crossing"
        ):
            continue
        navigation = view._context_override["molecule_activity_navigation"]
        ref = navigation["source_result_ref"]
        if ref not in retained:
            continue
        _, location = view._explorer.access._resolve(
            view._selection._target["location"]
        )
        record = {
            "focal": view._explorer.access._focal_key,
            "source_result_ref": ref,
            "target_card_ref": navigation["target_card_ref"],
            "inputs": list(view._explorer.access._inputs),
            "policies": _policies(navigation["scientific_options"]),
            "navigation": deepcopy(navigation),
            "location": location,
        }
        require(
            location["kind"] == "result" and location["result_ref"] in objects,
            "Native crossing wrapper is outside the retained object closure.",
        )
        crossings[_handle("MX_", record)] = record
    bundle["molecule_activity_crossings"] = crossings


def verify_objects(bundle, accesses):
    from .card_exploration_literature import verify_objects as previous_objects

    previous, expected = {}, {}
    for ref, record in bundle["scientific_results"].items():
        require(
            ref in bundle["objects"] and isinstance(record, dict),
            "Missing molecule result or manifest record.",
        )
        wire = bundle["objects"][ref]
        require(
            isinstance(wire, dict) and isinstance(wire.get("context"), dict),
            "Missing retained scientific context.",
        )
        if wire["context"].get("adapter") != ADAPTER:
            previous[ref] = record
            continue
        require(
            set(record) == {"focal", "entry_keys"} and record["focal"] in accesses,
            "Unsupported molecule manifest members or focal capture.",
        )
        options = options_for_activity_context(wire["context"]["options"])
        same(options, wire["context"]["options"], "molecule effective options")
        original = expected_result(accesses[record["focal"]], options, original=wire)
        require(
            ref == original.result_ref,
            "Molecule result identity differs from original inputs/options.",
        )
        same(
            wire,
            original.wire,
            "molecule identity, all native contexts and exact source membership",
        )
        same(
            record["entry_keys"],
            [entry.key for entry in original.entries],
            "molecule original row order",
        )
        expected[ref] = original
    require(expected, "Format @21 requires an original molecule activity result.")
    previous_objects({**bundle, "scientific_results": previous}, accesses)
    crossings = bundle["molecule_activity_crossings"]
    require(
        isinstance(crossings, dict),
        "Original molecule crossing manifest must be an object.",
    )
    for key, record in crossings.items():
        require(
            isinstance(record, dict)
            and set(record)
            == {
                "focal",
                "source_result_ref",
                "target_card_ref",
                "inputs",
                "policies",
                "navigation",
                "location",
            },
            "Unsupported native crossing manifest members.",
        )
        require(
            key == _handle("MX_", record),
            "Original crossing manifest identity differs.",
        )
        ref = record["source_result_ref"]
        require(
            ref in expected
            and record["focal"] == bundle["scientific_results"][ref]["focal"],
            "Native crossing has a foreign molecule result or focal capture.",
        )
        original, access = expected[ref], accesses[record["focal"]]
        same(
            record["inputs"], list(access._inputs), "crossing ordered input occurrences"
        )
        same(
            record["policies"],
            _policies(original.options),
            "crossing scientific policies",
        )
        navigation, pin = record["navigation"], record["target_card_ref"]
        require(
            isinstance(navigation, dict)
            and navigation.get("rule") == LINK_RULE
            and navigation.get("source_result_ref") == ref
            and navigation.get("source_row_key") in original.wire["rows"]
            and navigation.get("molecule_card_ref") == access._focal.pin
            and navigation.get("target_card_ref") == pin,
            "Native crossing has a foreign original row/navigation scope.",
        )
        same(
            navigation["scientific_options"],
            original.options,
            "crossing originating scientific options",
        )
        _, location = original.native_crossing(pin)
        wrapper = original._access._objects[location["result_ref"]]
        same(record["location"], location, "original native wrapper location")
        require(
            location["result_ref"] in bundle["objects"],
            "Original native wrapper is missing.",
        )
        same(
            bundle["objects"][location["result_ref"]],
            wrapper,
            "complete native crossing and exact wrapper owner",
        )


def retained_result(access, ref, bundle):
    """Expose verified retained data after original object admission."""
    record = bundle["scientific_results"][ref]
    crossings = {}
    for crossing in bundle["molecule_activity_crossings"].values():
        if crossing["source_result_ref"] != ref:
            continue
        pin, location = crossing["target_card_ref"], crossing["location"]
        value = {
            "wrapper": access._objects[location["result_ref"]],
            "location": location,
            "inputs": crossing["inputs"],
            "policies": crossing["policies"],
        }
        if pin in crossings:
            same(crossings[pin], value, "repeated native crossing scope")
        crossings[pin] = value
    return restore_result(
        access,
        ref,
        access._objects[ref],
        entry_keys=record["entry_keys"],
        native_crossings=crossings,
    )


def validate_filters(bundle):
    from .card_exploration_literature import validate_filters as previous_filters

    return previous_filters(
        {
            **bundle,
            "views": {
                key: record
                for key, record in bundle["views"].items()
                if record["flags"]["_record_panel"] != TOPIC
            },
        }
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
            and canonical_json(view.native_payload)
            == canonical_json(view._selection._scientific.native)
            and canonical_json(view._selection._scientific.options)
            == canonical_json(options)
        ):
            return view
    return None


def saved_topic(explorer, origin, options=None):
    from .card_exploration_storage import not_saved

    options = options_for_activity_context(options)
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
        explorer,
        "This exact original molecule activity request was not retained.",
        origin,
    )


def open_item(item):
    from .card_exploration_storage import not_saved

    parent, row = item._view, item._entry.value
    options = deepcopy(parent._selection._scientific.options)
    if row["kind"] == "activity_context_target":
        options.update(target_card_ref=row["target_card_ref"], measurement_ref=None)
    elif row["kind"] == "activity_context_group":
        options.update(
            target_card_ref=row["target_card_ref"],
            measurement_ref=row["measurement_ref"],
        )
    else:
        for view in parent._explorer._session["views"].values():
            if (
                view._saved_state is not None
                and is_view(view)
                and view.result_ref == parent.result_ref
                and view._display_request is None
                and len(view._selected) == 1
                and view._selected[0].location == item._entry.location
                and view.presentation == "detail"
                and canonical_json(view.native_payload) == canonical_json(row["item"])
                and view._origin is not None
                and is_view(view._origin)
            ):
                return replace(
                    view,
                    _explorer=parent._explorer,
                    _origin=parent,
                    _display_request=None,
                    _request=parent.request,
                )
        return not_saved(
            parent._explorer,
            "This original source-record detail was not retained.",
            parent,
        )
    view = _saved_topic_view(parent._explorer, options)
    if view is None:
        return not_saved(
            parent._explorer,
            "This exact original molecule drill-down was not retained.",
            parent,
        )
    return replace(
        view,
        _explorer=parent._explorer,
        _origin=parent,
        _request=parent.request,
        _display_request=None,
    )


def follow(item):
    from .card_exploration_storage import not_saved

    parent, link, explorer = item._view, item._entry.value, item._view._explorer
    navigation, role = link["molecule_activity_navigation"], link["role"]
    if role == "molecule_root":
        for view in explorer._session["views"].values():
            if (
                view.view_ref == navigation["molecule_root_view_ref"]
                and _selection_binding(view) == navigation["molecule_root_selection"]
            ):
                return replace(view, _origin=parent, _request=parent.request)
    for view in explorer._session["views"].values():
        if (
            view._saved_state is None
            or not is_context(view)
            or view._display_request is not None
            or view._context_override.get("activity_context") != role
            or canonical_json(
                view._context_override.get("molecule_activity_navigation")
            )
            != canonical_json(navigation)
            or view._origin is None
            or not view._origin._link_panel
            or canonical_json(view._origin.native_payload)
            != canonical_json(parent.native_payload)
        ):
            continue
        return replace(
            view, _origin=parent, _display_request=None, _request=parent.request
        )
    return not_saved(
        explorer,
        "This exact visited molecule activity endpoint was not retained.",
        parent,
    )


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


def _original_context(view):
    """Keep the original binding when the receiving session changes mode."""
    if view._context_override is not None:
        return deepcopy(view._context_override)
    return {**view._explorer.access.context, "mode": "live"}


def _question(view, result=None):
    parent, request = view._origin, view.request
    inherited = parent is not None and (is_view(parent) or is_context(parent))
    if inherited:
        same(request, parent.request, "molecule originating question continuity")
    if request is None:
        return
    require(
        isinstance(request, dict)
        and set(request) == {"question", "topic", "options"}
        and request["question"] == "measured_targets"
        and request["topic"] == TOPIC,
        "Unsupported original molecule activity question.",
    )
    same(
        request["options"],
        options_for_activity_context(request["options"]),
        "molecule question effective options",
    )
    if result is not None and not inherited:
        same(request["options"], result.options, "molecule question/result scope")


def _machine(selection, access, result):
    context = access._resolve(selection._context_location)[0]
    request = context["request"]
    spec = request.get("selection")
    query = (
        {}
        if spec is None
        else {key: spec[key] for key in ("where", "item_refs", "order_by")}
    )
    ref, entries, fields, expected = expected_selection(
        result, fields=selection._fields, **query
    )
    same(spec, expected, "molecule machine membership, order and exclusions")
    expected_request = {
        "topic": TOPIC,
        "fields": list(fields),
        "options": result.options,
    }
    if expected is not None:
        expected_request["selection"] = expected
    same(
        context,
        {"context": result.wire["context"], "request": expected_request},
        "molecule machine request context",
    )
    require(
        selection.selection_ref == ref and selection._operation == "select:" + TOPIC,
        "Molecule machine request identity differs.",
    )
    same(
        selection._target,
        {
            "node_type": "scientific_result",
            "size": len(result.entries),
            "location": selection._target["location"],
        },
        "molecule machine target",
    )
    same(
        access._resolve(selection._target["location"])[1],
        result.location("native_payload"),
        "molecule machine original native target",
    )
    return entries


def _filter_result(view, column, equals):
    validate_equality(column, equals)
    result = view._selection._scientific
    require(
        view._status in ("ok", "empty") or result.entries,
        "Unavailable molecule result has no filterable rows.",
    )
    entries = tuple(
        entry
        for entry in view._selected
        if equal(result.value(entry.key, column), equals)
    )
    outcome = (
        view.outcome
        if view._status not in ("ok", "empty")
        else {
            "status": "ok" if entries else "empty",
            "reason": None
            if entries
            else "No displayed items match; the original supplied contexts and scientific outcomes are unchanged.",
        }
    )
    return entries, outcome


def display_filter(view, column, equals):
    from ._molecule_activity_history_v1.selection import quantity_node

    entries, outcome = _filter_result(view, column, equals)
    operand = (
        quantity_node(equals)
        if column == "measurement"
        and equals is not None
        and not isinstance(equals, dict)
        else deepcopy(equals)
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=outcome["status"],
        _reason=outcome["reason"],
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": operand,
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
        _selected=tuple(entries),
        _origin=view,
        _display_request={
            "operation": "sort",
            "column": column,
            "descending": descending,
            "unit": unit,
            "selection_policy": SELECTION_FORMAT,
        },
    )


def verify_view(view, record):
    """Bind every human/machine row, quantity, display and original drill-down."""
    access, selection, parent = view._explorer.access, view._selection, view._origin
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
        "Foreign molecule presentation flags.",
    )
    result = selection._scientific
    require(
        result.result_ref == selection.result_ref
        and result.wire["context"]["card_ref"] == access._focal.pin
        and result.wire["context"]["snapshot_id"] == access._focal.snapshot,
        "Molecule view has a foreign result or focal capture.",
    )
    require(
        selection._slice is None
        and selection._outcome_override is None
        and view.presentation in SCHEMA["presentations"],
        "Unsupported molecule presentation.",
    )
    machine = selection._operation.startswith("select:")
    entries = _machine(selection, access, result) if machine else result.entries
    if not machine:
        ref = _handle(
            "XA_",
            {
                "format": "molecule_activity_human_selection@1",
                "result_ref": result.result_ref,
            },
        )
        _literal_selection(
            view, result.location(), entries=entries, result_override=ref
        )
    same(
        [vars(entry) for entry in selection._entries],
        [vars(entry) for entry in entries],
        "molecule original row membership",
    )
    require(
        view._machine_ref == (selection.selection_ref if machine else None),
        "Foreign molecule machine-origin binding.",
    )
    _question(view, result)
    root_return = parent is not None and parent._link_panel and is_context(parent)
    if root_return:
        navigation = parent._context_override["molecule_activity_navigation"]
        require(
            _selection_binding(view) == navigation["molecule_root_selection"],
            "Molecule return differs under the original Python selection-equality policy.",
        )
    elif view._display_request is not None:
        operation = view._display_request
        require(
            parent is not None
            and is_view(parent)
            and parent.result_ref == view.result_ref
            and parent._selection.selection_ref == selection.selection_ref,
            "Molecule display crossed its original result/request.",
        )
        if operation.get("operation") == "filter":
            require(
                set(operation) == {"operation", "column", "equals", "filter_policy"}
                and operation["filter_policy"] == SELECTION_FORMAT,
                "Unsupported molecule filter policy.",
            )
            selected, outcome = _filter_result(
                parent, operation["column"], operation["equals"]
            )
        elif operation.get("operation") == "sort":
            require(
                set(operation)
                == {"operation", "column", "descending", "unit", "selection_policy"}
                and operation["selection_policy"] == SELECTION_FORMAT,
                "Unsupported molecule ordering policy.",
            )
            selected = sorted_entries(
                parent._selected,
                result,
                operation["column"],
                descending=operation["descending"],
                unit=operation["unit"],
            )
            outcome = parent.outcome
        else:
            same(
                operation,
                {"operation": "presentation"},
                "molecule presentation operation",
            )
            selected, outcome = parent._selected, parent.outcome
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in selected],
            "molecule display membership and order",
        )
        same(view.outcome, outcome, "molecule display outcome")
    elif view.presentation == "detail":
        require(
            parent is not None
            and is_view(parent)
            and parent.result_ref == view.result_ref
            and result.wire["context"]["grain"] == "record"
            and len(view._selected) == 1
            and view._selected[0] in parent._selected,
            "Source-record detail lost its exact parent row.",
        )
    else:
        same(
            [vars(entry) for entry in view._selected],
            [vars(entry) for entry in entries],
            "molecule unrestricted selection",
        )
        same(
            view.outcome,
            {key: result.wire["outcome"][key] for key in ("status", "reason")},
            "molecule original result outcome",
        )
        require(
            view.presentation == ("summary" if machine else "table"),
            "Molecule initial presentation differs.",
        )
        if parent is not None and is_view(parent):
            original = parent._selection._scientific.options
            options = deepcopy(original)
            rows = parent._selected
            if result.wire["context"]["grain"] == "group":
                require(
                    any(
                        row.value["target_card_ref"]
                        == result.options["target_card_ref"]
                        for row in rows
                    ),
                    "Molecule drill-down lost its selected exact target.",
                )
                options.update(
                    target_card_ref=result.options["target_card_ref"],
                    measurement_ref=None,
                )
            elif result.wire["context"]["grain"] == "record":
                require(
                    any(
                        row.value["measurement_ref"]
                        == result.options["measurement_ref"]
                        and row.value["target_card_ref"]
                        == result.options["target_card_ref"]
                        for row in rows
                    ),
                    "Molecule drill-down lost its selected native group.",
                )
                options.update(
                    target_card_ref=result.options["target_card_ref"],
                    measurement_ref=result.options["measurement_ref"],
                )
            same(result.options, options, "molecule drill-down original policies")
    detail = view.presentation == "detail" and view._display_request is None
    expected_context = deepcopy(result.wire["context"])
    expected_native = result.wire["native_payload"]
    if detail:
        expected_context = {
            **_original_context(parent),
            "target_card_ref": view._selected[0].value["target_card_ref"],
        }
        expected_native = view._selected[0].value["item"]
    same(view._context_override, expected_context, "molecule original context override")
    _view_state(view, record, result, entries)
    require(
        record.get("native_encoding", "json") == "json",
        "Unsupported molecule native encoding.",
    )
    same(
        record["native_payload"],
        expected_native,
        "molecule complete original native payload",
    )


def saved_selection(access, fields, options, where, item_refs, order_by):
    from .card_exploration_storage import missing_selection

    options, fields = options_for_activity_context(options), projection(fields)
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
                "Recorded molecule activity machine selection",
                presentation="summary",
                _record_panel=TOPIC,
                _native_override=wire["native_payload"],
                _context_override=wire["context"],
                _status=wire["outcome"]["status"],
                _reason=wire["outcome"].get("reason"),
                _machine_ref=selection.selection_ref,
            )
            existing.add(selection.selection_ref)


# Original SDK211 navigation vocabulary; independent of the current LIVE helpers.
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


def expected_navigation(item):
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
        "identity_edges": deepcopy(
            result.wire["support"][item._entry.key]["identity_edges"]
        ),
        "identity_membership": deepcopy(
            result.wire["support"][item._entry.key]["identity_membership"]
        ),
    }


def _context(parent, navigation, role):
    return {
        **_original_context(parent),
        "adapter": LINK_RULE,
        "activity_context": role,
        "molecule_card_ref": navigation["molecule_card_ref"],
        "target_card_ref": navigation["target_card_ref"],
        "molecule_activity_navigation": deepcopy(navigation),
    }


def _located_link(explorer, role, label, location, basis, navigation):
    capture = explorer.access._focal_key
    if location["kind"] == "card":
        matches = [
            key
            for key, value in explorer.access._captures.items()
            if value.pin == location["card_ref"]
            and value.snapshot == location["snapshot_id"]
        ]
        require(
            len(matches) == 1, "A molecule link requires its exact retained capture."
        )
        capture = matches[0]
    return {
        "role": role,
        "label": label,
        "target_ref": label,
        "support": deepcopy(basis),
        "rule": LINK_RULE,
        "candidates": [
            {
                "location": deepcopy(location),
                "capture": capture,
                "basis": "exact_retained_node",
            }
        ],
        "paths": [],
        "blocked_paths": [],
        "availability": "available",
        "molecule_activity_navigation": deepcopy(navigation),
    }


def expected_links(item):
    """Expose exact join, source, assay, record and full target destinations."""
    parent, explorer = item._view, item._view._explorer
    result, basis = (
        parent._selection._scientific,
        [parent._selection._scientific.wire["support"][item._entry.key]],
    )
    original, navigation = basis[0], expected_navigation(item)
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
                (
                    "Native context only · original activity relationship · "
                    if relationship["id"]
                    in original["identity_membership"]["context_only_relationship_ids"]
                    else "Original identity or activity relationship · "
                )
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
    return rows


def _view_state(view, record, result, entries):
    from pyunitwizard import QuantityRecord

    from .quantities import to_quantity

    state = record["state"]
    same(state["schema"], SCHEMA, "molecule activity schema")
    require(
        state["context"].get("mode") in ("live", "saved"),
        "Unknown molecule activity saved display mode.",
    )
    same(
        state["context"],
        {**_original_context(view), "mode": state["context"]["mode"]},
        "molecule activity captured context",
    )
    same(
        state["coverage"],
        result.wire["coverage"],
        "molecule activity source/request coverage",
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
        "molecule activity labels, typed quantities and original support",
    )


def _anchor(view):
    anchor, seen = view, set()
    while anchor._display_request is not None:
        require(
            id(anchor) not in seen and anchor._origin is not None,
            "Molecule destination has a cyclic or missing display origin.",
        )
        seen.add(id(anchor))
        parent = anchor._origin
        require(
            anchor.result_ref == parent.result_ref
            and anchor._selection.selection_ref == parent._selection.selection_ref,
            "Molecule destination display changed its original selection.",
        )
        anchor = parent
    return anchor


def _state_context(view, record, expected):
    mode = record["state"]["context"].get("mode")
    require(mode in ("live", "saved"), "Unknown molecule display mode.")
    same(view._context_override, expected, "molecule destination original context")
    same(
        record["state"]["context"],
        {**expected, "mode": mode},
        "molecule destination saved context",
    )


def verify_links(view, record=None):
    """Authenticate the complete original source/destination vocabulary."""
    from .card_exploration import CardItem

    require(
        view._link_panel
        and is_context(view)
        and view._context_override.get("activity_context") == "links",
        "Unsupported molecule navigation panel.",
    )
    require(
        not any(
            (
                view._record_panel,
                view._field_panel,
                view._route_catalog,
                view._question_catalog,
                view._focus,
                view._component_navigation,
                view._context_only,
                view._machine_ref,
            )
        ),
        "Foreign molecule link presentation flags.",
    )
    anchor = _anchor(view)
    parent = anchor._origin
    require(
        parent is not None and is_view(parent),
        "Molecule links lost their originating selection.",
    )
    navigation = anchor._context_override["molecule_activity_navigation"]
    key = navigation["source_row_key"]
    matches = [entry for entry in parent._selected if entry.key == key]
    require(len(matches) == 1, "Molecule links lost their exact displayed source row.")
    item = CardItem(parent, matches[0])
    same(navigation, expected_navigation(item), "molecule original navigation history")
    access, result = parent._explorer.access, parent._selection._scientific
    require(
        view._explorer.access._focal_key == access._focal_key,
        "Molecule links changed the focal capture.",
    )
    expected = {
        "rule": LINK_RULE,
        "inputs": access.context["captures"],
        "focal": access._focal_key,
        "source_location": deepcopy(item.payload_location),
        "support_location": result.location("support", key),
        "links": expected_links(item),
    }
    same(
        view.native_payload,
        expected,
        "molecule complete original link destinations and support",
    )
    full = access._resolve(view._selection._target["location"])[1]
    require(
        full["kind"] == "result" and full["result_ref"] in access._metadata_refs,
        "Molecule links lost their literal metadata owner.",
    )
    same(
        access._objects[full["result_ref"]],
        expected,
        "molecule navigation metadata owner",
    )
    entries = tuple(
        _Entry(
            {
                **full,
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
    _literal_selection(view, full, entries=entries)
    _question(view)
    if view._display_request is None:
        same(
            view.outcome,
            {
                "status": "ok" if expected["links"] else "empty",
                "reason": "Exact retained molecule/target pins, identity statements and native activity destinations. Publication context retains its complete target scope; source silence does not establish inactivity or efficacy.",
            },
            "molecule original links outcome",
        )
    if record is not None:
        _state_context(view, record, _context(parent, navigation, "links"))
        require(
            record.get("native_encoding", "json") == "json",
            "Unknown molecule navigation encoding.",
        )
        same(record["native_payload"], expected, "molecule recorded navigation")
        _literal_state(view, record)


def verify_explanation(view, record):
    """Bind complete identity/native support and every original assertion row."""
    from .card_exploration import CardItem

    access, full = view._explorer.access, result_location(view)
    require(
        is_explanation(view)
        and is_context(view)
        and view._context_override.get("activity_context") == "support",
        "Unsupported molecule support presentation.",
    )
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
                view._context_only,
                view._machine_ref,
            )
        ),
        "Foreign molecule support presentation flags.",
    )
    anchor, navigation = (
        _anchor(view),
        view._context_override["molecule_activity_navigation"],
    )
    parent = anchor._origin
    require(
        parent is not None
        and is_view(parent)
        and parent.result_ref == full["result_ref"],
        "Molecule support lost its originating result/back context.",
    )
    key = full["segments"][1]["value"]
    matches = [entry for entry in parent._selected if entry.key == key]
    require(len(matches) == 1, "Molecule support lost its exact displayed source row.")
    same(
        navigation,
        expected_navigation(CardItem(parent, matches[0])),
        "molecule support navigation",
    )
    result = parent._selection._scientific
    same(full, result.location("explanations", key), "molecule support target")
    entries = tuple(
        _Entry(
            statement["location"],
            statement["id"],
            access._resolve(statement["location"])[0],
        )
        for statement in result.wire["support"][key]["source_assertions"]
        if statement["state"] == "present"
    )
    _literal_selection(view, full, entries=entries)
    same(
        record["native_payload"],
        result.wire["explanations"][key],
        "molecule complete original explanation",
    )
    _state_context(view, record, _context(parent, navigation, "support"))
    if view._display_request is None:
        same(
            view.outcome,
            {
                "status": "ok",
                "reason": "Exact retained identity relationships and native activity/assay support; missing references and original source outcomes remain explicit. Citation metadata does not imply article reading or independent evidence.",
            },
            "molecule original support outcome",
        )
    _question(view)
    _literal_state(view, record)


def verify_context(view, record):
    """Bind each visited endpoint to its original row, pins and actual parent."""
    if view._link_panel:
        return verify_links(view, record)
    if is_explanation(view):
        return verify_explanation(view, record)
    access, anchor = view._explorer.access, _anchor(view)
    parent = anchor._origin
    require(
        parent is not None and parent._link_panel and is_context(parent),
        "Molecule endpoint lost its original link/back context.",
    )
    verify_links(parent)
    role = anchor._context_override["activity_context"]
    navigation = parent._context_override["molecule_activity_navigation"]
    same(
        anchor._context_override["molecule_activity_navigation"],
        navigation,
        "molecule endpoint navigation scope",
    )
    choices = [
        link
        for link in parent.native_payload["links"]
        if link["role"] == role
        and (link["label"] == anchor.title or anchor.native_payload == {"link": link})
    ]
    require(len(choices) == 1, "Molecule endpoint has no unique original destination.")
    link = choices[0]
    require(len(link["candidates"]) <= 1, "Unsupported molecule endpoint ambiguity.")
    require(
        not any(
            (
                view._record_panel,
                view._field_panel,
                view._link_panel,
                view._question_catalog,
                view._focus,
                view._component_navigation,
                view._context_only,
            )
        )
        and view._selection._scientific is None
        and view._machine_ref is None,
        "Foreign molecule endpoint presentation flags.",
    )
    expected_context = _context(parent, navigation, role)
    if role == "native_ligand_crossing":
        result = parent._origin._selection._scientific
        native, full = result.native_crossing(navigation["target_card_ref"])
        same(access._resolve(full)[0], native, "molecule retained native crossing leaf")
    elif link["candidates"]:
        candidate = link["candidates"][0]
        if role == "target_card":
            require(
                candidate["capture"] == access._focal_key and view._route_catalog,
                "Explicit protein destination lost its exact capture or route catalog.",
            )
            expected_context = {
                **access.context,
                "mode": "live",
                "adapter": LINK_RULE,
                "activity_context": role,
                "molecule_card_ref": navigation["molecule_card_ref"],
                "target_card_ref": navigation["target_card_ref"],
                "molecule_activity_navigation": deepcopy(navigation),
            }
            native, full = access._resolve(view._selection._target["location"])
            require(
                full["kind"] == "result"
                and full["result_ref"] in access._metadata_refs,
                "Explicit protein route catalog lost its literal owner.",
            )
            same(
                sorted(native),
                sorted(
                    (
                        "annotated_regions",
                        "assembly_generation",
                        "bioactivities",
                        "content",
                        "coverage",
                        "function",
                        "ligand_instances",
                        "ligand_site_comparisons",
                        "literature",
                        "predicted_structures",
                        "quality",
                        "quaternary_interpretation",
                        "quaternary_structure",
                        "sequence",
                        "sites",
                        "sources",
                        "structures",
                    )
                ),
                "original protein destination routes",
            )
        else:
            require(
                candidate["capture"] == parent._explorer.access._focal_key
                or candidate["location"]["kind"] == "card",
                "Molecule endpoint changed its retained candidate capture.",
            )
            require(
                access._focal_key == parent._explorer.access._focal_key
                and not view._route_catalog,
                "Molecule context switched focal capture implicitly.",
            )
            full = candidate["location"]
            native = access._resolve(full)[0]
            if role == "publication_context":
                from .card_bioactivity_history_v2 import expected_publication

                wrapper, full = access._resolve(view._selection._target["location"])
                targets = [
                    key
                    for key, captured in access._captures.items()
                    if captured.pin == navigation["target_card_ref"]
                ]
                require(
                    len(targets) == 1,
                    "Publication context requires an exact original target pin.",
                )
                expected = expected_publication(
                    access._for_capture(targets[0]),
                    native["publication_ref"],
                    original=wrapper,
                )
                same(
                    wrapper,
                    expected,
                    "molecule full original target publication and all citation links",
                )
                native = expected["original_explanation"]
                require(
                    full["kind"] == "result"
                    and full["result_ref"] in access._metadata_refs,
                    "Publication explanation lost its retained literal owner.",
                )
    else:
        require(
            role == "source" and link["availability"] == "missing_prerequisite",
            "Unsupported unavailable molecule endpoint.",
        )
        native = {"link": link}
        _, full = access._resolve(view._selection._target["location"])
        same(
            access._resolve(full)[0],
            native,
            "unavailable original molecule source context",
        )
    if view._display_request is None:
        same(
            view.outcome,
            {
                "status": "missing_prerequisite"
                if not link["candidates"] and role != "native_ligand_crossing"
                else "ok",
                "reason": "The referenced original source statement is unavailable. Its retained identity relationship and missing support remain visible; no replacement or attribution is inferred."
                if not link["candidates"] and role != "native_ligand_crossing"
                else None,
            },
            "molecule original endpoint outcome",
        )
    _literal_selection(view, full)
    same(
        record["native_payload"], native, "molecule complete visited original endpoint"
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown molecule endpoint encoding.",
    )
    _state_context(view, record, expected_context)
    _question(view)
    _literal_state(view, record)


def verification_report(bundle):
    from .card_exploration_literature import verification_report as previous_report

    report = previous_report(bundle)
    report.update(
        verifier=VERIFIER,
        activity_context="original_frozen_v1_consistency_verified",
        recorded_navigation_decisions="Exact molecule/target captures, original source and native membership, complete support, typed quantities, executed display/machine selections and visited original destinations verified. Source authenticity, scientific truth and article reading remain unestablished.",
        verified_navigation_policies=[ROOT_RETURN_EQUALITY],
    )
    if ADAPTER not in report["verified_scientific_adapters"]:
        report["verified_scientific_adapters"].append(ADAPTER)
    return report


def verify_literature_view(view, record):
    """Bind the original intermediate question at an explicit target crossing.

    LIVE answer() first registers a topic view inheriting the incoming question,
    then registers the final view with its own publication question. Only that
    intermediate, exact supplied-Card destination uses this bridge. The original
    @19 literature verifier and ordinary publication questions remain unchanged.
    """
    from .card_exploration_literature import verify_view as previous_view

    request = view.request
    if request is None or request.get("question") != "measured_targets":
        return previous_view(view, record)
    parent, access = view._origin, view._explorer.access
    require(
        parent is not None and parent._link_panel and is_context(parent),
        "Incoming literature question has no original molecule target crossing.",
    )
    verify_links(parent)
    _question(parent)
    same(request, parent.request, "literature original incoming molecule question")
    navigation = parent._context_override["molecule_activity_navigation"]
    require(
        navigation["target_card_ref"] == access._focal.pin
        and access.profile == "protein"
        and any(
            link["role"] == "target_card"
            and any(
                candidate["capture"] == access._focal_key
                for candidate in link["candidates"]
            )
            for link in parent.native_payload["links"]
        ),
        "Incoming publication view lost its explicit exact target destination.",
    )
    return previous_view(replace(view, _request=None), record)
