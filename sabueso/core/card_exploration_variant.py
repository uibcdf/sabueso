"""Independent SDK230 variant tissue context human/source/navigation predicates."""

from copy import deepcopy
from dataclasses import replace

from ._variant_history_v1 import exploration as frozen
from ._variant_history_v1.machine import _machine
from ._variant_history_v1.replay import ReplayExplorer
from ._variant_history_v1.selection import COLUMNS
from .card_access import _handle
from .card_exploration import CardItem, CardView, Cell
from .card_exploration_disease_association import ADAPTERS as OLDER_ADAPTERS
from .card_variant_history_v1 import ADAPTER, TOPIC, options_for_variants
from .errors import StorageError
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@29"
VERIFIER = "variant_tissue_context_exploration_binding@1"
LINK_RULE = "variant_context_links@1"
ADAPTERS = (*OLDER_ADAPTERS, ADAPTER)
SCHEMA = {
    "kind": "variant_tissue_context_exploration",
    "grain": "native population-variant or isoform occurrence",
    "columns": list(COLUMNS),
    "presentations": ["summary", "table", "detail"],
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def same(actual, expected, scope):
    require(
        canonical_json(actual) == canonical_json(expected),
        "Saved variant tissue context " + scope + " differs from its original binding.",
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


def original_occurrences(selection, record):
    """Restore repeated references only in the frozen role-bound explanation."""
    flags = record["flags"]
    context = flags.get("_context_override") or {}
    if (
        context.get("adapter") != LINK_RULE
        or context.get("variant_context") != "explanation"
    ):
        return None
    buckets = {}
    for entry in selection._entries:
        ref = _handle(
            "XI_", {"result_ref": selection.result_ref, "location": entry.location}
        )
        buckets.setdefault(ref, []).append(entry)
    for entries in buckets.values():
        require(
            all(
                canonical_json(vars(entry)) == canonical_json(vars(entries[0]))
                for entry in entries
            ),
            "Repeated variant source references have different literal contents.",
        )
    consumed, selected = {}, []
    for ref in record["selected"]:
        index = consumed.get(ref, 0)
        require(
            ref in buckets and index < len(buckets[ref]),
            "Variant source occurrence count differs.",
        )
        selected.append(buckets[ref][index])
        consumed[ref] = index + 1
    return tuple(selected)


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
        "Variant tissue context destination is not an exact member of its originating selection."
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
    role = (view._context_override or {}).get("variant_context")
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
                len(entries) == 1,
                "Variant tissue context links lost their exact originating row.",
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
            bool(choices)
            and all(
                canonical_json(entry.value) == canonical_json(choices[0].value)
                for entry in choices
            )
            and all(
                not entry.value["candidates"]
                or entry.value["candidates"][0]["capture"]
                == view._explorer.access._focal_key
                for entry in choices
            ),
            "Variant tissue context source destination lost its original link membership.",
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
    """Bind declared variant tissue context cells and original literal source/quantity cells."""
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
        "Variant tissue context view has a foreign structural operation.",
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
        "Unknown variant tissue context native encoding.",
    )
    expected_state = _state(expected)
    mode = record["state"]["context"].get("mode")
    require(
        mode in ("live", "saved"), "Unknown variant tissue context saved context mode."
    )
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
            "Variant navigation changed its original focal/input/explorer scope.",
        )
        same(view.request, parent.request, "inherited question continuity")
    if view.request is not None:
        request = view.request
        require(
            set(request) == {"question", "topic", "options"}
            and request["topic"] == TOPIC
            and request["question"]
            in ("variant_tissue_context", "isoform_tissue_context"),
            "Unknown original variant question.",
        )
        options = options_for_variants(request["options"])
        same(request["options"], options, "effective typed question options")
        require(
            options["mode"]
            == (
                "variants"
                if request["question"] == "variant_tissue_context"
                else "isoforms"
            ),
            "Variant question mode differs.",
        )
        if is_view(view):
            same(
                options, view._selection._scientific.options, "question/result options"
            )


