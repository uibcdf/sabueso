"""Typed display selection over one original bioactivity result.

Selection changes displayed original members, never scientific grouping or scope.
"""

import math
from copy import deepcopy

from .card_access import _handle
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "bioactivity_access_selection@1"
QUANTITY_FIELD = "relationships.has_bioactivity.measurement.normalized"
COUNTS = ("measurement_count", "record_count")
COLUMNS = (
    "label",
    "kind",
    "molecule_ref",
    "measurement_ref",
    "relationship_id",
    "class",
    "measurement",
    "relation",
    *COUNTS,
    "source",
    "assay_ref",
    "document_ref",
)
DEFAULT_FIELDS = ("molecule_ref", "class", "measurement", *COUNTS)


def quantity_node(value):
    """Accept an explicit finite scalar concentration or percentage quantity."""
    import pyunitwizard as puw

    try:
        if isinstance(value, dict) and set(value) == {"value", "unit"}:
            if type(value["value"]) not in (int, float) or not isinstance(
                value["unit"], str
            ):
                raise ValueError("Invalid quantity node")
            quantity = puw.quantity(value["value"], value["unit"], form="pint")
        elif puw.is_quantity(value):
            quantity = value
        else:
            raise ValueError("Explicit quantity required")
        unit = puw.convert(
            str(puw.get_unit(quantity)), to_form="record", to_type="unit"
        )
        number = puw.get_value(quantity, to_unit=unit)
        if getattr(number, "shape", ()) != () or not math.isfinite(float(number)):
            raise ValueError("Finite scalar required")
        node = {"value": float(number), "unit": unit}
        _unit_target(unit)
        return node
    except Exception as exc:
        raise ArgumentError(
            "measurement requires a finite scalar concentration or percentage quantity with an explicit unit."
        ) from exc


def _unit_target(unit):
    import pyunitwizard as puw

    if not isinstance(unit, str) or not unit.strip():
        raise ArgumentError("measurement ordering requires an explicit unit.")
    for target in ("nanomolar", "percent"):
        try:
            puw.get_value(puw.quantity(1, unit, form="pint"), to_unit=target)
            return target
        except Exception:
            pass
    raise ArgumentError("measurement requires a concentration or percentage unit.")


def _number(node, unit):
    import pyunitwizard as puw

    from .quantities import converted

    try:
        quantity = puw.quantity(node["value"], node["unit"], form="pint")
        return converted(float(puw.get_value(quantity, to_unit=unit)))
    except Exception as exc:
        raise ArgumentError(
            "Measurement dimensions differ; concentration and percentage cannot be compared."
        ) from exc


def validate_equality(column, value):
    if column not in COLUMNS:
        raise ArgumentError("Unknown bioactivity equality column.")
    if value is None:
        return
    if column == "measurement":
        quantity_node(value)
    elif column in COUNTS:
        if type(value) is not int or value < 0:
            raise ArgumentError(
                "Bioactivity counts require a nonnegative integer or null."
            )
    elif not isinstance(value, str):
        raise ArgumentError("Bioactivity text columns require text or null.")
    else:
        try:
            canonical_json(value).encode("utf-8")
        except (TypeError, ValueError, UnicodeError, StorageError) as exc:
            raise ArgumentError(
                "Bioactivity equality requires serializable Unicode."
            ) from exc


def equal(first, second):
    if first is None or second is None:
        return first is None and second is None
    import pyunitwizard as puw

    if (isinstance(first, dict) and set(first) == {"value", "unit"}) or (
        not isinstance(first, (str, int, float, bool)) and puw.is_quantity(first)
    ):
        one, two = quantity_node(first), quantity_node(second)
        return _number(one, one["unit"]) == _number(two, one["unit"])
    return type(first) is type(second) and first == second


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
    where = {} if where is None else where
    if not isinstance(where, dict):
        raise ArgumentError("Bioactivity where requires a column-to-operand mapping.")
    encoded = {}
    for column, value in where.items():
        if not isinstance(column, str):
            raise ArgumentError("Bioactivity where keys must be declared columns.")
        validate_equality(column, value)
        encoded[column] = (
            quantity_node(value)
            if column == "measurement" and value is not None
            else deepcopy(value)
        )
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
        ):
            raise ArgumentError(
                "order_by requires a declared column and boolean descending."
            )
        unit = order_by.get("unit")
        if order_by["column"] == "measurement":
            _unit_target(unit)
        elif unit is not None:
            raise ArgumentError("unit applies only to measurement ordering.")
        order_by = {
            "column": order_by["column"],
            "descending": order_by.get("descending", False),
            "unit": unit,
        }
    return {"where": encoded, "item_refs": item_refs, "order_by": order_by}


def active(query):
    return (
        bool(query["where"])
        or query["item_refs"] is not None
        or query["order_by"] is not None
    )


def item_ref(result, entry):
    return _handle("XI_", {"result_ref": result.result_ref, "location": entry.location})


def sorted_entries(entries, result, column, descending=False, unit=None):
    """Order an existing display subset; unknown values stay last in either direction."""
    order = normalize(
        {}, None, {"column": column, "descending": descending, "unit": unit}
    )["order_by"]
    present = [
        entry for entry in entries if result.value(entry.key, column) is not None
    ]
    missing = [entry for entry in entries if result.value(entry.key, column) is None]
    present.sort(
        key=lambda entry: (
            _number(result.value(entry.key, column), order["unit"])
            if column == "measurement"
            else result.value(entry.key, column)
        ),
        reverse=descending,
    )
    return tuple([*present, *missing])


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
        for column, operand in sorted(query["where"].items()):
            if column == "measurement":
                continue
            value = result.value(entry.key, column)
            if not equal(value, operand):
                reasons.append(
                    {
                        "kind": "where",
                        "column": column,
                        "cell_state": result.cell_state(entry.key, column),
                        "reason": result.cell_reason(entry.key, column),
                    }
                )
        if not reasons and "measurement" in query["where"]:
            if not equal(
                result.value(entry.key, "measurement"), query["where"]["measurement"]
            ):
                reasons.append(
                    {
                        "kind": "where",
                        "column": "measurement",
                        "cell_state": result.cell_state(entry.key, "measurement"),
                        "reason": result.cell_reason(entry.key, "measurement"),
                    }
                )
        if reasons:
            exclusions.append(
                {"item_ref": ref, "location": entry.location, "reasons": reasons}
            )
        else:
            selected.append(entry)
    if query["order_by"] is not None:
        selected = sorted_entries(selected, result, **query["order_by"])
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
