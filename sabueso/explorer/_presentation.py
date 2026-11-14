"""Bounded human projections of native Card fields, cells and source edges.

This is presentation, not another scientific reader. Original items, states,
locations, units and support remain authoritative in the native view. Previews
are explicitly incomplete; Open and Sources keep the exact native bindings.
"""

from __future__ import annotations

from sabueso.core.card_exploration_render import preview

CELL_LIMIT = 8
TEXT_LIMIT = 240


def _cell(item, name, cell):
    from sabueso.core.card_exploration import Cell
    from sabueso.core.card_exploration_storage import _cell_record

    # Reuse the original Card codec to establish physical meaning; a textual
    # number or an arbitrary dictionary does not become a physical quantity.
    value = cell._value if type(cell) is Cell else cell.value
    record = (
        _cell_record(item, name, cell)
        if value is not None
        and not isinstance(value, (str, dict, list, tuple, int, float, bool))
        else {"encoding": "json"}
    )
    result = {
        "column": name,
        "text": preview(value, TEXT_LIMIT),
        "state": cell.state,
        "reason": cell.reason,
        "filterable": isinstance(value, str) and name in item._view.schema["columns"],
        "quantity": None,
    }
    if record["encoding"] == "quantity_record":
        import pyunitwizard as puw

        unit = record["unit"]
        result.update(
            text=f"{preview(puw.get_value(value, to_unit=unit), TEXT_LIMIT)} {unit}",
            quantity={
                "field": record["field"],
                "unit": unit,
                "record": record["value"],
            },
            filterable=name in item._view.schema["columns"],
        )
    return result


def item_preview(item):
    cells = item.cells
    names = [name for name in cells if name not in ("label", "kind", "type")]
    from ._association_presentation import applies

    # Keep the finite native identity/support cells beside source/channel.
    limit = 11 if applies(item._view) else CELL_LIMIT
    return {
        "cells": [_cell(item, name, cells[name]) for name in names[:limit]],
        "cell_count": len(names),
        "complete": len(names) <= limit,
    }


def orientation(view):
    # The bounded native orientation helper avoids copying whole function or
    # definition bodies solely to render their short preview.
    from sabueso.core.card_orientation_v1 import reading

    data = reading(view, source_limit=4, copy_values=False)
    if data is None:
        return None
    return {
        "rule": data["rule"],
        "profile": data["profile"],
        "fields": [
            {
                "path": field["path"],
                "label": field["label"],
                "state": field["state"],
                "can_open": field["field_location"] is not None,
                "text": preview(field["value"], TEXT_LIMIT),
                "support_state": field["support"]["state"],
                "sources": [
                    {
                        "state": source["state"],
                        "text": f"{preview(source['source'].get('name'), 60)} [{preview(source['source'].get('version'), 60)}]"
                        if isinstance(source["source"], dict)
                        else "Source descriptor not retained",
                    }
                    for source in field["support"]["sources"]
                ],
            }
            for field in data["fields"]
        ],
    }


def relationship_graph(items):
    """Only original relationship endpoints; no name, hierarchy or identity join."""
    edges = []
    for item in items:
        if item.kind != "relationship":
            continue
        cells = item.cells
        if not {"subject_ref", "predicate", "object_ref"} <= set(cells):
            continue
        values = {
            name: cells[name].value
            for name in ("subject_ref", "predicate", "object_ref")
        }
        if not all(isinstance(value, str) and value for value in values.values()):
            continue
        edges.append({"item_ref": item.item_ref, **values})
    return (
        {
            "rule": "retained_relationship_graph@1",
            "edges": edges,
            "scope": "Current page of retained relationship records; inspect original support and derivations",
        }
        if edges
        else None
    )


def text_kind(view):
    location = view._selection._target.get("location", {})
    if view.explorer is not None:
        _, location = view.explorer.access._resolve(location)
    segments = location.get("segments", [])
    return (
        "sequence"
        if (
            location.get("kind") == "card"
            and segments
            == [
                {"type": "Key", "value": key}
                for key in ("sections", "sequence", "primary", "value")
            ]
            and view.explorer is not None
            and view.explorer.profile == "protein"
        )
        else "text"
    )
