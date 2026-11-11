"""Independent SDK243 knowledge-comparison human/source/navigation predicates."""

from copy import deepcopy
from dataclasses import replace

from ._knowledge_comparison_history_v1 import exploration as frozen
from ._knowledge_comparison_history_v1.machine import _machine
from ._knowledge_comparison_history_v1.replay import ReplayExplorer
from ._protein_context_history_v1.selection import COLUMNS
from .card_access import _handle
from .card_exploration import CardItem, CardView, Cell
from .card_exploration_protein_context import ADAPTERS as OLDER_ADAPTERS
from .card_knowledge_comparison_history_v1 import (
    ADAPTER,
    options_for_context,
)
from .card_knowledge_comparison_history_v1 import (
    PANEL as TOPIC,
)
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@35"
VERIFIER = "knowledge_comparison_exploration_binding@1"
ADAPTERS = (*OLDER_ADAPTERS, ADAPTER)
SCHEMA = {
    "kind": "protein_context_exploration",
    "grain": "retained relationship or explicit captured comparison",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        "Saved knowledge-comparison " + scope + " differs from its original binding.",
    )


def is_result(result):
    return (
        result is not None and result.wire.get("context", {}).get("adapter") == ADAPTER
    )


def is_view(view):
    return is_result(view._selection._scientific)


def is_context(view):
    if is_view(view):
        return False
    if view._selection._scientific is not None:
        return False
    seen = set()
    parent = view._origin or view._explorer._origin
    while parent is not None and id(parent) not in seen:
        if is_view(parent):
            return True
        seen.add(id(parent))
        if parent._selection._scientific is not None:
            return False
        parent = parent._origin or parent._explorer._origin
    return False


def is_links(view):
    return is_context(view) and view._link_panel


def original_occurrences(selection, record):
    target = selection._target["location"]
    access = selection._access
    _, full = access._resolve(target)
    if full["kind"] != "result" or full["segments"][:1] != [
        {"type": "Key", "value": "explanations"}
    ]:
        return None
    wire = access._objects[full["result_ref"]]
    if not isinstance(wire, dict) or wire.get("context", {}).get("adapter") != ADAPTER:
        return None
    buckets = {}
    for entry in selection._entries:
        ref = _handle(
            "XI_", {"result_ref": selection.result_ref, "location": entry.location}
        )
        buckets.setdefault(ref, []).append(entry)
    consumed, entries = {}, []
    for ref in record["selected"]:
        index = consumed.get(ref, 0)
        require(
            ref in buckets and index < len(buckets[ref]),
            "Protein source occurrence count differs.",
        )
        entries.append(buckets[ref][index])
        consumed[ref] = index + 1
    return tuple(entries)


def _full(access, location):
    return access._resolve(location)[1]


def _selection_state(selection, access):
    return {
        "result_ref": selection.result_ref,
        "selection_ref": selection.selection_ref,
        "entries": [vars(entry) for entry in selection._entries],
        "context_location": _full(access, selection._context_location),
        "context": access._resolve(selection._context_location)[0],
        "target": {
            **selection._target,
            "location": _full(access, selection._target["location"]),
        },
        "operation": selection._operation,
        "slice": selection._slice,
        "fields": list(selection._fields),
        "outcome_override": selection._outcome_override,
        "scientific_result_ref": selection._scientific.result_ref
        if selection._scientific
        else None,
    }


def _state(view):
    """Bind declared knowledge-comparison cells and original literal source/quantity cells."""
    from .card_exploration_storage import _cell_record

    items = {}
    for entry in view._selection._entries:
        item = CardItem(view, entry)
        if is_view(view):
            result = view._selection._scientific
            support = [deepcopy(result.wire["support"][entry.key])]
            cells = {
                column: Cell(
                    deepcopy(result.value(entry.key, column)),
                    state=result.cell_state(entry.key, column),
                    reason=result.cell_reason(entry.key, column),
                    _support=tuple(support),
                )
                for column in COLUMNS
            }
        else:
            support, cells = item.support, item.cells
        items[item.item_ref] = {
            "label": item.label,
            "kind": item.kind,
            "support": support,
            "cells": {
                column: _cell_record(item, column, cell)
                for column, cell in cells.items()
            },
        }
    return {
        "items": items,
        "context": view.context,
        "schema": SCHEMA if is_view(view) else view.schema,
        "coverage": view.coverage,
    }


