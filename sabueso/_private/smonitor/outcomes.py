"""Tell users about outcomes already recorded as data (uibcdf/sabueso#31).

Cards and decks record every source outcome (``quality.enrichments``,
``deck.meta["sources"]``). The diagnostics are derived from those same records, so what a
user is told and what the result stores cannot diverge.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterable, List

from .emitter import warn
from .warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
    UnanchoredRecordsWarning,
)

# Warnings point at the user's call. Between it and report_* sit Sabueso's public
# function and the wrappers of @signal (SMonitor) and @arg_digest (ArgDigest); their depth
# is theirs to change, so it is measured, not counted by hand. A hand-counted constant
# broke the day ArgDigest's wrapper was added. Drop this once uibcdf/smonitor#23 and its
# ArgDigest counterpart let the libraries skip their own frames.
_INTERNAL = ("sabueso", "smonitor", "argdigest")


def _user_stacklevel() -> int:
    """``stacklevel`` for ``warn`` called in a report_* function: the first frame outside
    Sabueso, SMonitor and ArgDigest."""
    frame = sys._getframe(2)  # skip this helper and the report_* function
    level = 2  # warn()'s stacklevel counts from the report_* function's caller
    while frame is not None:
        module = frame.f_globals.get("__name__", "")
        if module.split(".", 1)[0] not in _INTERNAL:
            return level
        frame = frame.f_back
        level += 1
    return 2


def report_outcomes(records: Iterable[Dict[str, Any]], subject: str) -> None:
    """Warn about failed and truncated source outcomes. ``not_found`` is an answer,
    recorded as data, and is not a diagnostic."""
    for record in records:
        source = record.get("source") or "A source"
        if record.get("status") == "error":
            warn(
                EnrichmentFailedWarning(
                    source=source, subject=subject, detail=record.get("detail") or ""
                ),
                stacklevel=_user_stacklevel(),
            )
        for error in record.get("errors") or []:
            warn(
                EnrichmentFailedWarning(
                    source=source,
                    subject=error.get("inchikey") or subject,
                    detail=error.get("detail") or "",
                ),
                stacklevel=_user_stacklevel(),
            )
        if record.get("truncated"):
            warn(
                EnrichmentTruncatedWarning(
                    source=source,
                    subject=subject,
                    count=record.get("count"),
                    total=record.get("total_count"),
                ),
                stacklevel=_user_stacklevel(),
            )


def report_unanchored(unanchored: List[Dict[str, Any]], subject: str) -> None:
    """Warn when records could not be identified and were left out."""
    if not unanchored:
        return
    refs = [u.get("ref") for u in unanchored]
    examples = ", ".join(refs[:5]) + (", ..." if len(refs) > 5 else "")
    warn(
        UnanchoredRecordsWarning(subject=subject, count=len(refs), examples=examples),
        stacklevel=_user_stacklevel(),
    )
