"""Human sequence changes sharing exact source occurrences with compact access."""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle
from .card_sequence_change_access import materialize
from .card_sequence_change_selection_v1 import (
    FORMAT,
    equal,
    sorted_entries,
    validate_equality,
)

HEADERS = (
    "Index",
    "Source annotation",
    "Sequence axis",
    "Original positions",
    "Original change",
    "Source support",
)


def view(explorer, origin, options=None):
    result = materialize(explorer.access, options)
    captured = explorer._inspect(
        result.location(), origin, title="Natural variants and mutagenesis"
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(
            captured._selection,
            _result_ref=result.result_ref,
            _selection_ref=_handle(
                "XA_",
                {
                    "format": "sequence_change_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel="sequence_changes",
        _native_override=result.native,
        _context_override=result.wire["context"],
        _request=origin.request if origin else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def open_item(item):
    opened = item._view.explorer._inspect(
        item.payload_location, item._view, title=item.label
    )
    return replace(opened, _request=item._view.request)


def explain(item):
    result, explorer = item._view._selection._scientific, item._view.explorer
    opened = explorer._inspect(
        result.location("explanations", item._entry.key),
        item._view,
        title="Original annotation support · " + item.label,
    )
    entries = []
    for statement in result.wire["support"][item._entry.key]["source_assertions"]:
        if statement["state"] == "present":
            value, location = explorer.access._resolve(statement["location"])
            entries.append(_Entry(location, statement["id"], value))
    explorer._session["views"].pop(id(opened), None)
    return replace(
        opened,
        _selection=replace(opened._selection, _entries=tuple(entries)),
        _selected=tuple(entries),
        _native_override=result.explanations[item._entry.key],
        _request=item._view.request,
        _reason="Exact original annotation support; unrelated field statements remain contextual.",
    )


def display_filter(view, column, operand):
    validate_equality(column, operand)
    result = view._selection._scientific
    entries = tuple(
        e for e in view._selected if equal(result.value(e.key, column), operand)
    )
    return replace(
        view,
        _selected=entries,
        _origin=view,
        _status=view._status if entries else "empty",
        _display_request={
            "operation": "filter",
            "column": column,
            "equals": deepcopy(operand),
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


def opening(view, preview):
    return [
        "Each row retains one Card annotation occurrence and all its matching source statements; it does not establish unique native-feature correspondence.",
        "Natural variants and experimental mutagenesis are different source statement types; equal positions never join them to population genomic variants.",
        "Read the original residue and complete alternative list together. A deletion is stated only when the original missing flag is true; unstated values remain unknown.",
        "Original axes, endpoint modifiers, source conflicts and sequence revisions remain in item support. Related structural questions use the existing source-bound admission rule and may remain unavailable.",
        "Open an item for its complete original annotation, explain() for exact source records, and related() for original input sources and the explicit structural question.",
        "Captured Card export retains the original source data.",
    ]


def display_row(item, index, preview):
    row = item._entry.value
    change = "not stated"
    if row["missing"] is True:
        change = "stated deletion"
    elif row["original"] is not None or row["alternatives"] is not None:
        change = preview(row["original"]) + " → " + preview(row["alternatives"])
    return (
        str(index),
        preview(item.label),
        preview(row["sequence_ref"]),
        preview(row["start"])
        + " – "
        + preview(row["end"])
        + " · "
        + preview(row["start_modifier"])
        + "/"
        + preview(row["end_modifier"]),
        change,
        preview(row["support_state"]),
    )
