"""PhosphoSitePlus database tools (minimal)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.phosphositeplus import map_psp_ptm


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_psp_card_from_json(psp_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_psp_ptm(psp_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_psp_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_psp_card_from_json(load_json(path), retrieved_at=retrieved_at)