def verify_view(view, record):
    """Reenact only immutable presentation rules over already verified original rows."""
    _scope(view)
    replay = ReplayExplorer(
        view._origin._explorer
        if not is_view(view) and view._origin is not None and is_links(view._origin)
        else view._explorer
    )
    parent = replay.shadow(view._origin) if view._origin is not None else None
    request_mode = view._explorer.access._resolve(view._selection._context_location)[0][
        "context"
    ]["mode"]
    require(
        request_mode in ("live", "saved"),
        "Unknown original variant tissue context request mode.",
    )
    replay.access._mode = request_mode
    operation = view._display_request
    if is_view(view):
        if operation is not None:
            require(
                parent is not None and is_view(parent),
                "Variant tissue context display lost its exact originating result.",
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
                    "Unknown variant tissue context display operation.",
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
            expected = frozen.view(replay, parent, view._selection._scientific.options)
            expected = replace(expected, _request=view.request)
    else:
        require(
            is_context(view) or is_links(view),
            "Unknown independent variant tissue context view.",
        )
        if operation is not None:
            # Original literal display grammar remains independently owned by the
            # literal verifier; its undisplayed anchor is checked here too.
            from .card_exploration_literature import _literal_state

            require(
                parent is not None and is_context(parent),
                "Variant tissue context literal display lost its originating context.",
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
                        "Variant tissue context link construction is ambiguous.",
                    )
                    expected = intermediates[0]
            elif kind == "explanations":
                expected = frozen.explain(item)
            else:
                expected = frozen.open_item(item)
        else:
            require(
                parent is not None and is_context(parent) and not parent._link_panel,
                "Variant tissue context literal descendant has no original parent.",
            )
            full = _full(view._explorer.access, view._selection._target["location"])
            matches = [
                entry
                for entry in parent._selection._entries
                if canonical_json(entry.location) == canonical_json(full)
            ]
            require(
                bool(matches)
                and all(
                    canonical_json(vars(entry)) == canonical_json(vars(matches[0]))
                    for entry in matches
                ),
                "Variant tissue context literal descendant is not an original child.",
            )
            item = CardItem(parent, matches[0])
            expected = (
                replace(
                    replay._inspect(full, parent, title=item.label),
                    _request=parent.request,
                    _context_only=parent._context_only,
                    _context_override=parent._context_override,
                )
                if (view._context_override or {}).get("variant_context")
                == "literal_child"
                else replace(
                    replay._inspect(full, parent, title=item.label),
                    _request=parent.request,
                    _context_only=parent._context_only,
                    _context_override=parent._context_override,
                )
            )
    _compare(view, expected, record, replay)


def descriptor():
    from .card_variant_history_v1 import descriptor as original_descriptor

    return original_descriptor()


def verify_literal_view(view, record):
    """Use frozen literal/catalog predicates for the actual auxiliary nodes."""
    from .card_exploration_verification_v29 import (
        _verify_profile,
        _verify_request,
        _verify_state,
    )

    require(
        not is_view(view) and not is_context(view) and not is_links(view),
        "A rich variant view cannot enter the literal inspection predicate.",
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
    from .card_exploration_disease_association import ADAPTERS as older_adapters

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
    from .card_exploration_disease_association import verify_objects as older_objects
    from .card_variant_history_v1 import verify_result

    older = {}
    for ref, record in bundle["scientific_results"].items():
        wire = bundle["objects"][ref]
        if wire["context"]["adapter"] != ADAPTER:
            older[ref] = record
            continue
        require(
            set(record) == {"focal"} and record["focal"] in accesses,
            "Variant tissue context result lost its original focal manifest.",
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
                "Variant tissue context navigation attempted to create a scientific result.",
            )
            destination._objects[ref] = value
            destination._metadata_refs.add(ref)
    destination._locations.update(source._locations)
    selection = replace(expected._selection, _access=destination)
    destination._selections.setdefault(selection.selection_ref, selection)
    return replace(expected, _explorer=explorer, _selection=selection, _origin=origin)


def item_operation(item, operation):
    """Read original variant tissue context data without executing current science or digesters."""
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


def open_retained_child(item):
    require(
        is_context(item._view)
        and any(
            canonical_json(vars(entry)) == canonical_json(vars(item._entry))
            for entry in item._view._selected
        ),
        "Variant literal child is outside its originating display.",
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
    from ._variant_history_v1.selection import (
        active,
        evaluate,
        normalize,
        projection,
        selection_ref,
    )
    from .card_exploration_storage import missing_selection
    from .card_variant_history_v1 import options_for_variants

    options, fields = options_for_variants(options), projection(fields)
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

    options = options_for_variants(options)
    request = (
        {
            "question": "variant_tissue_context"
            if options["mode"] == "variants"
            else "isoform_tissue_context",
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
        explorer, "This original variant topic/question was not retained.", origin
    )


def display_filter(view, column, equals):
    return frozen.display_filter(view, column, equals)


def display_sort(view, column, descending=False, unit=None):
    return frozen.display_sort(view, column, descending, unit)


def validate_filters(bundle):
    from .card_exploration_disease_association import validate_filters as older_filters

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
    from .card_exploration_disease_association import (
        verification_report as older_report,
    )

    report = older_report(bundle)
    report.update(
        verifier=VERIFIER,
        bindings="original captured snapshots, frozen scoped variant/isoform native/source values and exact typed human/machine/origin context",
        variants="original_frozen_v1_consistency_verified",
        verified_scientific_rules=sorted(
            set(report["verified_scientific_rules"])
            | {
                ADAPTER,
                "variant_tissue_context_support@1",
                "pext_at_variant@2",
                "isoform_exon_usage@3",
            }
        ),
    )
    report["verified_navigation_policies"] = sorted(
        set(report.get("verified_navigation_policies", []))
        | {"variant_context_links@1"}
    )
    if (
        "disease_association_exploration@1"
        not in report["verified_scientific_adapters"]
    ):
        report.pop("associations", None)
        report["verified_scientific_rules"] = [
            rule
            for rule in report["verified_scientific_rules"]
            if rule
            not in (
                "disease_association_exploration@1",
                "disease_association_support@1",
                "disease_association_context@1",
                "knowledge_state@5",
            )
        ]
        report["verified_navigation_policies"] = [
            rule
            for rule in report["verified_navigation_policies"]
            if rule
            not in (
                "disease_scientific_question_transition@1",
                "disease_source_occurrences@1",
            )
        ]
    report["recorded_navigation_decisions"] = (
        "Original variant/isoform native/input/source destinations and exact initiating typed questions and actual origins verified. Additional scientific adapters are reported only when retained."
    )
    return report
