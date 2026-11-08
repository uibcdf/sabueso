"""Typed selections of retained clinical statements and citation occurrences."""

from copy import deepcopy
from math import isfinite

from .card_access import _handle
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

FORMAT = "clinical_access_selection@1"
COLUMNS = (
    "label",
    "kind",
    "molecule_ref",
    "disease_ref",
    "disease_term",
    "trial_ref",
    "chembl_max_phase",
    "registry_status",
    "registry_phases",
    "registry_state",
    "citation_count",
    "state",
)
DEFAULT_FIELDS = (
    "kind",
    "disease_term",
    "trial_ref",
    "chembl_max_phase",
    "registry_state",
    "registry_status",
)
SORT_COLUMNS = tuple(key for key in COLUMNS if key != "registry_phases")


def validate_equality(column, value):
    if column not in COLUMNS:
        raise ArgumentError("Unknown clinical equality column.")
    if value is not None:
        if column == "chembl_max_phase":
            if type(value) not in (int, float) or (
                type(value) is float and not isfinite(value)
            ):
                raise ArgumentError("ChEMBL phase requires a finite number or null.")
        elif column == "citation_count":
            if type(value) is not int or value < 0:
                raise ArgumentError(
                    "Clinical citation count requires a nonnegative integer or null."
                )
        elif column == "registry_phases":
            if not isinstance(value, list) or any(
                not isinstance(v, str) for v in value
            ):
                raise ArgumentError(
                    "Registry phases require an original list of strings or null."
                )
        elif not isinstance(value, str):
            raise ArgumentError("Clinical text columns require text or null.")
    try:
        canonical_json(value).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, StorageError) as exc:
        raise ArgumentError("Clinical equality requires serializable Unicode.") from exc


def equal(first, second):
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
        raise ArgumentError("fields requires unique declared clinical column names.")
    return tuple(fields)


def normalize(where, item_refs, order_by):
    where = {} if where is None else where
    if not isinstance(where, dict):
        raise ArgumentError("Clinical where requires a column-to-operand mapping.")
    for column, value in where.items():
        if not isinstance(column, str):
            raise ArgumentError("Clinical where keys require declared column names.")
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
            or order_by.get("column") not in SORT_COLUMNS
            or type(order_by.get("descending", False)) is not bool
            or order_by.get("unit") is not None
        ):
            raise ArgumentError(
                "Clinical order_by requires a sortable scalar column, boolean descending and no unit."
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


def sorted_entries(entries, result, column, descending=False, unit=None):
    normalize({}, None, {"column": column, "descending": descending, "unit": unit})
    present, missing = [], []
    for entry in entries:
        (missing if result.value(entry.key, column) is None else present).append(entry)
    present.sort(key=lambda entry: result.value(entry.key, column), reverse=descending)
    return tuple([*present, *missing])


def evaluate(result, query):
    membership = query["item_refs"]
    if membership is not None and set(membership) - {
        item_ref(result, e) for e in result.entries
    }:
        raise ArgumentError(
            "item_refs contains an item outside this captured clinical result."
        )
    selected, exclusions = [], []
    for entry in result.entries:
        ref, reasons = item_ref(result, entry), []
        if membership is not None and ref not in membership:
            reasons.append({"kind": "membership"})
        for column, operand in sorted(query["where"].items()):
            if not equal(result.value(entry.key, column), operand):
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
    if query["order_by"] is not None:
        selected = sorted_entries(selected, result, **query["order_by"])
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