def _compare(view, expected, record, replay):
    from .card_exploration_storage import _FLAGS

    require(
        view._component_navigation is None,
        "Knowledge-comparison view has a foreign structural operation.",
    )
    same(
        view._explorer.access._focal_key,
        expected._explorer.access._focal_key,
        "exact destination focal capture",
    )
    same(
        {key: getattr(view, key) for key in _FLAGS},
        {key: getattr(expected, key) for key in _FLAGS},
        "presentation flags, request and outcome",
    )
    same(
        _selection_state(view._selection, view._explorer.access),
        _selection_state(expected._selection, expected._explorer.access),
        "literal/scientific request and original entry membership",
    )
    same(
        [vars(entry) for entry in view._selected],
        [vars(entry) for entry in expected._selected],
        "display membership/order",
    )
    same(
        record["native_payload"],
        expected.native_payload,
        "complete original native payload",
    )
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown knowledge-comparison native encoding.",
    )
    expected_state = _state(expected)
    mode = record["state"]["context"].get("mode")
    require(
        mode in ("live", "saved"), "Unknown knowledge-comparison saved context mode."
    )
    expected_state["context"] = {**expected_state["context"], "mode": mode}
    same(
        record["state"],
        expected_state,
        "full typed cells, source support, schema and request coverage",
    )


def _scope(view):
    if is_view(view) and view.request is not None:
        same(
            view.request,
            {
                "question": "knowledge_differences",
                "topic": "comparative_context",
                "options": view._selection._scientific.options,
            },
            "original knowledge-comparison question",
        )
    if (
        not is_view(view)
        and view._origin is not None
        and (is_view(view._origin) or is_context(view._origin))
    ):
        same(view.request, view._origin.request, "inherited question")


