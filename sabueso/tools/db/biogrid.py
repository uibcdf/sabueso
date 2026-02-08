"""BioGRID database tools (minimal)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib.parse import quote
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.biogrid import map_biogrid_interactions


def fetch_biogrid_interactions(gene: str, tax_id: int = 9606, access_key: str | None = None) -> Dict[str, Any]:
    """Fetch BioGRID interactions JSON by gene symbol."""
    key = access_key or os.getenv("BIOGRID_ACCESS_KEY")
    if not key:
        raise ValueError("BIOGRID_ACCESS_KEY is required for online BioGRID access")

    gene_enc = quote(gene)
    url = (
        "https://webservice.thebiogrid.org/interactions/?"
        f"accesskey={key}&format=json&geneList={gene_enc}&taxId={tax_id}"
    )
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        return json.loads(resp.read().decode("utf-8"))


def create_biogrid_card_online(gene: str, retrieved_at: str, tax_id: int = 9606, access_key: str | None = None) -> Any:
    data = fetch_biogrid_interactions(gene, tax_id=tax_id, access_key=access_key)
    mapping = map_biogrid_interactions(data, query_name=gene, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})
