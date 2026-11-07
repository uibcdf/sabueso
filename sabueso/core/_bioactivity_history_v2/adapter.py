"""SDK202 literature inputs for the unchanged original bioactivity builder.

The SDK200 scientific, quantity, membership, selection and result predicates stay
immutable. Its native-input cache is an explicit frozen contract: SDK202 changes
only the retained literature summary projection, including False and numeric zero.
Seed that complete input before invoking the original builder; never patch its
functions or replace any recorded wire value with an expected value.
"""

from copy import deepcopy

from .._bioactivity_history_v1 import adapter as _original
from .._bioactivity_history_v1.adapter import ADAPTER as ADAPTER
from .._bioactivity_history_v1.adapter import SUPPORT_FORMAT as SUPPORT_FORMAT
from .._bioactivity_history_v1.adapter import TOPIC as TOPIC
from .._bioactivity_history_v1.adapter import BioactivityResult as BioactivityResult
from .._bioactivity_history_v1.adapter import defer_frame as defer_frame
from .._bioactivity_history_v1.adapter import descriptor as descriptor
from .._bioactivity_history_v1.adapter import (
    options_for_bioactivities as options_for_bioactivities,
)
from ..snapshot import canonical_json
from .inputs import _CapturedCard
from .rules import native_request


def _native(access, method, *args, **kwargs):
    if method not in ("literature", "explain_literature"):
        return _original._native(access, method, *args, **kwargs)
    key = (
        ADAPTER,
        "native",
        access._focal_key,
        method,
        canonical_json([args, kwargs]),
    )
    if key not in access._scientific_cache:
        card_key = (ADAPTER, "sdk202_literature_input", access._focal_key)
        if card_key not in access._scientific_cache:
            access._scientific_cache[card_key] = _CapturedCard(access._focal)
        with native_request(method):
            access._scientific_cache[key] = deepcopy(
                getattr(access._scientific_cache[card_key], method)(*args, **kwargs)
            )
    return access._scientific_cache[key]


def materialize(access, options=None):
    options = options_for_bioactivities(options)
    if access.mode == "live" and _original._guard(access) is None:
        _native(access, "literature")
    return _original.materialize(access, options)