def verify_view(view, record):
    """Verify original row, display and literal source operations independently."""
    from ._knowledge_comparison_history_v1 import navigation

    _scope(view)
    replay = ReplayExplorer(view._explorer)
    parent = replay.shadow(view._origin) if view._origin is not None else None
    request_mode = view._explorer.access._resolve(view._selection._context_location)[0][
        "context"
    ]["mode"]
    require(request_mode in ("live", "saved"), "Unknown original request mode.")
    replay.access._mode = request_mode
    operation = view._display_request
    if not is_view(view) and operation is not None:
        verify_literal_view(view, record)
        return
    if is_view(view):
        if operation is not None:
            require(
                parent is not None and is_view(parent),
                "Protein display lost its original parent.",
            )
            if operation.get("operation") == "filter":
                expected = frozen.display_filter(
                    parent, operation["column"], operation["equals"]
                )
            elif operation.get("operation") == "sort":
                expected = frozen.display_sort(
                    parent,
                    operation["column"],
                    operation["descending"],
                    operation["unit"],
                )
            else:
                same(operation, {"operation": "presentation"}, "display operation")
                expected = replace(
                    parent,
                    _origin=parent,
                    presentation=view.presentation,
                    _display_request=operation,
                )
        elif view._selection._operation.startswith("select:"):
            result = view._selection._scientific
            expected = CardView(
                replay,
                view._selection,
                _machine(view._selection, view._explorer.access, result),
                "Saved machine selection",
                parent,
                _record_panel=TOPIC,
                _machine_ref=view._selection.selection_ref,
                _native_override=result.native,
                _context_override=result.wire["context"],
                _status=result.wire["outcome"]["status"],
                _reason=result.wire["outcome"]["reason"],
            )
        else:
            result = view._selection._scientific
            expected = replace(
                frozen.view(replay, parent, result.options),
                _request=view.request,
            )
    else:
        require(
            parent is not None and is_context(view),
            "Protein context has no originating operation.",
        )
        target = _full(view._explorer.access, view._selection._target["location"])
        if (
            target["kind"] == "result"
            and target["result_ref"] in replay.access._metadata_refs
            and not (
                isinstance(view.native_payload, dict)
                and view.native_payload.get("rule") == "knowledge_comparison_links@1"
                and "links" in view.native_payload
            )
        ):
            # The existing literal predicate binds exact metadata identity, input
            # support and navigation. Source-owned lookalikes never enter here:
            # membership in the metadata registry, not value shape, owns dispatch.
            verify_literal_view(view, record)
            return
        if is_view(parent):
            result = parent._selection._scientific
            native = view.native_payload
            if (
                isinstance(native, dict)
                and native.get("rule") == "knowledge_comparison_links@1"
            ):
                matches = [
                    entry
                    for entry in parent._selection._entries
                    if canonical_json(native.get("support_location"))
                    == canonical_json(result.location("support", entry.key))
                ]
                require(
                    len(matches) == 1,
                    "Protein links lost their exact original row occurrence.",
                )
                expected = frozen.links(CardItem(parent, matches[0]))
            else:
                matches = [
                    (entry, kind)
                    for entry in parent._selection._entries
                    for kind, location in [
                        ("open", result.location("rows", entry.key, "item")),
                        ("explanations", result.location("explanations", entry.key)),
                    ]
                    if canonical_json(target) == canonical_json(location)
                ]
                require(
                    len(matches) == 1,
                    "Protein detail is not an exact original row occurrence.",
                )
                entry, kind = matches[0]
                expected = (
                    frozen.open_item(CardItem(parent, entry))
                    if kind == "open"
                    else frozen.explain(CardItem(parent, entry))
                )
        elif parent._link_panel:
            link = next(
                (
                    entry
                    for entry in parent._selected
                    if entry.value.get("candidates")
                    and len(entry.value["candidates"]) == 1
                    and canonical_json(entry.value["candidates"][0]["location"])
                    == canonical_json(target)
                ),
                None,
            )
            if link is None:
                native = view.native_payload
                require(
                    isinstance(native, dict) and isinstance(native.get("link"), dict),
                    "Protein context lost the clicked original link.",
                )
                candidates = [
                    entry
                    for entry in parent._selected
                    if canonical_json(entry.value) == canonical_json(native["link"])
                ]
                require(
                    len(candidates) == 1,
                    "Protein link context is foreign or ambiguous.",
                )
                link = candidates[0]
            expected = navigation.follow(CardItem(parent, link))
        else:
            matches = [
                entry
                for entry in parent._selection._entries
                if canonical_json(entry.location) == canonical_json(target)
            ]
            if not matches:
                require(
                    target["kind"] == "result"
                    and target["result_ref"] in replay.access._metadata_refs,
                    "Protein source detail is not an original child or declared literal metadata.",
                )
                verify_literal_view(view, record)
                return
            require(
                bool(matches)
                and all(
                    canonical_json(vars(entry)) == canonical_json(vars(matches[0]))
                    for entry in matches
                ),
                "Protein source detail is not an original child.",
            )
            item = CardItem(parent, matches[0])
            expected = replace(
                replay._inspect(target, parent, title=item.label),
                _request=parent.request,
                _display_request=None,
                _context_only=parent._context_only,
                _context_override=parent._context_override,
            )
    _compare(view, expected, record, replay)


def descriptor(topic="comparative_context"):
    from .card_knowledge_comparison_history_v1 import descriptor as original_descriptor

    return original_descriptor(topic)


def verify_literal_view(view, record):
    """Use frozen literal/catalog predicates for the actual auxiliary nodes."""
    from .card_exploration_verification_v35 import (
        _verify_profile,
        _verify_request,
        _verify_state,
    )

    require(
        not is_view(view),
        "A rich knowledge-comparison view cannot enter the literal inspection predicate.",
    )
    replay = ReplayExplorer(view._explorer)
    mode = view._explorer.access._resolve(view._selection._context_location)[0][
        "context"
    ]["mode"]
    require(mode in ("live", "saved"), "Unknown original literal request mode.")
    replay.access._mode = mode
    shadow = replay.shadow(view)
    _verify_request(shadow, replay.access)
    _verify_profile(shadow, record["native_payload"], replay.access)
    _verify_state(shadow, record, record["native_payload"], replay.access)


def register_bundle(
    bundle, objects, access, *, session_format=None, preserve_access_origins=False
):
    retained = {
        ref: wire
        for ref, wire in objects.items()
        if ref not in access._metadata_refs
        and isinstance(wire, dict)
        and wire.get("context", {}).get("adapter") == ADAPTER
        and "native_payload" in wire
    }
    catalog = has_observed_catalog(bundle)
    current_topics = session_format in (
        None,
        FORMAT,
    ) and has_observed_topics(bundle)
    # The existing @35 verifier binds actual accesses as well as earlier native
    # scientific predicates. A newly retained finite request needs those bindings;
    # a verified @35 resave must keep them even without a question/menu witness.
    current_origins = session_format == FORMAT or (
        session_format is None and preserve_access_origins
    )
    if (
        not retained
        and not catalog
        and not current_topics
        and not current_origins
        and not has_sequence_context_display(bundle)
    ):
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
    for member in (
        "scientific_results",
        "molecule_activity_crossings",
        "molecule_activity_operations",
        "molecule_activity_root_returns",
    ):
        bundle.setdefault(member, {})


