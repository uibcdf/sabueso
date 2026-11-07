"""Original SDK200 argument shapes, independent of current public digesters."""

import re

from ..errors import ArgumentError


def digest_include_indirect(value):
    if type(value) is not bool:
        raise ArgumentError("include_indirect requires a boolean.")
    return value


def digest_molecule_ref(value):
    if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_.]*:[^\s#]+", value):
        return value
    raise ArgumentError("molecule_ref requires an exact namespaced bioactivity key.")


def digest_measurement_ref(value):
    if isinstance(value, str) and re.fullmatch(
        r"(?:REL_[A-Za-z0-9_]+|MG_[0-9a-f]{16})", value
    ):
        return value
    raise ArgumentError("measurement_ref requires a native REL_ or MG_ identifier.")


def digest_item_ref(value):
    if isinstance(value, str) and re.fullmatch(r"XI_[0-9a-f]{64}", value):
        return value
    raise ArgumentError("item_refs requires exact XI_ references.")


def digest_thresholds(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ArgumentError("thresholds requires quantities in a mapping or None.")
    from .bioactivities import resolve_thresholds

    resolve_thresholds(value)
    return value
