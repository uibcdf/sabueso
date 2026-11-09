"""Pure SDK230 threshold/rule grammar; no public scientific digesters."""

from math import isfinite

from .._literature_history_v1.validation import digest_item_ref as digest_item_ref
from ..errors import ArgumentError


def digest_threshold(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 1
        or not isfinite(value)
    ):
        raise ArgumentError("Expected a finite dimensionless threshold in [0, 1].")
    return value


def check_arguments(threshold, usage_rule, *, kind):
    digest_threshold(threshold)
    expected = "pext_at_variant@2" if kind == "variant" else "isoform_exon_usage@3"
    if usage_rule != expected:
        raise ArgumentError("Unsupported original scoped tissue rule.")
