"""Tell users about outcomes already recorded as data (uibcdf/sabueso#31).

Cards and decks record every source outcome (``quality.enrichments``,
``deck.meta["sources"]``). The diagnostics are derived from those same records, so what a
user is told and what the result stores cannot diverge.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .emitter import warn
from .warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
    UnanchoredRecordsWarning,
)

# Point warnings at the user's call: report_* <- public API function <- @signal wrapper
# <- caller. The wrapper frame is counted by hand; drop it once uibcdf/smonitor#23 lets
# SMonitor skip its own frames.
_CALLER = 4


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
                stacklevel=_CALLER,
            )
        for error in record.get("errors") or []:
            warn(
                EnrichmentFailedWarning(
                    source=source,
                    subject=error.get("inchikey") or subject,
                    detail=error.get("detail") or "",
                ),
                stacklevel=_CALLER,
            )
        if record.get("truncated"):
            warn(
                EnrichmentTruncatedWarning(
                    source=source,
                    subject=subject,
                    count=record.get("count"),
                    total=record.get("total_count"),
                ),
                stacklevel=_CALLER,
            )


def report_unanchored(unanchored: List[Dict[str, Any]], subject: str) -> None:
    """Warn when records could not be identified and were left out."""
    if not unanchored:
        return
    refs = [u.get("ref") for u in unanchored]
    examples = ", ".join(refs[:5]) + (", ..." if len(refs) > 5 else "")
    warn(
        UnanchoredRecordsWarning(subject=subject, count=len(refs), examples=examples),
        stacklevel=_CALLER,
    )
