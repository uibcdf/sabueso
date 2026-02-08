"""GO database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.go import map_go_terms


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_go_card_from_json(go_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_go_terms(go_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_go_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_go_card_from_json(load_json(path), retrieved_at=retrieved_at)


def fetch_go_term(go_id: str) -> Dict[str, Any]:
    url = f"https://api.geneontology.org/api/ontology/term/{go_id}"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_go_card_online(go_id: str, retrieved_at: str) -> Any:
    data = fetch_go_term(go_id)
    return create_go_card_from_json(data, retrieved_at=retrieved_at)
