"""Independent SDK224 clinical human/source/navigation predicates."""

from copy import deepcopy
from dataclasses import replace

from ._clinical_history_v1 import exploration as frozen
from ._clinical_history_v1.machine import _machine
from ._clinical_history_v1.replay import ReplayExplorer
from ._clinical_history_v1.selection import COLUMNS
from .card_access import _handle
from .card_clinical_history_v1 import ADAPTER, TOPIC
from .card_exploration import CardItem, CardView, Cell
from .card_exploration_molecule_activity import ADAPTERS as OLDER_ADAPTERS
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@25"
VERIFIER = "clinical_exploration_binding@1"
LINK_RULE = "clinical_context_links@1"
ADAPTERS = (*OLDER_ADAPTERS, ADAPTER)
SCHEMA = {
    "kind": "clinical_exploration",
    "grain": "separate molecule phase, indication, cited-trial occurrence and registry record",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        "Saved clinical " + scope + " differs from its original binding.",
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


def is_links(view):
    return (
        view._link_panel
        and isinstance(view.native_payload, dict)
        and view.native_payload.get("rule") == LINK_RULE
    )


def _full(access, location):
    return access._resolve(location)[1]


def _entry_for_location(parent, target, kind):
    result = parent._selection._scientific
    for entry in parent._selected:
        location = (
            result.location("explanations", entry.key)
            if kind == "explanation"
            else result.location("rows", entry.key, "item")
        )
        if canonical_json(location) == canonical_json(target):
            return entry
    raise StorageError(
        "Clinical destination is not an exact member of its originating selection."
    )


def edge(view):
    """Identify an original operation by its actual parent and exact typed target."""
    if (
        view._display_request is not None
        or view._origin is None
        or not (is_context(view) or is_links(view))
    ):
        return None
    parent, access = view._origin, view._explorer.access
    target = _full(access, view._selection._target["location"])
    role = (view._context_override or {}).get("clinical_context")
    if is_view(parent):
        if is_links(view):
            native = view.native_payload
            location = (
                native.get("source_location") if isinstance(native, dict) else None
            )
            entries = [
                entry
                for entry in parent._selected
                if canonical_json(entry.location) == canonical_json(location)
            ]
            require(
                len(entries) == 1, "Clinical links lost their exact originating row."
            )
            return parent, "links", entries[0].key
        if role in ("original_item", "explanation"):
            entry = _entry_for_location(parent, target, role)
            return (
                parent,
                "open" if role == "original_item" else "explanations",
                entry.key,
            )
    if is_links(parent):
        choices = []
        for entry in parent._selected:
            link = entry.value
            if len(link["candidates"]) == 1:
                if (
                    canonical_json(link["candidates"][0]["location"])
                    == canonical_json(target)
                    and link["label"] == view.title
                    and link["role"] == role
                ):
                    choices.append(entry)
            elif (
                not link["candidates"]
                and view._context_only
                and view.native_payload.get("link") == link
            ):
                choices.append(entry)
        require(
            len(choices) == 1,
            "Clinical source destination lost its exact originating link.",
        )
        return parent, "open", choices[0].key
    return None


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
    """Bind declared clinical cells and original literal source/quantity cells."""
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
        "Clinical view has a foreign structural operation.",
    )
    same(
        {key: getattr(view, key) for key in _FLAGS},
        {key: getattr(expected, key) for key in _FLAGS},
        "presentation flags, request and outcome",
    )
    same(
        _selection_state(view._selection, view._explorer.access),
        _selection_state(expected._selection, replay.access),
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
        "Unknown clinical native encoding.",
    )
    expected_state = _state(expected)
    mode = record["state"]["context"].get("mode")
    require(mode in ("live", "saved"), "Unknown clinical saved context mode.")
    expected_state["context"] = {**expected_state["context"], "mode": mode}
    same(
        record["state"],
        expected_state,
        "full typed cells, source support, schema and request coverage",
    )


def _scope(view):
    parent = view._origin
    if parent is not None and (
        is_view(parent) or is_context(parent) or is_links(parent)
    ):
        require(
            parent._explorer.access._focal_key == view._explorer.access._focal_key
            and parent._explorer.access._inputs == view._explorer.access._inputs
            and parent._explorer._origin is view._explorer._origin,
            "Clinical navigation crossed its original explorer scope.",
        )
        same(view.request, parent.request, "inherited question continuity")
    if view.request is not None:
        same(
            view.request,
            {"question": "clinical_context", "topic": TOPIC, "options": {}},
            "declared clinical question",
        )


