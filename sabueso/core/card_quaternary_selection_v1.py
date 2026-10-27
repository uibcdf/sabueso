"""Versioned textual display selection over native quaternary results (#148).

This policy creates no scientific knowledge. Preserve v1 semantics when adding
future selection policies; historical verification must not switch to live rules.
"""

from copy import deepcopy

from .card_access import _handle
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "quaternary_access_selection@1"
COLUMNS = (
    "label",
    "kind",
    "partner_ref",
    "status",
    "coordinate_status",
    "finding",
    "reason",
)
DEFAULT_FIELDS = ("kind", "partner_ref", "status", "coordinate_status", "finding")


def projection(fields):
    if fields is None:
        return DEFAULT_FIELDS
    if isinstance(fields, str):
        fields = [fields]
    if (
        not isinstance(fields, (list, tuple))
        or any(not isinstance(key, str) or key not in COLUMNS for key in fields)
        or len(set(fields)) != len(fields)
    ):
        raise ArgumentError(f"fields requires unique keys from {', '.join(COLUMNS)}.")
    return tuple(fields)


def normalize(where, item_refs, order_by):
    if where is None:
        where = {}
    if not isinstance(where, dict) or any(
        not isinstance(key, str) or key not in COLUMNS or not isinstance(value, str)
        for key, value in where.items()
    ):
        raise ArgumentError(
            "Quaternary where requires declared textual columns and string operands."
        )
    try:
        canonical_json(where).encode("utf-8")
    except (ValueError, TypeError, UnicodeError, StorageError) as exc:
        raise ArgumentError(
            "where operands require serializable Unicode strings."
        ) from exc
    if item_refs is not None:
        from sabueso._private.argdigest.argument.item_ref import digest_item_ref

        if not isinstance(item_refs, (list, tuple)):
            raise ArgumentError(
                "item_refs requires a sequence of exact item references."
            )
        item_refs = [digest_item_ref(ref) for ref in item_refs]
        if len(set(item_refs)) != len(item_refs):
            raise ArgumentError("item_refs must not contain duplicates.")
        item_refs = sorted(item_refs)
    if order_by is not None:
        if (
            not isinstance(order_by, dict)
            or set(order_by) - {"column", "descending", "unit"}
            or not isinstance(order_by.get("column"), str)
            or order_by["column"] not in COLUMNS
            or type(order_by.get("descending", False)) is not bool
            or order_by.get("unit") is not None
        ):
            raise ArgumentError(
                "Quaternary order_by requires a textual column, optional boolean descending and no unit."
            )
        order_by = {
            "column": order_by["column"],
            "descending": order_by.get("descending", False),
            "unit": None,
        }
    return {"where": deepcopy(where), "item_refs": item_refs, "order_by": order_by}


def active(query):
    return (
        bool(query["where"])
        or query["item_refs"] is not None
        or query["order_by"] is not None
    )


def item_ref(result, entry):
    return _handle("XI_", {"result_ref": result.result_ref, "location": entry.location})


def evaluate(result, query):
    membership = query["item_refs"]
    refs = {item_ref(result, entry) for entry in result.entries}
    if membership is not None and set(membership) - refs:
        raise ArgumentError(
            "item_refs contains an item outside this scientific result."
        )
    selected, exclusions = [], []
    for entry in result.entries:
        ref, reasons = item_ref(result, entry), []
        if membership is not None and ref not in membership:
            reasons.append({"kind": "membership"})
        for column, value in sorted(query["where"].items()):
            if result.value(entry.key, column) != value:
                reasons.append(
                    {"kind": "where", "column": column, "cell_state": "present"}
                )
        if reasons:
            exclusions.append(
                {"item_ref": ref, "location": entry.location, "reasons": reasons}
            )
        else:
            selected.append(entry)
    order = query["order_by"]
    if order is not None:
        selected.sort(
            key=lambda entry: result.value(entry.key, order["column"]),
            reverse=order["descending"],
        )
    return tuple(selected), {
        "format": FORMAT,
        **deepcopy(query),
        "underlying_count": len(result.entries),
        "selected_count": len(selected),
        "members": [item_ref(result, entry) for entry in selected],
        "display_exclusions": exclusions,
    }


def selection_ref(result, fields, spec):
    return _handle(
        "XA_",
        {
            "format": FORMAT,
            "result_ref": result.result_ref,
            "fields": fields,
            "selection": spec,
        },
    )
