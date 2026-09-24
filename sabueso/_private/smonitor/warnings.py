"""Catalog warnings: outcomes users need to see (uibcdf/sabueso#31)."""

from __future__ import annotations

from typing import Any

from smonitor.integrations import CatalogWarning

from .catalog import CATALOG, META


class SabuesoWarning(CatalogWarning):
    """Base class of Sabueso's catalog warnings."""


class EnrichmentFailedWarning(SabuesoWarning):
    """A source could not be consulted; the result was built without it."""

    catalog_key = "EnrichmentFailedWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        source: str | None = None,
        subject: str | None = None,
        detail: str | None = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {"source": source, "subject": subject, "detail": detail}
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )


class EnrichmentTruncatedWarning(SabuesoWarning):
    """A source returned fewer records than it holds."""

    catalog_key = "EnrichmentTruncatedWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        source: str | None = None,
        subject: str | None = None,
        count: Any = None,
        total: Any = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {
                "source": source,
                "subject": subject,
                "count": count,
                "total": total,
            }
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )


class UnanchoredRecordsWarning(SabuesoWarning):
    """Records without a standard InChIKey were left out of a deck."""

    catalog_key = "UnanchoredRecordsWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        subject: str | None = None,
        count: Any = None,
        examples: str | None = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {"subject": subject, "count": count, "examples": examples}
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )


class CuratedDisagreementWarning(SabuesoWarning):
    """A curated literature assertion differs from other sources (uibcdf/sabueso#41)."""

    catalog_key = "CuratedDisagreementWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        subject: str | None = None,
        field: str | None = None,
        publication: str | None = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {"subject": subject, "field": field, "publication": publication}
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )


class DeprecatedUsageWarning(SabuesoWarning, FutureWarning):
    """A deprecated function was called; it will be removed before 1.0 (#49).

    Also a FutureWarning, so Python shows it to end users by default.
    """

    catalog_key = "DeprecatedUsageWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        function: str | None = None,
        replacement: str | None = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {"function": function, "replacement": replacement}
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )


class NewerCardSchemaWarning(SabuesoWarning):
    """A card written with a newer schema of this line was read (#42)."""

    catalog_key = "NewerCardSchemaWarning"

    def __init__(
        self,
        message: str | None = None,
        *,
        card: str | None = None,
        schema: str | None = None,
    ) -> None:
        extra = None
        if message is None:
            extra = {"card": card, "schema": schema}
        super().__init__(
            message,
            catalog=CATALOG if extra else None,
            meta=META if extra else None,
            extra=extra,
        )
