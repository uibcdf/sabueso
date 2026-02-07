"""PDB (RCSB) database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.pdb import map_structure


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load PDB JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_structure_card_from_json(pdb_json: Dict[str, Any], pdb_id: str, retrieved_at: str) -> Any:
    """Create a Protein Card from PDB JSON (offline)."""
    mapping = map_structure(pdb_json, pdb_id=pdb_id, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_structure_card_from_file(path: str | Path, pdb_id: str, retrieved_at: str) -> Any:
    """Create a Protein Card from a PDB JSON file."""
    return create_structure_card_from_json(load_json(path), pdb_id=pdb_id, retrieved_at=retrieved_at)


def fetch_pdb_json(pdb_id: str) -> Dict[str, Any]:
    """Fetch PDB entry JSON online by PDB ID."""
    url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_structure_card_online(pdb_id: str, retrieved_at: str) -> Any:
    """Create a Protein Card by PDB ID using online fetch."""
    data = fetch_pdb_json(pdb_id)
    return create_structure_card_from_json(data, pdb_id=pdb_id, retrieved_at=retrieved_at)
