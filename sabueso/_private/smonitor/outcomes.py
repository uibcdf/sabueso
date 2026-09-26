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
    CuratedDisagreementWarning,
    DeprecatedUsageWarning,
    EnrichmentFailedWarning,
    EnrichmentPartialWarning,
    EnrichmentTruncatedWarning,
    NewerCardSchemaWarning,
    UnanchoredRecordsWarning,
)

# Warnings point at the user's call. Between it and report_* sit Sabueso's public
# function and the wrappers of @signal (SMonitor) and @arg_digest (ArgDigest); their depth
# is theirs to change, so it is measured, not counted by hand. A hand-counted constant
# broke the day ArgDigest's wrapper was added.
#
# Since SMonitor 0.17.0 (uibcdf/smonitor#23), DiagnosticBundle.warn skips SMonitor's own
# frames when it applies ``stacklevel``. So SMonitor frames are passed over here without
# being counted. Sabueso's and ArgDigest's frames are still counted until ArgDigest offers
# the same.
_SKIPPED_BY_SMONITOR = ("smonitor",)
_INTERNAL = ("sabueso", "smonitor", "argdigest")


def _user_stacklevel() -> int:
    """``stacklevel`` for ``warn`` called in a report_* function: the first frame outside
    Sabueso, SMonitor and ArgDigest, counted as SMonitor >= 0.17 counts (its own frames
    excluded)."""
    frame = sys._getframe(2)  # skip this helper and the report_* function
    level = 2  # warn()'s stacklevel counts from the report_* function's caller
    while frame is not None:
        package = frame.f_globals.get("__name__", "").split(".", 1)[0]
        if package not in _INTERNAL:
            return level
        frame = frame.f_back
        if (
            frame is not None
            and frame.f_globals.get("__name__", "").split(".", 1)[0]
            not in _SKIPPED_BY_SMONITOR
        ):
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
        if record.get("status") == "partial":
            warn(
                EnrichmentPartialWarning(
                    source=source,
                    subject=(
                        f"{subject} ({record['structure']})"
                        if record.get("structure")
                        else subject
                    ),
                    missing=", ".join(record.get("missing") or []),
                    detail=record.get("detail") or "",
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


def report_curated_disagreement(subject: str, field: str, publication: str) -> None:
    """Warn that a curated assertion disagrees; the conflict is already recorded."""
    warn(
        CuratedDisagreementWarning(
            subject=subject, field=field, publication=publication
        ),
        stacklevel=_user_stacklevel(),
    )


def report_deprecated(function: str, replacement: str) -> None:
    """Warn that a deprecated function was called, and what to use instead."""
    warn(
        DeprecatedUsageWarning(function=function, replacement=replacement),
        stacklevel=_user_stacklevel(),
    )


def report_newer_schema(card: str, schema: str) -> None:
    """Warn that a card from a newer Sabueso was read."""
    warn(
        NewerCardSchemaWarning(card=card, schema=schema), stacklevel=_user_stacklevel()
    )
