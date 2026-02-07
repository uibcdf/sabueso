"""UniProt database tools (minimal)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.uniprot import map_protein


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load UniProt JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def create_protein_card_from_json(uniprot_json: Dict[str, Any], retrieved_at: str | None = None) -> Any:
    """Create a Protein Card from UniProt JSON (offline)."""
    mapping = map_protein(uniprot_json, retrieved_at=retrieved_at or _now_date())
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_protein_card_from_file(path: str | Path, retrieved_at: str | None = None) -> Any:
    """Create a Protein Card from a UniProt JSON file."""
    return create_protein_card_from_json(load_json(path), retrieved_at=retrieved_at)


def create_protein_card(uniprot_id: str, retrieved_at: str | None = None, data_dir: str | Path = "temp_data") -> Any:
    """
    Create a Protein Card by UniProt ID using a local JSON fixture.

    This is an offline helper. It expects a file named <ID>.json in data_dir.
    """
    path = Path(data_dir) / f"{uniprot_id}.json"
    return create_protein_card_from_file(path, retrieved_at=retrieved_at)


def fetch_uniprot_json(uniprot_id: str) -> Dict[str, Any]:
    """Fetch UniProt JSON online by accession."""
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_protein_card_online(uniprot_id: str, retrieved_at: str | None = None) -> Any:
    """Create a Protein Card by UniProt ID using online fetch."""
    data = fetch_uniprot_json(uniprot_id)
    return create_protein_card_from_json(data, retrieved_at=retrieved_at)