def verify_view(view, record):
    """Reenact only immutable presentation rules over already verified original rows."""
    _scope(view)
    replay = ReplayExplorer(view._explorer)
    parent = replay.shadow(view._origin) if view._origin is not None else None
    request_mode = view._explorer.access._resolve(view._selection._context_location)[0][
        "context"
    ]["mode"]
    require(
        request_mode in ("live", "saved"), "Unknown original clinical request mode."
    )
    replay.access._mode = request_mode
    operation = view._display_request
    if is_view(view):
        if operation is not None:
            require(
                parent is not None and is_view(parent),
                "Clinical display lost its exact originating result.",
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
                require(
                    operation == {"operation": "presentation"},
                    "Unknown clinical display operation.",
                )
                expected = replace(
                    parent,
                    _origin=parent,
                    presentation=view.presentation,
                    _display_request=operation,
                )
        elif view._selection._operation == "select:" + TOPIC:
            result = view._selection._scientific
            entries = _machine(view._selection, view._explorer.access, result)
            expected = CardView(
                replay,
                view._selection,
                entries,
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
            expected = frozen.view(replay, parent)
            expected = replace(expected, _request=view.request)
    else:
        require(
            is_context(view) or is_links(view), "Unknown independent clinical view."
        )
        if operation is not None:
            # Original literal display grammar remains independently owned by the
            # literal verifier; its undisplayed anchor is checked here too.
            from .card_exploration_literature import _literal_state

            require(
                parent is not None and is_context(parent),
                "Clinical literal display lost its originating context.",
            )
            same(
                view._context_override,
                parent._context_override,
                "literal display context",
            )
            same(
                _selection_state(view._selection, view._explorer.access),
                _selection_state(parent._selection, parent._explorer.access),
                "literal display original selection",
            )
            same(
                record["native_payload"],
                parent.native_payload,
                "literal display original native context",
            )
            _literal_state(view, record)
            return
        relation = edge(view)
        if relation is not None:
            _, kind, key = relation
            entry = next(entry for entry in parent._selected if entry.key == key)
            item = CardItem(parent, entry)
            if parent._link_panel:
                expected = frozen.follow(item)
            elif kind == "links":
                expected = frozen.links(item)
                if view._context_override is None:
                    intermediates = [
                        candidate
                        for candidate in replay._session["views"].values()
                        if is_links(candidate) and candidate._context_override is None
                    ]
                    require(
                        len(intermediates) == 1,
                        "Clinical link construction is ambiguous.",
                    )
                    expected = intermediates[0]
            elif kind == "explanations":
                expected = frozen.explain(item)
            else:
                expected = frozen.open_item(item)
        else:
            require(
                parent is not None and is_context(parent) and not parent._link_panel,
                "Clinical literal descendant has no original parent.",
            )
            full = _full(view._explorer.access, view._selection._target["location"])
            matches = [
                entry
                for entry in parent._selection._entries
                if canonical_json(entry.location) == canonical_json(full)
            ]
            require(
                len(matches) == 1,
                "Clinical literal descendant is not an original child.",
            )
            item = CardItem(parent, matches[0])
            expected = replace(
                replay._inspect(full, parent, title=item.label),
                _request=parent.request,
                _context_only=parent._context_only,
                _context_override=parent._context_override,
            )
    _compare(view, expected, record, replay)


def descriptor():
    from .card_clinical_history_v1 import descriptor as original_descriptor

    return original_descriptor()


def register_bundle(bundle, objects, access):
    from .card_exploration_molecule_activity import ADAPTERS as older_adapters

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
    from .card_clinical_history_v1 import verify_result
    from .card_exploration_literature import verify_objects as older_objects
    from .card_exploration_molecule_activity import verify_objects as molecule_objects

    older, molecule = {}, False
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            molecule |= (
                wire["context"]["adapter"] == "molecule_activity_context_exploration@1"
            )
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Clinical result lost its exact focal manifest.",
        )
        verify_result(accesses[record["focal"]], ref, wire)
    projected = {**bundle, "scientific_results": older}
    if molecule:
        molecule_objects(projected, accesses)
    else:
        require(
            bundle["molecule_activity_crossings"] == {},
            "Clinical-only bundle has a foreign molecule crossing.",
        )
        older_objects(projected, accesses)


def _publish(expected, explorer, origin):
    """Expose only frozen literal navigation metadata over the retained original."""
    source, destination = expected._explorer.access, explorer.access
    for ref, value in source._objects.items():
        if ref not in destination._objects:
            require(
                ref
                == _handle("XR_", {"adapter": "literal_metadata@1", "value": value}),
                "Clinical navigation attempted to create a scientific result.",
            )
            destination._objects[ref] = value
            destination._metadata_refs.add(ref)
    destination._locations.update(source._locations)
    selection = replace(expected._selection, _access=destination)
    destination._selections.setdefault(selection.selection_ref, selection)
    return replace(expected, _explorer=explorer, _selection=selection, _origin=origin)


def item_operation(item, operation):
    """Read original clinical data without executing current science or digesters."""
    explorer = item._view._explorer
    replay = ReplayExplorer(explorer)
    parent = replay.shadow(item._view)
    original = CardItem(parent, item._entry)
    expected = (
        frozen.follow(original)
        if parent._link_panel
        else frozen.open_item(original)
        if operation == "open"
        else frozen.explain(original)
        if operation == "explanations"
        else frozen.links(original)
    )
    return _publish(expected, explorer, item._view)


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
    from ._clinical_history_v1.selection import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )
    from .card_clinical_history_v1 import options_for_clinical
    from .card_exploration_storage import missing_selection

    options, fields = options_for_clinical(options), projection(fields)
    query = normalize(where, item_refs, order_by)
    for selection in access._selections.values():
        if (
            not is_result(selection._scientific)
            or selection._operation != "select:" + TOPIC
        ):
            continue
        result = selection._scientific
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
    from .card_clinical_history_v1 import options_for_clinical
    from .card_exploration_storage import not_saved

    options_for_clinical(options)
    request = (
        {"question": "clinical_context", "topic": TOPIC, "options": {}}
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
            and view.request == request
        ):
            return replace(
                view,
                _explorer=explorer,
                _origin=explorer._origin if origin is None else origin,
            )
    return not_saved(
        explorer, "This original clinical topic/question was not retained.", origin
    )


