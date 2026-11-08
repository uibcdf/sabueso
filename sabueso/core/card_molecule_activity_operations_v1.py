"""Exact recorded molecule operation histories for exploration @21.

Node identities distinguish executions; they never merge molecular identities.
The operation manifest preserves all repeated destination occurrences.
"""

from dataclasses import replace

from . import card_exploration_molecule_activity as binding
from .card_access import _handle
from .snapshot import canonical_json

MEMBER = "molecule_activity_operations"
RULE = "molecule_activity_operation_history@1"
NODE = "_molecule_node_ref"


def _key(source, operation, row):
    return _handle("MO_", {"source": source, "operation": operation, "row_key": row})


def _edge(view):
    parent = view._origin
    if parent is None:
        return None
    root_return = (
        parent._link_panel and binding.is_context(parent) and binding.is_view(view)
    )
    if view._display_request is not None and not root_return:
        return None
    if binding.is_view(parent):
        if binding.is_context(view):
            context = view._context_override
            role = context["activity_context"]
            if role in ("links", "support"):
                return (
                    parent,
                    "links" if role == "links" else "explanations",
                    context["molecule_activity_navigation"]["source_row_key"],
                )
        if binding.is_view(view):
            result = view._selection._scientific
            grain = result.wire["context"]["grain"]
            rows = [
                entry
                for entry in parent._selected
                if (
                    grain == "group"
                    and entry.value["target_card_ref"]
                    == result.options["target_card_ref"]
                )
                or (
                    grain == "record"
                    and entry.value["target_card_ref"]
                    == result.options["target_card_ref"]
                    and entry.value["measurement_ref"]
                    == result.options["measurement_ref"]
                )
            ]
            if view.presentation == "detail" and len(view._selected) == 1:
                rows = [
                    entry
                    for entry in parent._selected
                    if entry.location == view._selected[0].location
                ]
            if len(rows) == 1:
                return parent, "open", rows[0].key
    if parent._link_panel and binding.is_context(parent):
        if binding.is_view(view):
            role = "molecule_root"
            rows = [entry for entry in parent._selected if entry.value["role"] == role]
        elif binding.is_context(view):
            role = view._context_override["activity_context"]
            rows = binding._endpoint_entries(view, parent, role)
        else:
            return None
        binding.require(
            len(rows) == 1, "Molecule endpoint lost its exact original link occurrence."
        )
        return parent, "open", rows[0].key
    return None


def manifest(nodes):
    identities = {id(view): key for key, view in nodes.items()}
    result = {}
    for destination, view in nodes.items():
        edge = _edge(view)
        if edge is None:
            continue
        parent, operation, row = edge
        binding.require(
            id(parent) in identities,
            "Molecule operation has a foreign source instance.",
        )
        source = identities[id(parent)]
        key = _key(source, operation, row)
        record = result.setdefault(
            key,
            {
                "rule": RULE,
                "source": source,
                "operation": operation,
                "row_key": row,
                "destinations": [],
            },
        )
        record["destinations"].append(destination)
    return result


def register(bundle, nodes):
    bundle[MEMBER] = manifest(nodes)


def verify(bundle, nodes):
    binding.same(
        bundle[MEMBER],
        manifest(nodes),
        "molecule complete source-instance operation history",
    )
    # Every displayed scientific row must retain its original support routes.
    for source, view in nodes.items():
        if not binding.is_view(view):
            continue
        for entry in view._selected:
            for operation in ("links", "explanations"):
                binding.require(
                    _key(source, operation, entry.key) in bundle[MEMBER],
                    "Molecule displayed row lacks its exact original operation closure.",
                )


def _source(view):
    session = view._explorer._session
    key = (view._saved_state or {}).get(NODE)
    original = session.get("original_nodes", {}).get(key)
    if original is None:
        return None
    if canonical_json(binding._selection_binding(original)) != canonical_json(
        binding._selection_binding(view)
    ):
        return None
    return key


def has_operation(view, operation):
    """Report only routes retained for this actual displayed source history."""
    source, session = _source(view), view._explorer._session
    return (
        bool(view._selected)
        and source is not None
        and all(
            _key(source, operation, entry.key) in session.get(MEMBER, {})
            for entry in view._selected
        )
    )


def has_support_closure(view):
    """Empty displays require no row routes; other displays need both routes."""
    return not view._selected or all(
        has_operation(view, operation) for operation in ("explanations", "links")
    )


def saved_machine_view(selection):
    """Find the exact retained request, including a legitimate focal rebind."""
    access = selection._access
    session = access._exploration_session or {}

    def request(value):
        return {
            "result_ref": value.result_ref,
            "selection_ref": value.selection_ref,
            "operation": value._operation,
            "fields": list(value._fields),
            "entries": [vars(entry) for entry in value._entries],
            "context_location": value._context_location,
            "target": value._target,
            "slice": value._slice,
            "outcome_override": value._outcome_override,
        }

    requested = canonical_json(request(selection))
    for view in session.get("original_nodes", {}).values():
        if (
            view._machine_ref == selection.selection_ref
            and view._explorer.access._focal_key == access._focal_key
            and view._explorer.access._inputs == access._inputs
            and canonical_json(request(view._selection)) == requested
        ):
            return view
    return None


def saved_item(item, operation):
    from .card_exploration_storage import not_saved

    view, session = item._view, item._view._explorer._session
    source = _source(view)
    record = (
        session.get(MEMBER, {}).get(_key(source, operation, item._entry.key))
        if source is not None
        else None
    )
    if record is None:
        return not_saved(
            view._explorer,
            "This exact molecule operation and originating history were not retained.",
            view,
        )
    destinations = [session["original_nodes"][key] for key in record["destinations"]]
    first = destinations[0]
    binding.require(
        all(
            canonical_json(binding._selection_binding(candidate))
            == canonical_json(binding._selection_binding(first))
            and canonical_json(candidate.native_payload)
            == canonical_json(first.native_payload)
            for candidate in destinations
        ),
        "Repeated original molecule operations have different destinations.",
    )
    return replace(first, _origin=view)


def recorded_display(view, operation):
    source, session = _source(view), view._explorer._session
    if source is None:
        return None
    original = session["original_nodes"][source]
    for candidate in session["original_nodes"].values():
        if candidate._origin is original and canonical_json(
            candidate._display_request
        ) == canonical_json(operation):
            return replace(candidate, _origin=view, _explorer=view._explorer)
    return None
