"""Frozen typed display selection over original assembly-generation findings."""

from copy import deepcopy

from .card_access import _handle
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "assembly_generation_access_selection@1"
COLUMNS = (
    "label",
    "kind",
    "structure_ref",
    "assembly_id",
    "status",
    "operator_scope",
    "component_scope",
    "declaration_count",
    "count_state",
    "finding",
    "reason",
)
NULLABLE = {
    "structure_ref",
    "assembly_id",
    "operator_scope",
    "component_scope",
    "declaration_count",
}
DEFAULT_FIELDS = (
    "structure_ref",
    "assembly_id",
    "status",
    "operator_scope",
    "component_scope",
    "declaration_count",
)


def projection(fields):
    if fields is None:
        return DEFAULT_FIELDS
    if isinstance(fields, str):
        fields = [fields]
    if (
        not isinstance(fields, (list, tuple))
        or any(not isinstance(f, str) or f not in COLUMNS for f in fields)
        or len(set(fields)) != len(fields)
    ):
        raise ArgumentError(f"fields requires unique keys from {', '.join(COLUMNS)}.")
    return tuple(fields)


def validate_equality(column, value):
    if not isinstance(column, str) or column not in COLUMNS:
        raise ArgumentError("Use a declared assembly-generation column.")
    if value is None and column in NULLABLE:
        return
    if column == "declaration_count":
        if type(value) is not int or value < 0:
            raise ArgumentError(
                "declaration_count requires a nonnegative integer or None, never a boolean or quantity."
            )
    elif not isinstance(value, str):
        raise ArgumentError(
            f"{column} requires a string" + (" or None." if column in NULLABLE else ".")
        )
    try:
        canonical_json(value).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, StorageError) as exc:
        raise ArgumentError(
            "Selection operands require serializable Unicode values."
        ) from exc


def normalize(where, item_refs, order_by):
    where = {} if where is None else where
    if not isinstance(where, dict):
        raise ArgumentError("where requires a mapping of declared column equalities.")
    for column, value in where.items():
        validate_equality(column, value)
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
            or order_by.get("column") not in COLUMNS
            or type(order_by.get("descending", False)) is not bool
            or order_by.get("unit") is not None
        ):
            raise ArgumentError(
                "order_by requires a declared column, optional boolean descending and no quantity unit."
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
    members = query["item_refs"]
    known = {item_ref(result, e) for e in result.entries}
    if members is not None and set(members) - known:
        raise ArgumentError("item_refs contains an item outside this assembly result.")
    selected, exclusions = [], []
    for entry in result.entries:
        ref, reasons = item_ref(result, entry), []
        if members is not None and ref not in members:
            reasons.append({"kind": "membership"})
        for column, value in sorted(query["where"].items()):
            if result.value(entry.key, column) != value:
                reasons.append(
                    {
                        "kind": "where",
                        "column": column,
                        "cell_state": result.cell_state(entry.key, column),
                    }
                )
        if reasons:
            exclusions.append(
                {"item_ref": ref, "location": entry.location, "reasons": reasons}
            )
        else:
            selected.append(entry)
    order = query["order_by"]
    if order is not None:
        present = [
            e for e in selected if result.value(e.key, order["column"]) is not None
        ]
        missing = [e for e in selected if result.value(e.key, order["column"]) is None]
        present.sort(
            key=lambda e: result.value(e.key, order["column"]),
            reverse=order["descending"],
        )
        selected = present + missing
    return tuple(selected), {
        "format": FORMAT,
        **deepcopy(query),
        "underlying_count": len(result.entries),
        "selected_count": len(selected),
        "members": [item_ref(result, e) for e in selected],
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