def machine_request_witness(bundle):
    """Find an owned scientific request, never a marker in source-owned JSON."""
    for key, record in bundle["views"].items():
        flags = record["flags"]
        if flags.get("_machine_ref") is None:
            continue
        selection = record["selection"]
        ref = selection.get("scientific_result_ref")
        wire = bundle["objects"].get(ref, {})
        if (
            flags["_machine_ref"] == selection.get("selection_ref")
            and selection.get("operation", "").startswith("select:")
            and ref in bundle.get("scientific_results", {})
            and isinstance(wire, dict)
            and "native_payload" in wire
            and wire.get("context", {}).get("adapter") in ADAPTERS
        ):
            return key
    return None


def frozen_catalog():
    from ._knowledge_comparison_history_v1.catalogs import QUESTIONS

    return QUESTIONS["protein"]


def frozen_protein_topics():
    from ._knowledge_comparison_history_v1.catalogs import TOPICS

    return {key: {"description": value[1]} for key, value in TOPICS["protein"].items()}


def has_observed_topics(bundle):
    """Recognize an actual owned protein route catalog, never source-owned lookalikes."""
    expected = frozen_protein_topics()
    for record in bundle["views"].values():
        if not record["flags"].get("_route_catalog", False):
            continue
        capture = bundle["cards"].get(record.get("focal"), {})
        if capture.get("data", {}).get("meta", {}).get("entity_type") != "protein":
            continue
        target = record["selection"]["target"]["location"]
        if target.get("kind") == "lookup":
            target = bundle["locations"].get(target["location_ref"], {})
        value = bundle["objects"].get(target.get("result_ref"))
        if (
            target.get("kind") == "result"
            and not target.get("segments")
            and value == expected
            and target["result_ref"]
            == _handle("XR_", {"adapter": "literal_metadata@1", "value": value})
        ):
            return True
    return False


def verify_molecule_context(view, record):
    """Bind the current complete target catalog while retaining original molecule science."""
    from . import card_exploration_molecule_activity as molecule

    if (
        not view._route_catalog
        or (view._context_override or {}).get("activity_context") != "target_card"
        or view.native_payload != frozen_protein_topics()
    ):
        return molecule.verify_context(view, record)
    anchor = molecule._anchor(view)
    parent, access = anchor._origin, view._explorer.access
    require(
        parent is not None and parent._link_panel and molecule.is_context(parent),
        "Current protein catalog lost its original molecule link.",
    )
    molecule.verify_links(parent)
    navigation = parent._context_override["molecule_activity_navigation"]
    same(
        anchor._context_override["molecule_activity_navigation"],
        navigation,
        "current target catalog incoming navigation",
    )
    link = molecule._endpoint_entries(anchor, parent, "target_card")[0].value
    require(
        len(link["candidates"]) == 1
        and link["candidates"][0]["capture"] == access._focal_key,
        "Current protein catalog changed its explicit target capture.",
    )
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
        "Current protein catalog has foreign scientific/presentation flags.",
    )
    native, full = access._resolve(view._selection._target["location"])
    require(
        full["kind"] == "result"
        and not full["segments"]
        and full["result_ref"] in access._metadata_refs,
        "Current protein catalog lost its complete literal metadata owner.",
    )
    same(native, frozen_protein_topics(), "complete frozen current target catalog")
    same(record["native_payload"], native, "current target catalog native payload")
    require(
        record.get("native_encoding", "json") == "json",
        "Unknown current target catalog encoding.",
    )
    molecule._literal_selection(view, full)
    molecule._state_context(
        view,
        record,
        {
            **access.context,
            "mode": "live",
            "adapter": molecule.LINK_RULE,
            "activity_context": "target_card",
            "molecule_card_ref": navigation["molecule_card_ref"],
            "target_card_ref": navigation["target_card_ref"],
            "molecule_activity_navigation": deepcopy(navigation),
        },
    )
    if view._display_request is None:
        same(
            view.outcome,
            {"status": "ok", "reason": None},
            "current target catalog outcome",
        )
    molecule._question(view)
    molecule._literal_state(view, record)
    from .card_exploration_verification import _verify_display

    _verify_display(view, record)


