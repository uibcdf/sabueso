"""Conservative interval interpretation without changing original @3.

Classes describe configured concentration bands, not efficacy or selectivity.
A class requires the entire permitted interval to occupy one band. Single-point
inhibition is not converted into a potency bound or a compound dose from prose.
"""

import math

from .errors import ArgumentError

RULE = "bioactivity_class@4"
LEGACY_RULE = "bioactivity_class@3"


def classification_rule(value):
    if isinstance(value, str) and value in (LEGACY_RULE, RULE):
        return value
    raise ArgumentError(
        'classification_rule requires "bioactivity_class@3" or "bioactivity_class@4".',
        argument="classification_rule",
    )


def thresholds_in_force(thresholds):
    from .bioactivities import _value_in, resolve_thresholds
    from .quantities import CONCENTRATION_UNIT

    nodes = resolve_thresholds(thresholds)
    active = _value_in(nodes["active_max"], CONCENTRATION_UNIT)
    weak = _value_in(nodes["weak_max"], CONCENTRATION_UNIT)
    percent = _value_in(nodes["single_point_min"], "percent")
    if not (
        all(math.isfinite(x) for x in (active, weak, percent))
        and 0 < active <= weak
        and 0 <= percent <= 100
    ):
        raise ArgumentError(
            "Activity thresholds require finite positive ordered concentration "
            "bounds and a percentage between 0 and 100.",
            argument="thresholds",
        )
    return nodes, active, weak


def derivation(thresholds):
    from .relationship_store import make_derivation

    nodes, _, _ = thresholds_in_force(thresholds)
    return make_derivation(
        RULE,
        inputs=["has_bioactivity.measurement", "has_bioactivity.assay.description"],
        parameters={
            **nodes,
            "class_meaning": "configured concentration band, not efficacy or selectivity",
            "interval_policy": "classify only when all permitted values occupy one band",
            "single_point_policy": "retain inhibition; do not infer potency or compound dose from assay text",
            "unused_thresholds": ["single_point_min"],
            "uncertainty_policy": "inconclusive when stated uncertainty has no interpreted interval",
            "missing_relation": "a stated scalar without a relation is read as an exact point",
        },
    )


def classify(measurement, assay_description=None, thresholds=None):
    from .bioactivities import (
        INACTIVE_COMMENTS,
        NOT_DETERMINED,
        POTENCY_TYPES,
        SINGLE_POINT_TYPES,
        is_range,
        upper_node,
    )
    from .quantities import (
        CONCENTRATION_UNIT,
        is_quantity_node,
        normalized_measurement,
    )

    _, active, weak = thresholds_in_force(thresholds)

    def answer(cls, basis, reason):
        return {"class": cls, "basis": basis, "interpretation": reason}

    if measurement.get("value") is None:
        comment = (measurement.get("activity_comment") or "").strip().lower()
        if comment in NOT_DETERMINED:
            return answer(
                "not_determined",
                "activity_comment",
                "The source states not determined.",
            )
        if comment in INACTIVE_COMMENTS:
            return answer(
                "inactive",
                "activity_comment",
                "The source states an inactive activity comment.",
            )
        return answer("inconclusive", "no_value", "No numeric measurement is stated.")

    kind = measurement.get("type")
    if kind in SINGLE_POINT_TYPES:
        result = answer(
            "inconclusive",
            "single_point_context_required",
            "This rule does not infer a potency class from single-point inhibition. "
            "The assay description has not been validated as a tested-compound dose.",
        )
        result["test_concentration_state"] = "not_interpreted"
        return result
    if kind not in POTENCY_TYPES:
        return answer(
            "unclassified",
            "measurement_type",
            "This measurement type has no potency-band interpretation.",
        )
    if (
        measurement.get("normalized_uncertainty") is not None
        or measurement.get("uncertainty") is not None
    ):
        return answer(
            "inconclusive",
            "uncertainty_not_interpreted",
            "The stated uncertainty has no interpreted permitted interval.",
        )

    def valid(node):
        return (
            is_quantity_node(node)
            and node["unit"] == CONCENTRATION_UNIT
            and math.isfinite(node["value"])
            and node["value"] > 0
        )

    try:
        raw = measurement.get("value")
        node = measurement.get("normalized") or normalized_measurement(
            raw, measurement.get("units")
        )
        if isinstance(raw, bool) or not valid(node):
            return answer(
                "inconclusive",
                "invalid_potency",
                "A finite positive concentration in supported units is required.",
            )
        value = node["value"]
        relation = measurement.get("relation") or "="
        if is_range(measurement):
            upper = upper_node(measurement)
            if (
                isinstance(measurement.get("upper_value"), bool)
                or not valid(upper)
                or upper["value"] < value
            ):
                return answer(
                    "inconclusive",
                    "invalid_potency_range",
                    "The stated range needs finite positive ordered endpoints.",
                )
            if relation != "=":
                return answer(
                    "inconclusive",
                    "range_relation_not_interpreted",
                    "The range and its additional qualifier need explicit interpretation.",
                )
            high = upper["value"]
            cls = (
                "active"
                if high <= active
                else "weak"
                if value > active and high <= weak
                else "inactive"
                if value > weak
                else "inconclusive"
            )
            return answer(
                cls,
                "potency_range",
                "Both range endpoints and every value between them must occupy the same band.",
            )
    except (TypeError, ValueError, OverflowError):
        return answer(
            "inconclusive",
            "invalid_potency",
            "The supplied potency cannot be interpreted as a finite positive concentration.",
        )

    if relation == "=":
        cls = "active" if value <= active else "weak" if value <= weak else "inactive"
    elif relation in ("<", "<="):
        cls = "active" if value <= active else "inconclusive"
    elif relation == ">":
        cls = "inactive" if value >= weak else "inconclusive"
    elif relation == ">=":
        cls = "inactive" if value > weak else "inconclusive"
    else:
        return answer(
            "inconclusive",
            "relation_not_interpreted",
            "The qualifier has no defined permitted interval under this rule.",
        )
    return answer(
        cls,
        "potency",
        "The entire interval permitted by the relation must occupy the configured band.",
    )
