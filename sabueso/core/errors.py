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
