"""InterPro site residues of a protein (uibcdf/sabueso#28).

InterPro member databases annotate sites inside their signatures, e.g. the catalytic
triad, substrate binding site and dimer interface of the CDD model ``cd00311`` for
triosephosphate isomerase. InterPro states them positioned on the protein's own
sequence: the source maps its family model onto the protein, so Sabueso records
positions and never aligns anything itself. They become
``features_positional.family_site`` (``mappings/interpro.py``) through
``resolve_protein_card(..., family_sites=True)``.

``site_residues(accession)`` returns ``{accession, retrieved_at, version, residues}``.
``OnlineInterProClient`` queries the InterPro API; ``FixtureInterProClient`` reads
``<directory>/interpro/residues__<accession>.json``. Both raise ``RecordNotFoundError``
when InterPro states no site residues (the API answers an empty object, also for an
unknown accession, so the two cannot be told apart) and ``ConnectorError`` on failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sabueso.core.errors import ConnectorError, RecordNotFoundError

INTERPRO_API = "https://www.ebi.ac.uk/interpro/api"
NO_RESIDUES = "InterPro states no site residues for {} (or does not know it)"


class OnlineInterProClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    def site_residues(self, accession: str) -> Dict[str, Any]:
        url = f"{INTERPRO_API}/protein/uniprot/{accession}/?residues"
        request = Request(url, headers={"Accept": "application/json"})
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                body = resp.read()
                version = resp.headers.get("InterPro-Version")
        except HTTPError as exc:
            if exc.code in (204, 404):
                raise RecordNotFoundError(NO_RESIDUES.format(accession)) from exc
            raise ConnectorError(
                f"InterPro request for {accession} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(
                f"InterPro request for {accession} failed: {exc}"
            ) from exc
        try:
            residues = json.loads(body) if body else {}
        except ValueError as exc:
            raise ConnectorError(
                f"InterPro request for {accession} failed: {exc}"
            ) from exc
        if not residues:
            raise RecordNotFoundError(NO_RESIDUES.format(accession))
        return {
            "accession": accession,
            "retrieved_at": retrieved_at,
            "version": version,
            "residues": residues,
        }


class FixtureInterProClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def site_residues(self, accession: str) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(f"InterPro request for {accession} failed (simulated)")
        path = self.directory / "interpro" / f"residues__{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(NO_RESIDUES.format(accession))
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {
            "accession": accession,
            "retrieved_at": self.retrieved_at,
            "version": saved.get("version"),
            "residues": saved["residues"],
        }
