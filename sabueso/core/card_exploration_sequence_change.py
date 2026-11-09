"""Independent SDK234 sequence-change human/source/navigation predicates."""

from copy import deepcopy
from dataclasses import replace

from ._sequence_change_history_v1 import exploration as frozen
from ._sequence_change_history_v1.machine import _machine
from ._sequence_change_history_v1.replay import ReplayExplorer
from ._sequence_change_history_v1.selection import COLUMNS
from .card_access import _handle
from .card_exploration import CardItem, CardView, Cell
from .card_exploration_variant import ADAPTERS as OLDER_ADAPTERS
from .card_sequence_change_history_v1 import ADAPTER, TOPIC, options_for_changes
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@31"
VERIFIER = "sequence_change_exploration_binding@1"
ADAPTERS = (*OLDER_ADAPTERS, ADAPTER)
SCHEMA = {
    "kind": "sequence_change_exploration",
    "grain": "one original natural-variant or mutagenesis occurrence",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        "Saved sequence-change " + scope + " differs from its original binding.",
    )


def is_result(result):
    return (
        result is not None and result.wire.get("context", {}).get("adapter") == ADAPTER
    )


def is_view(view):
    return view._record_panel == TOPIC or is_result(view._selection._scientific)


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
            "Sequence source occurrence count differs.",
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
    """Bind declared sequence-change cells and original literal source/quantity cells."""
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
        "Sequence-change view has a foreign structural operation.",
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
        "Unknown sequence-change native encoding.",
    )
    expected_state = _state(expected)
    mode = record["state"]["context"].get("mode")
    require(mode in ("live", "saved"), "Unknown sequence-change saved context mode.")
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
            {"question": TOPIC, "topic": TOPIC, "options": {}},
            "original sequence question",
        )
    if view.request is not None and view.request.get("question") == "sequence_changes":
        same(
            view.request,
            {"question": TOPIC, "topic": TOPIC, "options": {}},
            "original sequence question",
        )
    if view._origin is not None and (is_view(view._origin) or is_context(view._origin)):
        same(view.request, view._origin.request, "inherited question")


