"""InterPro database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.interpro import map_interpro_domains


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_interpro_card_from_json(interpro_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_interpro_domains(interpro_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_interpro_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_interpro_card_from_json(load_json(path), retrieved_at=retrieved_at)


def fetch_interpro_entry(ipr_id: str) -> Dict[str, Any]:
    url = f"https://www.ebi.ac.uk/interpro/api/entry/interpro/{ipr_id}"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_interpro_card_online(ipr_id: str, retrieved_at: str) -> Any:
    data = fetch_interpro_entry(ipr_id)
    return create_interpro_card_from_json(data, retrieved_at=retrieved_at)
