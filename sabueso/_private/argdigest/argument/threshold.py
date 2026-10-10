"""Dimensionless pext cutoff used by comparative explanations."""

import math

from sabueso._private.argdigest._shared import refuse


def digest_threshold(threshold, caller=None):
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or not 0 <= threshold <= 1
    ):
        raise refuse(
            "threshold",
            threshold,
            caller,
            "expected a finite dimensionless number in [0, 1]",
        )
    return threshold
