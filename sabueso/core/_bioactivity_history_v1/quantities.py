# Frozen original B4 predicates from 2eb6114 / SDK200.
# Private consistency expectations only; preserve these meanings.
"""Original consumed quantity vocabulary and explicit conversions; no Card I/O."""

from functools import lru_cache
from typing import Any, Dict, Optional

from ..errors import SchemaError

CONCENTRATION_UNIT = "nanomolar"


CHEMBL_UNITS: Dict[str, str] = {
    "pM": "picomolar",
    "nM": "nanomolar",
    "uM": "micromolar",
    "µM": "micromolar",
    "mM": "millimolar",
    "M": "molar",
    "%": "percent",
}


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


SCALE_ORDERS = (3, 6)


def scale_discrepancy(a: Any, b: Any) -> int | None:
    """3 or 6 when two values of one quantity differ by exactly that many orders of
    magnitude; otherwise None. Values must already be in the same unit."""
    import math

    numbers = (int, float)
    if isinstance(a, bool) or isinstance(b, bool):
        return None
    if not (isinstance(a, numbers) and isinstance(b, numbers)) or a <= 0 or b <= 0:
        return None
    ratio = max(a, b) / min(a, b)
    for orders in SCALE_ORDERS:
        if math.isclose(ratio, 10.0**orders, rel_tol=10.0 ** -(SIGNIFICANT_DIGITS - 3)):
            return orders
    return None


def to_quantity(node: Any):
    """A PyUnitWizard quantity from a node, in the session's default form."""
    import pyunitwizard as puw

    if not is_quantity_node(node):
        raise SchemaError(f"Not a quantity: {node!r}.")
    return puw.quantity(node["value"], node["unit"])
