"""Core exception types for Sabueso.

They are SMonitor catalog exceptions (uibcdf/sabueso#31): each keeps the message written
where it is raised, and gains a stable code (``exc.code``) and structured context
(``exc.extra``) from ``sabueso/_private/smonitor/catalog.py``.
"""

from __future__ import annotations

from typing import Any, Dict

from smonitor.integrations import CatalogException

from sabueso._private.smonitor.catalog import CATALOG, META


class SabuesoError(CatalogException):
    """Base error for Sabueso."""

    catalog_key = "SabuesoError"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        extra: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, extra=extra, catalog=CATALOG, meta=META)


class ResolverError(SabuesoError):
    """Resolver failed to select or normalize values."""

    catalog_key = "ResolverError"


class SchemaError(SabuesoError):
    """Schema mismatch or validation failure."""

    catalog_key = "SchemaError"


class StorageError(SabuesoError):
    """Persistence/storage failure."""

    catalog_key = "StorageError"


class ConnectorError(SabuesoError):
    """External data source or connector failure."""

    catalog_key = "ConnectorError"


class RecordNotFoundError(SabuesoError):
    """A source was consulted and holds no record for the requested identifier.

    Distinct from ConnectorError: "not found" is an answer, a connector failure is not.
    """

    catalog_key = "RecordNotFoundError"
