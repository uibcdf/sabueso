"""Core exception types for Sabueso."""


class SabuesoError(Exception):
    """Base error for Sabueso."""


class ResolverError(SabuesoError):
    """Resolver failed to select or normalize values."""


class SchemaError(SabuesoError):
    """Schema mismatch or validation failure."""


class StorageError(SabuesoError):
    """Persistence/storage failure."""


class ConnectorError(SabuesoError):
    """External data source or connector failure."""


class RecordNotFoundError(SabuesoError):
    """A source was consulted and holds no record for the requested identifier.

    Distinct from ConnectorError: "not found" is an answer, a connector failure is not.
    """
