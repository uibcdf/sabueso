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


class ArgumentError(SabuesoError, ValueError):
    """An argument of a public function has a value the function cannot accept.

    Raised by the ArgDigest digesters in ``sabueso/_private/argdigest/argument/``
    (uibcdf/sabueso#31), before the function runs: a wrong value is refused rather than
    turned into a plausible wrong result. It is also a ValueError, which is what it is.
    """

    catalog_key = "ArgumentError"

    def __init__(
        self,
        message: str | None = None,
        *,
        argument: str | None = None,
        value: Any = None,
        caller: str | None = None,
        reason: str | None = None,
    ) -> None:
        if message is None:
            where = f" of {caller}" if caller else ""
            why = f": {reason}" if reason else ""
            message = f"Argument {argument!r}{where} cannot take {value!r}{why}."
        super().__init__(message, extra={"argument": argument, "caller": caller})


class LibraryNotFoundError(SabuesoError, ImportError):
    """An optional library a function needs is not installed (DepDigest, #46).

    Raised by ``@dep_digest`` with the library, the caller and install hints; also an
    ImportError, which is what it is.
    """

    catalog_key = "LibraryNotFoundError"

    def __init__(
        self,
        message: str | None = None,
        *,
        library: str | None = None,
        caller: str | None = None,
    ) -> None:
        if message is None:
            where = f" for {caller}" if caller else ""
            message = f"The optional library {library!r} is required{where}."
        super().__init__(message, extra={"library": library, "caller": caller})