def has_sequence_context_display(bundle):
    """Choose current receiving for actual display operations below a sequence result."""
    return bool(sequence_context_display_ancestry(bundle))


def sequence_context_display_ancestry(bundle):
    """Retain one actual ancestry as the bounded shared-header admission witness."""
    for key, record in bundle["views"].items():
        if (
            record["flags"].get("_display_request") is None
            or record["selection"].get("scientific_result_ref") is not None
        ):
            continue
        parent = record.get("origin") or record.get("explorer_origin")
        seen = set()
        path = [key]
        while parent is not None and parent not in seen:
            seen.add(parent)
            path.append(parent)
            original = bundle["views"][parent]
            result = original["selection"].get("scientific_result_ref")
            if result is not None:
                if (
                    bundle["objects"][result]["context"]["adapter"]
                    == "sequence_change_exploration@1"
                ):
                    return path
                break
            parent = original.get("origin") or original.get("explorer_origin")
    return []


def has_observed_catalog(bundle):
    """Only an actual question-catalog operation admits its new frozen meanings."""
    for record in bundle["views"].values():
        if not record["flags"].get("_question_catalog", False):
            continue
        target = record["selection"]["target"]["location"]
        if target.get("kind") == "lookup":
            target = bundle["locations"].get(target["location_ref"], {})
        ref = target.get("result_ref")
        value = bundle["objects"].get(ref)
        if (
            target.get("kind") == "result"
            and not target.get("segments")
            and value == frozen_catalog()
            and ref == _handle("XR_", {"adapter": "literal_metadata@1", "value": value})
        ):
            return True
    return False


def verify_objects(bundle, accesses):
    from .card_exploration_protein_context import verify_objects as older_objects
    from .card_knowledge_comparison_history_v1 import verify_result

    older = {}
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Knowledge-comparison result lost its original focal manifest.",
        )
        verify_result(accesses[record["focal"]], ref, wire)
    older_objects({**bundle, "scientific_results": older}, accesses)


def _publish(expected, explorer, origin):
    """Expose only frozen literal navigation metadata over the retained original."""
    source = expected._explorer.access
    if expected._explorer._origin is expected._origin and expected._origin is not None:
        from .card_exploration_storage import _explorer

        explorer = _explorer(
            explorer.access._for_capture(source._focal_key), explorer._session
        )
        explorer._origin = origin
    destination = explorer.access
    for ref, value in source._objects.items():
        if ref not in destination._objects:
            require(
                ref
                == _handle("XR_", {"adapter": "literal_metadata@1", "value": value}),
                "Knowledge-comparison navigation attempted to create a scientific result.",
            )
            destination._objects[ref] = value
            destination._metadata_refs.add(ref)
    destination._locations.update(source._locations)
    selection = replace(expected._selection, _access=destination)
    destination._selections.setdefault(selection.selection_ref, selection)
    return replace(expected, _explorer=explorer, _selection=selection, _origin=origin)


def item_operation(item, operation):
    """Read original knowledge-comparison data without executing current science or digesters."""
    explorer = item._view._explorer
    replay = ReplayExplorer(explorer)
    parent = replay.shadow(item._view)
    original = CardItem(parent, item._entry)
    if parent._link_panel and item._entry.value.get("role") == "question":
        request = item._entry.value.get("comparison_request")
        if isinstance(request, dict):
            return explorer._answer(request["question"], request["options"], item._view)
    from ._knowledge_comparison_history_v1 import navigation

    expected = (
        navigation.follow(original)
        if parent._link_panel
        else frozen.open_item(original)
        if operation == "open"
        else frozen.explain(original)
        if operation == "explanations"
        else navigation.related(original)
    )
    origin = item._view
    return _publish(expected, explorer, origin)


def open_retained_child(item):
    require(
        is_context(item._view)
        and any(
            canonical_json(vars(entry)) == canonical_json(vars(item._entry))
            for entry in item._view._selected
        ),
        "Protein literal child is outside its originating display.",
    )
    replay = ReplayExplorer(item._view._explorer)
    parent = replay.shadow(item._view)
    expected = replace(
        replay._inspect(item._entry.location, parent, title=item.label),
        _request=parent.request,
        _context_only=parent._context_only,
        _context_override=parent._context_override,
    )
    return _publish(expected, item._view._explorer, item._view)


