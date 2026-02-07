"""ChEMBL database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.chembl import map_molecule


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load ChEMBL JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_molecule_card_from_json(chembl_json: Dict[str, Any], retrieved_at: str) -> Any:
    """Create a SmallMolecule Card from ChEMBL JSON (offline)."""
    mapping = map_molecule(chembl_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "small_molecule"})


def create_molecule_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    """Create a SmallMolecule Card from a ChEMBL JSON file."""
    return create_molecule_card_from_json(load_json(path), retrieved_at=retrieved_at)


def fetch_chembl_json(chembl_id: str) -> Dict[str, Any]:
    """Fetch ChEMBL molecule JSON online by ChEMBL ID."""
    url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{chembl_id}.json"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_molecule_card_online(chembl_id: str, retrieved_at: str) -> Any:
    """Create a SmallMolecule Card by ChEMBL ID using online fetch."""
    data = fetch_chembl_json(chembl_id)
    return create_molecule_card_from_json(data, retrieved_at=retrieved_at)
