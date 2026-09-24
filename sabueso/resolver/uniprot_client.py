"""Moved to ``sabueso.tools.db.uniprot`` (uibcdf/sabueso#49); kept as an alias until 1.0."""

from sabueso.tools.db.uniprot import (  # noqa: F401
    SEARCH_FIELDS,
    SEARCH_SIZE,
    UNIPROT_REST,
    FixtureUniProtClient,
    OnlineUniProtClient,
    search_key,
    search_query,
)