def prepare(root):
    """Retain machine requests and source closure; acquire no new knowledge."""
    session = root._explorer._session
    accesses = {
        id(view._explorer.access): view._explorer.access
        for view in session["views"].values()
    }
    accesses[id(root._explorer.access)] = root._explorer.access
    existing = {view._machine_ref for view in session["views"].values()}
    from .card_exploration_storage import _explorer, operation_key

    for access in accesses.values():
        for selection in list(access._selections.values()):
            if (
                not is_result(selection._scientific)
                or selection.selection_ref in existing
            ):
                continue
            result = selection._scientific
            CardView(
                _explorer(access, session),
                selection,
                selection._entries,
                "Saved machine selection",
                _record_panel=TOPIC,
                _machine_ref=selection.selection_ref,
                _native_override=result.native,
                _context_override=result.wire["context"],
                _status=result.wire["outcome"]["status"],
                _reason=result.wire["outcome"]["reason"],
            )
            existing.add(selection.selection_ref)
    for view in list(session["views"].values()):
        if not is_view(view):
            continue
        for entry in view._selection._entries:
            item = CardItem(view, entry)
            key = operation_key(item)
            for operation in ("explanations", "links"):
                if key not in session[operation]:
                    session[operation][key] = item_operation(item, operation)


def saved_selection(access, topic, fields, options, where, item_refs, order_by):
    from ._protein_context_history_v1.selection import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )
    from .card_exploration_storage import missing_selection

    options, fields = options_for_context(topic, options), projection(fields)
    query = normalize(where, item_refs, order_by)
    for selected in access._selections.values():
        if (
            not is_result(selected._scientific)
            or selected._operation != "select:" + topic
        ):
            continue
        result = selected._scientific
        if topic != "comparative_context" or canonical_json(
            result.options
        ) != canonical_json(options):
            continue
        entries, spec = (
            evaluate(result, query) if active(query) else (result.entries, None)
        )
        ref = (
            selection_ref(result, fields, spec)
            if spec is not None
            else _handle(
                "XA_",
                {
                    "format": "scientific_access_selection@1",
                    "result_ref": result.result_ref,
                    "fields": fields,
                },
            )
        )
        if ref == selected.selection_ref:
            return selected
    return missing_selection(
        access, topic, options, fields, query if active(query) else None
    )


def saved_topic(explorer, topic, origin, options=None, *, question=None):
    from .card_exploration_storage import not_saved

    options = options_for_context(topic, options)
    request = (
        {"question": question, "topic": topic, "options": options}
        if question is not None
        else None
    )
    for view in explorer._session["views"].values():
        if (
            is_view(view)
            and view._saved_state is not None
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view._machine_ref is None
            and view._selection._operation == "read"
            and topic == "comparative_context"
            and canonical_json(view._selection._scientific.options)
            == canonical_json(options)
            and canonical_json(view.request) == canonical_json(request)
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
            )
    return not_saved(
        explorer,
        "This original knowledge-comparison topic/question was not retained.",
        origin,
    )


def display_filter(view, column, equals):
    return frozen.display_filter(view, column, equals)


def display_sort(view, column, descending=False, unit=None):
    return frozen.display_sort(view, column, descending, unit)


def validate_filters(bundle):
    from .card_exploration_protein_context import validate_filters as older_filters

    return older_filters(bundle)


def verification_report(bundle):
    from .card_exploration_protein_context import verification_report as older_report

    report = older_report(bundle)
    if "protein_context_exploration@1" not in report["verified_scientific_adapters"]:
        report.pop("protein_context", None)
        report["verified_scientific_rules"] = [
            rule
            for rule in report["verified_scientific_rules"]
            if rule
            not in (
                "protein_context_exploration@1",
                "protein_context_projection@1",
                "captured_sequence_comparison@1",
                "equal_length_positions@1",
                "protein_context_support@1",
            )
        ]
    report["verified_navigation_policies"] = [
        rule
        for rule in report.get("verified_navigation_policies", [])
        if rule != "protein_context_access_origins@1"
    ]
    report.update(
        verifier=VERIFIER,
        knowledge_comparison="original_frozen_v1_consistency_verified",
        bindings="exact typed captured inputs, supplied map, every original source/alternative/conflict/candidate occurrence and actual source access",
    )
    if ADAPTER in report["verified_scientific_adapters"]:
        report["verified_scientific_rules"] = sorted(
            set(report["verified_scientific_rules"])
            | {
                ADAPTER,
                "card_knowledge_diff@2",
                "knowledge_state@5",
                "protein_knowledge_projection@1",
            }
        )
        report["verified_navigation_policies"] = sorted(
            set(report["verified_navigation_policies"])
            | {"knowledge_comparison_links@1"}
        )
    report["verified_navigation_policies"] = sorted(
        set(report["verified_navigation_policies"])
        | {"knowledge_comparison_access_origins@1"}
    )
    return report


