"""CATH database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import Request, urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.cath import map_cath_domains


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_cath_card_from_json(cath_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_cath_domains(cath_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_cath_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_cath_card_from_json(load_json(path), retrieved_at=retrieved_at)


def fetch_cath_domain(domain_id: str) -> Dict[str, Any]:
    url = f"https://www.cathdb.info/version/v4_3_0/api/rest/domain_summary/{domain_id}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_cath_card_online(domain_id: str, retrieved_at: str) -> Any:
    data = fetch_cath_domain(domain_id)
    return create_cath_card_from_json(data, retrieved_at=retrieved_at)
