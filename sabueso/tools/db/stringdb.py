"""STRING database tools (minimal)."""

from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib.parse import quote
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.stringdb import map_string_interactions


def fetch_string_network(identifiers: str, species: int = 9606) -> List[Dict[str, Any]]:
    """Fetch STRING network JSON by identifier."""
    ident = quote(identifiers)
    url = f"https://string-db.org/api/json/network?identifiers={ident}&species={species}"
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_string_card_online(identifiers: str, retrieved_at: str | None = None, species: int = 9606) -> Any:
    from datetime import datetime, timezone

    def _now_date() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    data = fetch_string_network(identifiers, species=species)
    mapping = map_string_interactions(data, query_name=identifiers, retrieved_at=retrieved_at or _now_date())
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})