def verify_links(view):
    """Bind displayed link tables to the exact frozen source-row metadata."""
    from ._knowledge_comparison_history_v1.replay import ReplayExplorer

    parent = view._origin
    seen = set()
    while parent is not None and parent._link_panel:
        require(id(parent) not in seen, "Protein link display is cyclic.")
        seen.add(id(parent))
        same(
            view.native_payload, parent.native_payload, "original link display payload"
        )
        parent = parent._origin
    require(
        parent is not None and is_view(parent),
        "Protein links lost their exact scientific row parent.",
    )
    result = parent._selection._scientific
    matches = [
        entry
        for entry in parent._selection._entries
        if canonical_json(view.native_payload.get("support_location"))
        == canonical_json(result.location("support", entry.key))
    ]
    require(len(matches) == 1, "Protein link display has a foreign original row.")
    replay = ReplayExplorer(parent._explorer)
    expected = frozen.links(CardItem(replay.shadow(parent), matches[0]))
    same(
        view.native_payload,
        expected.native_payload,
        "complete original link declarations",
    )
    same(
        _selection_state(view._selection, view._explorer.access),
        _selection_state(expected._selection, expected._explorer.access),
        "underlying original link selection",
    )


def bioactivity_bridge(view):
    """Verify the original catalog crossing before using older bioactivity predicates."""
    from copy import copy

    from . import card_exploration_bioactivity_v2 as bioactivity

    request = view.request
    if (
        not isinstance(request, dict)
        or request.get("question") != "knowledge_differences"
    ):
        from .card_exploration_protein_context import bioactivity_bridge as older_bridge

        return older_bridge(view)
    chain, current, seen = [], view, set()
    while current is not None and (
        bioactivity.is_view(current)
        or bioactivity.is_context(current)
        or bioactivity.is_explanation(current)
        or current._link_panel
        and current.native_payload.get("rule") == bioactivity.LINK_RULE
    ):
        require(
            id(current) not in seen, "Incoming protein/bioactivity history is cyclic."
        )
        seen.add(id(current))
        same(current.request, request, "incoming knowledge question continuity")
        require(
            current._explorer.access._focal_key == view._explorer.access._focal_key,
            "Incoming protein/bioactivity history changed capture.",
        )
        chain.append(current)
        current = current._origin
    require(
        chain and bioactivity.is_view(chain[-1]),
        "Incoming bioactivity support has no original scientific view.",
    )
    require(
        current is not None
        and current._route_catalog
        and is_context(current)
        and current._explorer.access._focal_key == view._explorer.access._focal_key
        and canonical_json(current.request) == canonical_json(request)
        and any(entry.key == "bioactivities" for entry in current._selected),
        "Incoming bioactivity view lost its exact original knowledge catalog crossing.",
    )
    parent = current
    for original in reversed(chain):
        clone = copy(original)
        object.__setattr__(clone, "_request", None)
        object.__setattr__(clone, "_origin", parent)
        parent = clone
    return parent


def saved_older_topic(explorer, topic, origin, options=None, *, question=None):
    from .card_exploration_protein_context import is_result as older_result
    from .card_exploration_storage import not_saved
    from .card_protein_context_history_v1 import options_for_context

    options = options_for_context(topic, options)
    request = (
        {"question": question, "topic": topic, "options": options}
        if question is not None
        else None
    )
    for view in explorer._session["views"].values():
        if (
            older_result(view._selection._scientific)
            and view._saved_state is not None
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view._machine_ref is None
            and view._selection._operation == "read"
            and view._selection._scientific.wire["context"]["topic"] == topic
            and canonical_json(view._selection._scientific.options)
            == canonical_json(options)
            and canonical_json(view.request) == canonical_json(request)
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
            )
    return not_saved(
        explorer,
        "This original protein-context topic/question was not retained.",
        origin,
    )
