"""TED database tools (minimal)."""

from __future__ import annotations

import gzip
import io
import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.ted import map_ted_domains

DEFAULT_TED_DUMP_URL = (
    "https://zenodo.org/records/13908086/files/novel_folds_set.domain_summary.tsv.gz?download=1"
)


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_ted_card_from_json(ted_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_ted_domains(ted_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_ted_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_ted_card_from_json(load_json(path), retrieved_at=retrieved_at)


def _iter_ted_dump_lines(url: str):
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        raw = resp.read()
    text = gzip.GzipFile(fileobj=io.BytesIO(raw)).read().decode("utf-8", errors="ignore")
    for line in text.splitlines():
        if not line.strip():
            continue
        yield line


def _parse_ted_dump(entry_id: str, lines) -> Dict[str, Any]:
    for line in lines:
        parts = line.split("\t")
        if not parts:
            continue
        if parts[0] == entry_id:
            return {"domains": [{"id": entry_id, "name": entry_id}]}
    raise KeyError(f"TED entry not found in dump: {entry_id}")


def fetch_ted_entry(entry_id: str) -> Dict[str, Any]:
    dump_path = os.environ.get("TED_DUMP_PATH")
    if dump_path:
        raw = Path(dump_path).read_bytes()
        text = gzip.GzipFile(fileobj=io.BytesIO(raw)).read().decode("utf-8", errors="ignore")
        return _parse_ted_dump(entry_id, text.splitlines())

    dump_url = os.environ.get("TED_DUMP_URL", DEFAULT_TED_DUMP_URL)
    return _parse_ted_dump(entry_id, _iter_ted_dump_lines(dump_url))


def create_ted_card_online(entry_id: str, retrieved_at: str) -> Any:
    data = fetch_ted_entry(entry_id)
    return create_ted_card_from_json(data, retrieved_at=retrieved_at)
