"""Original shared detail and typed display predicates only."""

from copy import deepcopy
from dataclasses import replace

from .._protein_context_history_v1.selection import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)


def inherited_request(origin):
    request = origin.request if origin is not None else None
    return (
        request
        if isinstance(request, dict)
        and request.get("question")
        in (
            "protein_associations",
            "related_proteins",
            "sequence_differences",
            "knowledge_differences",
        )
        and request.get("topic") in ("associations", "comparative_context")
        else None
    )


def open_item(item):
    row = item._entry.value
    # Original items remain accessible through the local result even if the
    # original captured input belongs to another explicit focal context.
    result = item._view._selection._scientific
    opened = item._view.explorer._inspect(
        result.location("rows", item._entry.key, "item"), item._view, title=item.label
    )
    return replace(
        opened, _native_override=deepcopy(row["item"]), _request=item._view.request
    )


def explain(item):
    result, explorer, key = (
        item._view._selection._scientific,
        item._view.explorer,
        item._entry.key,
    )
    opened = explorer._inspect(
        result.location("explanations", key),
        item._view,
        title="Recorded source bindings · " + item.label,
    )
    # The source list is metadata with exact original locations. Following a
    # foreign source explicitly switches its focal access through related().
    return replace(
        opened,
        _native_override=deepcopy(result.explanations[key]),
        _request=item._view.request,
    )


def display_filter(view, column, value):
    validate_equality(column, value)
    entries = tuple(
        e
        for e in view._selected
        if equal(view._selection._scientific.value(e.key, column), value)
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=view._status if entries else "empty",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(value),
            "filter_policy": FORMAT,
        },
    )


def display_sort(view, column, descending=False, unit=None):
    entries = sorted_entries(
        view._selected, view._selection._scientific, column, descending, unit
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
            "sort_policy": FORMAT,
        },
    )