def display_filter(view, column, equals):
    return frozen.display_filter(view, column, equals)


def display_sort(view, column, descending=False, unit=None):
    return frozen.display_sort(view, column, descending, unit)


def validate_filters(bundle):
    from .card_exploration_molecule_activity import validate_filters as older_filters

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
    from .card_exploration_literature import verification_report as older_report

    report = older_report(bundle)
    older_rules = report["verified_scientific_rules"]
    report.update(
        {
            "verifier": VERIFIER,
            "integrity": "verified",
            "bindings": "original captured snapshots, frozen clinical values/source roles/request scope and exact typed human/machine/navigation context",
            "verified_scientific_adapters": sorted(
                {
                    bundle["objects"][ref]["context"]["adapter"]
                    for ref in bundle["scientific_results"]
                }
            ),
            "verified_scientific_rules": [
                ADAPTER,
                "clinical_support_membership@1",
                "clinical_query_scope@1",
                "knowledge_state@5",
            ],
            "recorded_navigation_decisions": "Original clinical source/indication/registry destinations and exact originating questions independently verified; literal reading may inspect retained raw context without a new source request.",
            "source_authenticity_and_truth": "not_established_by_hashes",
            "clinical": "original_frozen_v1_consistency_verified",
        }
    )
    report["verified_scientific_rules"] = sorted(
        set(report["verified_scientific_rules"]) | set(older_rules)
    )
    if (
        "molecule_activity_context_exploration@1"
        in report["verified_scientific_adapters"]
    ):
        from .card_exploration_molecule_activity_v2 import ROOT_RETURN_POLICY

        report.update(
            activity_context="original_frozen_v1_consistency_verified",
            verified_navigation_policies=[ROOT_RETURN_POLICY],
            originating_root_instances="verified_against_exact_retained_origin_chain",
        )
    return report


def saved_declared_destination(explorer, candidate, origin):
    """Admit original @23 destination predicates in an explicit @25 projection."""
    from copy import copy

    from .card_exploration_molecule_activity_v2 import (
        saved_declared_destination as original_destination,
    )

    if explorer._session.get("format") != FORMAT:
        return None
    projected = copy(explorer)
    projected._session = {**explorer._session, "format": "sabueso.card_exploration@23"}
    result = original_destination(projected, candidate, origin)
    if result is not None:
        result._explorer._session = explorer._session
    return result
