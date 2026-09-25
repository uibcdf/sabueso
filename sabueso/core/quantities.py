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

#: Every place a card stores quantities (a path template, as the seal names its columns)
#: and the units negotiated for it. The writer refuses a quantity anywhere else, and the
#: reader declares these, not what the card says, as the fields and dimensionalities it
#: expects (MOLI quantity integrity policy, guarantee 2).
NEGOTIATED_UNITS: Dict[str, Tuple[str, ...]] = {
    **{path: (unit,) for path, unit in FIELD_UNITS.items()},
    "relationships.has_structure.resolution": (LENGTH_UNIT,),
    "relationships.has_structure.ligands.instances.contacts.min_distance": (
        LENGTH_UNIT,
    ),
    "relationships.has_bioactivity.measurement.normalized": (
        CONCENTRATION_UNIT,
        "percent",
    ),
    # A range: the upper end, normalized like the lower one (#37, schema 0.3.2).
    "relationships.has_bioactivity.measurement.normalized_upper": (
        CONCENTRATION_UNIT,
        "percent",
    ),
    # An uncertainty a publication states, in the measurement's normalized unit (#37).
    **{
        f"relationships.has_bioactivity.measurement.normalized_uncertainty.{part}": (
            CONCENTRATION_UNIT,
            "percent",
        )
        for part in ("half_width", "lower", "upper")
    },
}

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


def _negotiated(key: str) -> str:
    """The unit of column ``key`` if Sabueso negotiated it there; otherwise None."""
    template, unit = key.rsplit("|", 1)
    allowed = NEGOTIATED_UNITS.get(template, ())
    return unit if unit in {canonical_unit(u) for u in allowed} else None


def _dimensionality(unit: str) -> Dict[str, int]:
    import pyunitwizard as puw

    dims = puw.get_dimensionality(puw.quantity(1.0, unit, form="pint"))
    return {k: int(v) for k, v in dims.items()}


def seal(card_data: Mapping[str, Any]) -> Dict[str, Any]:
    """The ``quantities`` entry of a stored card: one bundle, one column per path and unit."""
    import numpy as np
    import pyunitwizard as puw
    from pyunitwizard import QuantityRecordBundle

    raw = _columns(card_data)
    unexpected = sorted(key for key in raw if _negotiated(key) is None)
    if unexpected:
        raise SchemaError(
            f"Quantities outside Sabueso's negotiated paths and units: {unexpected}. "
            "Register them in quantities.NEGOTIATED_UNITS."
        )
    columns = {
        key: puw.quantity(np.asarray(values, dtype=np.float64), unit, form="pint")
        for key, (unit, values) in raw.items()
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
            f"Card {card_id} has no quantities seal; cards since schema 0.3.0 are written with one, "
            "and there is no default unit."
        )
    columns = _columns(card_data)
    unexpected = sorted(key for key in columns if _negotiated(key) is None)
    if unexpected:
        raise StorageError(
            f"Card {card_id} stores quantities where Sabueso negotiated none, or in "
            f"another unit: {unexpected}."
        )
    try:
        bundle = QuantityRecordBundle.from_dict(sealed)
        # The expectation is Sabueso's, per column: the negotiated unit's dimensionality.
        stored = bundle.to_quantities(
            expected={key: _dimensionality(unit) for key, (unit, _) in columns.items()},
            form="pint",
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


def quantity_columns(card_data: Mapping[str, Any], template: str) -> Dict[str, Any]:
    """``{unit: array quantity}`` of every node at ``template``, as sealed.

    One column per unit, in stored order; units are never mixed or converted here.
    """
    import numpy as np
    import pyunitwizard as puw

    out: Dict[str, Any] = {}
    for key, (unit, values) in _columns(card_data).items():
        if key.rsplit("|", 1)[0] == template:
            out[unit] = puw.quantity(np.asarray(values, dtype=np.float64), unit)
    return out


#: Orders of magnitude that mark a probable unit slip, as in ChEMBL's "Potential
#: transcription error": nM written as µM or pM (3), or as mM (6).
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
