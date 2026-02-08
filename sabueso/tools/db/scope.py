"""SCOPe database tools (minimal)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable
from urllib.request import urlopen

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.scope import map_scope_domains

DEFAULT_SCOPE_DUMP_URL = (
    "https://zenodo.org/records/5829561/files/dir.des.scope.2.08-stable.txt?download=1"
)


def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_scope_card_from_json(scope_json: Dict[str, Any], retrieved_at: str) -> Any:
    mapping = map_scope_domains(scope_json, retrieved_at=retrieved_at)
    return build_card_from_mapping(mapping, meta={"entity_type": "protein"})


def create_scope_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    return create_scope_card_from_json(load_json(path), retrieved_at=retrieved_at)


def _iter_scope_dump_lines(url: str) -> Iterable[str]:
    with urlopen(url) as resp:  # nosec - expected trusted endpoint
        for raw in resp:
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line or line.startswith("#"):
                continue
            yield line


def _parse_scope_dump(sunid: str, lines: Iterable[str]) -> Dict[str, Any]:
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        if parts[0] == str(sunid):
            return {
                "sunid": parts[0],
                "type": parts[1],
                "sccs": parts[2],
                "sid": parts[3],
                "name": parts[4],
            }
    raise KeyError(f"SCOPe SUNID not found in dump: {sunid}")


def fetch_scope_entry(sunid: str) -> Dict[str, Any]:
    dump_path = os.environ.get("SCOPE_DUMP_PATH")
    if dump_path:
        text = Path(dump_path).read_text(encoding="utf-8")
        return _parse_scope_dump(sunid, (l for l in text.splitlines()))

    dump_url = os.environ.get("SCOPE_DUMP_URL", DEFAULT_SCOPE_DUMP_URL)
    lines = _iter_scope_dump_lines(dump_url)
    return _parse_scope_dump(sunid, lines)


def create_scope_card_online(sunid: str, retrieved_at: str) -> Any:
    data = fetch_scope_entry(sunid)
    return create_scope_card_from_json(data, retrieved_at=retrieved_at)
