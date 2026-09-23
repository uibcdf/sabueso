"""UniProtKB record access for entity resolution.

Two interchangeable clients return ``(entry, retrieved_at)``:
- ``OnlineUniProtClient`` queries the UniProt REST API;
- ``FixtureUniProtClient`` reads saved REST responses (offline tests, reproducibility).

Both raise ``RecordNotFoundError`` when UniProt holds no record and ``ConnectorError``
when the source cannot answer, so that callers never confuse "not found" with "failed".
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sabueso.core.errors import ConnectorError, RecordNotFoundError

UNIPROT_REST = "https://rest.uniprot.org/uniprotkb"


class OnlineUniProtClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch_entry(self, accession: str) -> Tuple[Dict[str, Any], str]:
        request = Request(
            f"{UNIPROT_REST}/{accession}.json", headers={"Accept": "application/json"}
        )
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                return json.loads(resp.read().decode("utf-8")), retrieved_at
        except HTTPError as exc:
            if exc.code == 404:
                raise RecordNotFoundError(f"UniProt has no record {accession}") from exc
            raise ConnectorError(
                f"UniProt request for {accession} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(
                f"UniProt request for {accession} failed: {exc}"
            ) from exc


class FixtureUniProtClient:
    """Serve saved UniProt REST responses from ``<directory>/<accession>.json``."""

    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def fetch_entry(self, accession: str) -> Tuple[Dict[str, Any], str]:
        if accession in self.failing:
            raise ConnectorError(f"UniProt request for {accession} failed (simulated)")
        path = self.directory / f"{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"UniProt has no record {accession}")
        return json.loads(path.read_text(encoding="utf-8")), self.retrieved_at
