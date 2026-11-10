"""Frozen selected assertion value access; creates no source statements."""

from __future__ import annotations

from typing import Any, Dict

SourceAssertion = Dict[str, Any]


def assertion_value(assertion: SourceAssertion) -> Any:
    """Value used for resolution: the normalized value when present, else the asserted one."""
    if "normalized_value" in assertion:
        return assertion["normalized_value"]
    return assertion.get("asserted_value")
