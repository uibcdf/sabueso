"""Physical quantities in cards (uibcdf/sabueso#32).

Every stored quantity is a node ``{"value": x, "unit": "<canonical name>"}``; a number
never carries its unit in a field name, in metadata, or in documentation only. When a
card is written, all its quantity nodes are sealed together by one PyUnitWizard
``QuantityRecordBundle`` (``Card.to_dict()["quantities"]``) whose entries are *columns*:
every value of one quantity path in one unit, in a deterministic order. When a card is
read, PyUnitWizard verifies the bundle and Sabueso checks every node against its column,
so a change made outside Sabueso, to a node or to the seal, is refused. It is a
cross-checked redundancy, never a fallback.

The format itself belongs to PyUnitWizard (uibcdf/pyunitwizard#82, design in #83); this
module only decides which Sabueso values are quantities, in which unit, and where they
live. Sabueso never configures PyUnitWizard's session policy and converts only with an
explicit target unit (uibcdf/moli#11).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from .errors import SchemaError, StorageError

#: Negotiated unit of each section field that holds a quantity.
FIELD_UNITS: Dict[str, str] = {
    "sequence.molecular_weight": "dalton",
    "properties.physchem.molecular_weight": "dalton",
    "properties.physchem.tpsa": "angstrom ** 2",
}
#: Unit of normalized bioactivity concentrations (DECISIONS: homogeneous nanomolar).
CONCENTRATION_UNIT = "nanomolar"
LENGTH_UNIT = "angstrom"

#: ChEMBL ``standard_units`` spellings Sabueso normalizes, and to what. Source strings are
#: never handed to a unit parser: ``nM`` and ``nm`` differ only in case, and ChEMBL's
#: ``ug.mL-1`` is not a valid pint expression. Anything else is left unnormalized.
CHEMBL_UNITS: Dict[str, str] = {
    "pM": "picomolar",
    "nM": "nanomolar",
    "uM": "micromolar",
    "µM": "micromolar",
    "mM": "millimolar",
    "M": "molar",
    "%": "percent",
}
_CONCENTRATIONS = {"picomolar", "nanomolar", "micromolar", "millimolar", "molar"}


#: Significant digits kept after a unit conversion. pint converts through SI base units,
#: so 20 µM becomes 19999.999999999996 nM; a measurement exactly on a threshold would
#: then fall on either side depending on how the threshold was written, and stored
#: values would carry the noise. No source states more than a few digits; 12 keeps every
#: stated digit and drops the noise.
SIGNIFICANT_DIGITS = 12


def converted(value: float) -> float:
    """A converted value without floating-point noise (see SIGNIFICANT_DIGITS)."""
    return float(f"{value:.{SIGNIFICANT_DIGITS}g}")


@lru_cache(maxsize=None)
def canonical_unit(unit: str) -> str:
    """PyUnitWizard's canonical spelling of ``unit`` (``"nM"`` → ``"nanomolar"``)."""
    import pyunitwizard as puw

    return puw.convert(unit, to_form="record", to_type="unit")