def verify_view(view, record):
    """Verify original row, display and literal source operations independently."""
    from ._sequence_change_history_v1 import navigation

    _scope(view)
    replay = ReplayExplorer(view._explorer)
    parent = replay.shadow(view._origin) if view._origin is not None else None
    request_mode = view._explorer.access._resolve(view._selection._context_location)[0][
        "context"
    ]["mode"]
    require(request_mode in ("live", "saved"), "Unknown original request mode.")
    replay.access._mode = request_mode
    operation = view._display_request
    if is_view(view):
        if operation is not None:
            require(
                parent is not None and is_view(parent),
                "Sequence display lost its original parent.",
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
        elif view._selection._operation == "select:" + TOPIC:
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
            expected = replace(frozen.view(replay, parent, {}), _request=view.request)
    else:
        require(
            parent is not None and is_context(view),
            "Sequence context has no originating operation.",
        )
        target = _full(view._explorer.access, view._selection._target["location"])
        if (
            target["kind"] == "result"
            and target["result_ref"] in replay.access._metadata_refs
            and not (
                isinstance(view.native_payload, dict)
                and view.native_payload.get("rule") == "retained_context_links@3"
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
            matches = [
                (entry, kind)
                for entry in parent._selection._entries
                for kind, location in [
                    ("open", entry.value["original_location"]),
                    ("explanations", result.location("explanations", entry.key)),
                ]
                if canonical_json(target) == canonical_json(location)
            ]
            require(
                len(matches) == 1,
                "Sequence detail is not an exact original occurrence.",
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
                    "Sequence context lost the clicked original link.",
                )
                candidates = [
                    entry
                    for entry in parent._selected
                    if canonical_json(entry.value) == canonical_json(native["link"])
                ]
                require(
                    len(candidates) == 1,
                    "Sequence link context is foreign or ambiguous.",
                )
                link = candidates[0]
            expected = navigation.follow(CardItem(parent, link))
        elif (
            isinstance(view.native_payload, dict)
            and view.native_payload.get("rule") == "retained_context_links@3"
        ):
            origin = parent._origin
            require(
                origin is not None and is_view(origin),
                "Sequence links lost their original row parent.",
            )
            row_parent = replay.shadow(origin)
            result = row_parent._selection._scientific
            matches = [
                entry
                for entry in row_parent._selection._entries
                if canonical_json(entry.value["original_location"])
                == canonical_json(view.native_payload["source_location"])
            ]
            require(
                len(matches) == 1, "Sequence links refer to a different occurrence."
            )
            expected = navigation.related(CardItem(row_parent, matches[0]))
            if not view._link_panel:
                candidates = [
                    node
                    for node in replay._session["views"].values()
                    if not node._link_panel
                    and canonical_json(node.native_payload)
                    == canonical_json(expected.native_payload)
                ]
                require(
                    len(candidates) == 1, "Sequence link metadata origin is ambiguous."
                )
                expected = candidates[0]
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
                    "Sequence source detail is not an original child or declared literal metadata.",
                )
                verify_literal_view(view, record)
                return
            require(
                bool(matches)
                and all(
                    canonical_json(vars(entry)) == canonical_json(vars(matches[0]))
                    for entry in matches
                ),
                "Sequence source detail is not an original child.",
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


def descriptor():
    from .card_sequence_change_history_v1 import descriptor as original_descriptor

    return original_descriptor()


def verify_literal_view(view, record):
    """Use frozen literal/catalog predicates for the actual auxiliary nodes."""
    from .card_exploration_verification_v31 import (
        _verify_profile,
        _verify_request,
        _verify_state,
    )

    require(
        not is_view(view),
        "A rich sequence-change view cannot enter the literal inspection predicate.",
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


def register_bundle(bundle, objects, access):
    from .card_exploration_variant import ADAPTERS as older_adapters

    retained = {
        ref: wire
        for ref, wire in objects.items()
        if ref not in access._metadata_refs
        and isinstance(wire, dict)
        and wire.get("context", {}).get("adapter") == ADAPTER
        and "native_payload" in wire
    }
    if not retained:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = [*older_adapters, ADAPTER]
    for ref, wire in retained.items():
        focal = next(
            key
            for key, capture in access._captures.items()
            if capture.pin == wire["context"]["card_ref"]
            and capture.snapshot == wire["context"]["snapshot_id"]
        )
        bundle.setdefault("scientific_results", {})[ref] = {"focal": focal}
    bundle.setdefault("molecule_activity_crossings", {})


def verify_objects(bundle, accesses):
    from .card_exploration_variant import verify_objects as older_objects
    from .card_sequence_change_history_v1 import verify_result

    older = {}
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Sequence-change result lost its original focal manifest.",
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
                "Sequence-change navigation attempted to create a scientific result.",
            )
            destination._objects[ref] = value
            destination._metadata_refs.add(ref)
    destination._locations.update(source._locations)
    selection = replace(expected._selection, _access=destination)
    destination._selections.setdefault(selection.selection_ref, selection)
    return replace(expected, _explorer=explorer, _selection=selection, _origin=origin)


def item_operation(item, operation):
    """Read original sequence-change data without executing current science or digesters."""
    explorer = item._view._explorer
    replay = ReplayExplorer(explorer)
    parent = replay.shadow(item._view)
    original = CardItem(parent, item._entry)
    if parent._link_panel and item._entry.value.get("role") == "question":
        basis = item._entry.value.get("annotation_context")
        if isinstance(basis, dict) and basis.get("state") == "ready":
            request = basis["request"]
            return explorer._answer(request["question"], request["options"], item._view)
    from ._sequence_change_history_v1 import navigation

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
    if operation == "links" and is_view(parent):
        # The original related() creates an explicit annotation detail first.
        # Preserve that actual extra back step for newly exposed operations too.
        origin = _publish(expected._origin, explorer, origin)
    return _publish(expected, explorer, origin)


def open_retained_child(item):
    require(
        is_context(item._view)
        and any(
            canonical_json(vars(entry)) == canonical_json(vars(item._entry))
            for entry in item._view._selected
        ),
        "Sequence literal child is outside its originating display.",
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


def saved_selection(access, fields, options, where, item_refs, order_by):
    from ._sequence_change_history_v1.selection import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )
    from .card_exploration_storage import missing_selection
    from .card_sequence_change_history_v1 import options_for_changes

    options, fields = options_for_changes(options), projection(fields)
    query = normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if (
            not is_result(selection._scientific)
            or selection._operation != "select:" + TOPIC
        ):
            continue
        result = selection._scientific
        if canonical_json(result.options) != canonical_json(options):
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
        if ref == selection.selection_ref:
            return selection
    return missing_selection(
        access, TOPIC, options, fields, query if active(query) else None
    )


def saved_topic(explorer, origin, options=None, *, question=False):
    from .card_exploration_storage import not_saved

    options = options_for_changes(options)
    request = (
        {
            "question": "sequence_changes",
            "topic": TOPIC,
            "options": options,
        }
        if question
        else None
    )
    for view in explorer._session["views"].values():
        if (
            is_view(view)
            and view._record_panel == TOPIC
            and view._saved_state is not None
            and view._explorer.access._focal_key == explorer.access._focal_key
            and view._display_request is None
            and view._machine_ref is None
            and view._selection._operation == "read"
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
        "This original sequence-change topic/question was not retained.",
        origin,
    )


def display_filter(view, column, equals):
    return frozen.display_filter(view, column, equals)


def display_sort(view, column, descending=False, unit=None):
    return frozen.display_sort(view, column, descending, unit)


def validate_filters(bundle):
    from .card_exploration_variant import validate_filters as older_filters

    return older_filters(
        {
            **bundle,
            "views": {
                key: record
                for key, record in bundle["views"].items()
                if record["flags"]["_record_panel"] != TOPIC
            },
        }
    )


def verification_report(bundle):
    from .card_exploration_variant import verification_report as older_report

    report = older_report(bundle)
    if (
        "variant_tissue_context_exploration@1"
        not in report["verified_scientific_adapters"]
    ):
        report.pop("variants", None)
        report["verified_scientific_rules"] = [
            rule
            for rule in report["verified_scientific_rules"]
            if rule
            not in (
                "variant_tissue_context_exploration@1",
                "variant_tissue_context_support@1",
                "pext_at_variant@2",
                "isoform_exon_usage@3",
            )
        ]
        report["verified_navigation_policies"] = [
            rule
            for rule in report["verified_navigation_policies"]
            if rule != "variant_context_links@1"
        ]
    report.update(
        verifier=VERIFIER,
        sequence_changes="original_frozen_v1_consistency_verified",
        bindings="original captured snapshots, retained annotation occurrences, exact source membership, typed substitutions and actual human/machine origins",
    )
    report["verified_scientific_rules"] = sorted(
        set(report["verified_scientific_rules"])
        | {
            ADAPTER,
            "sequence_change_projection@1",
            "sequence_change_support@1",
            "annotation_item_support@1",
            "annotation_structure_request@1",
        }
    )
    report["verified_navigation_policies"] = sorted(
        set(report.get("verified_navigation_policies", []))
        | {"retained_context_links@3", "sequence_change_access_origins@1"}
    )
    report["recorded_navigation_decisions"] = (
        "Exact Card annotation occurrences, original source/back/question context, finite typed requests and actual operation parents verified. Structural results are reported only when retained; no current scientific calculation or acquisition."
    )
    return report
