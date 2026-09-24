from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sabueso")
except PackageNotFoundError:
    # Package is not installed
    try:
        from ._version import __version__
    except ImportError:
        __version__ = "0.0.0+unknown"

from smonitor.integrations import ensure_configured as _ensure_smonitor_configured

from sabueso._private.smonitor import PACKAGE_ROOT as _SMONITOR_PACKAGE_ROOT
from sabueso.core.curation_store import CurationStore
from sabueso.core.errors import (
    ConnectorError,
    ResolverError,
    SabuesoError,
    SchemaError,
    StorageError,
)
from sabueso.core.tables import to_dataframe
from sabueso.tools.card.protein import ambiguity_deck, resolve_protein_card
from sabueso.tools.card.small_molecule import ligand_deck, resolve_molecule_card
from sabueso.tools.card.storage import save_card_json, save_card_sqlite
from sabueso.tools.db.chembl import (
    create_molecule_card_from_file,
    create_molecule_card_from_json,
    create_molecule_card_online,
)
from sabueso.tools.db.pubchem import (
    create_compound_card_from_file,
    create_compound_card_from_json,
    create_compound_card_online,
)
from sabueso.tools.db.uniprot import (
    create_protein_card,
    create_protein_card_from_file,
    create_protein_card_from_json,
    create_protein_card_online,
)
from sabueso.tools.deck.storage import save_deck_jsonl, save_deck_sqlite
from sabueso.tools.resolve import resolve

# SMonitor is configured when Sabueso is imported (uibcdf/sabueso#31).
_ensure_smonitor_configured(_SMONITOR_PACKAGE_ROOT)

__all__ = [
    "create_protein_card_from_file",
    "create_protein_card_from_json",
    "create_protein_card",
    "create_protein_card_online",
    "create_compound_card_from_file",
    "create_compound_card_from_json",
    "create_compound_card_online",
    "create_molecule_card_from_file",
    "create_molecule_card_from_json",
    "create_molecule_card_online",
    "resolve",
    "CurationStore",
    "to_dataframe",
    "resolve_protein_card",
    "resolve_molecule_card",
    "ligand_deck",
    "ambiguity_deck",
    "save_card_json",
    "save_card_sqlite",
    "save_deck_jsonl",
    "save_deck_sqlite",
    "SabuesoError",
    "ResolverError",
    "SchemaError",
    "StorageError",
    "ConnectorError",
]