def quantity_node(value: Any, unit: str) -> Optional[Dict[str, Any]]:
    """A stored quantity, or ``None`` when there is no value."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"A quantity value must be a number, not {value!r}.")
    return {"value": value, "unit": canonical_unit(unit)}


def field_node(
    field_path: str, value: Any, source_assertion_ids: List[str]
) -> Dict[str, Any]:
    """A section field node; fields with a negotiated unit carry it."""
    node: Dict[str, Any] = {
        "value": value,
        "source_assertion_ids": source_assertion_ids,
    }
    unit = FIELD_UNITS.get(field_path)
    if (
        unit is not None
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        node["unit"] = canonical_unit(unit)
    return node


def normalized_measurement(value: Any, units: Any) -> Optional[Dict[str, Any]]:
    """A ChEMBL measurement normalized to nanomolar (or kept in percent), if it can be.

    The conversion is explicit (``to_unit``); the session's standard units play no part.
    """
    if value is None or units not in CHEMBL_UNITS:
        return None
    unit = CHEMBL_UNITS[units]
    if unit == "percent":
        return quantity_node(value, "percent")
    import pyunitwizard as puw

    value_nM = puw.convert(
        puw.quantity(float(value), unit, form="pint"),
        to_unit=CONCENTRATION_UNIT,
        to_type="value",
    )
    return quantity_node(converted(float(value_nM)), CONCENTRATION_UNIT)


def is_quantity_node(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("unit"), str)
        and isinstance(obj.get("value"), (int, float))
        and not isinstance(obj.get("value"), bool)
    )


def _walk(obj: Any, template: str) -> Iterator[Tuple[str, Dict[str, Any]]]:
    if is_quantity_node(obj):
        yield template, obj
        return
    if isinstance(obj, dict):
        for key in sorted(obj):
            yield from _walk(obj[key], f"{template}.{key}" if template else str(key))
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item, template)


def iter_quantity_nodes(
    card_data: Mapping[str, Any],
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """``(path template, node)`` for every quantity node, in deterministic order.

    Sections are walked in key order; relationships in id order, their qualifiers in key
    order, and lists in their stored order. List indices do not appear in templates, so
    one template names a whole column.
    """
    yield from _walk(card_data.get("sections") or {}, "")
    relationships = sorted(
        card_data.get("relationship_store") or [], key=lambda r: r.get("id", "")
    )
    for relationship in relationships:
        yield from _walk(
            relationship.get("qualifiers") or {},
            f"relationships.{relationship.get('predicate')}",
        )


def _columns(card_data: Mapping[str, Any]) -> Dict[str, Tuple[str, List[float]]]:
    columns: Dict[str, Tuple[str, List[float]]] = {}
    for template, node in iter_quantity_nodes(card_data):
        key = f"{template}|{node['unit']}"
        columns.setdefault(key, (node["unit"], []))[1].append(float(node["value"]))
    return columns


def seal(card_data: Mapping[str, Any]) -> Dict[str, Any]:
    """The ``quantities`` entry of a stored card: one bundle, one column per path and unit."""
    import numpy as np
    import pyunitwizard as puw
    from pyunitwizard import QuantityRecordBundle

    columns = {
        key: puw.quantity(np.asarray(values, dtype=np.float64), unit, form="pint")
        for key, (unit, values) in _columns(card_data).items()
    }
    return QuantityRecordBundle.from_quantities(columns).to_dict()


def verify(card_data: Mapping[str, Any], sealed: Any) -> None:
    """Refuse a stored card whose quantities do not match their seal."""
    import numpy as np
    import pyunitwizard as puw
    from pyunitwizard import QuantityRecordBundle

    card_id = (card_data.get("meta") or {}).get("card_id")
    if sealed is None:
        raise StorageError(
            f"Card {card_id} has no quantities seal; schema 0.3.0 cards are written with one, "
            "and there is no default unit."
        )
    columns = _columns(card_data)
    try:
        bundle = QuantityRecordBundle.from_dict(sealed)
        stored = bundle.to_quantities(
            expected={key: None for key in columns}, form="pint"
        )
    except Exception as exc:  # RecordError, or a malformed bundle
        raise StorageError(
            f"Card {card_id}: the quantities seal does not verify ({exc})."
        ) from exc
    for key, (unit, values) in columns.items():
        q = stored[key]
        if str(puw.get_unit(q)) != unit or not np.array_equal(
            np.asarray(puw.get_value(q), dtype=np.float64).reshape(-1),
            np.asarray(values, dtype=np.float64),
        ):
            raise StorageError(
                f"Card {card_id}: the quantities at {key!r} were changed outside Sabueso; "
                "they no longer match their seal."
            )


def to_quantity(node: Any):
    """A PyUnitWizard quantity from a node, in the session's default form."""
    import pyunitwizard as puw

    if not is_quantity_node(node):
        raise SchemaError(f"Not a quantity: {node!r}.")
    return puw.quantity(node["value"], node["unit"])
