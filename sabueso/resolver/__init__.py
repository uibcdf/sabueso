"""Resolver utilities."""

from .entity_resolver import (
    EntityQuery,
    EntityResolution,
    EntityResolver,
    sequence_identity_link,
)
from .field_resolver import resolve_field
from .loader import load_selection_rules
from .uniprot_client import FixtureUniProtClient, OnlineUniProtClient

__all__ = [
    "EntityQuery",
    "EntityResolution",
    "EntityResolver",
    "FixtureUniProtClient",
    "OnlineUniProtClient",
    "load_selection_rules",
    "resolve_field",
    "sequence_identity_link",
]
