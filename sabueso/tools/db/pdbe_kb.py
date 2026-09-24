"""PDBe-KB ligand binding sites (uibcdf/sabueso#28) and interface residues (#40) of a
protein.

PDBe-KB aggregates, over all PDB structures of a UniProt protein, the residues that each
ligand contacts. Positions are stated in UniProt numbering, with the entries, entities
and chains where each contact is observed. Sabueso records them as ``has_ligand_site``
relationships (``mappings/pdbe_kb.py``) through
``resolve_protein_card(..., ligand_sites=True)``.

``interface_residues(accession)`` is the same for the residues PDBe-KB reports at the
protein's interfaces with other polymer chains, per partner protein
(``has_interface_with``, ``resolve_protein_card(..., interfaces=True)``). PDBe-KB derives
them from the structures (PISA); Sabueso records them as PDBe-KB states them.

``ligand_sites(accession)`` returns ``{accession, retrieved_at, record}``, where
``record`` is PDBe-KB's record for that accession (``sequence``, ``length``, ``dataType``
and ``data``). ``OnlinePDBeKBClient`` queries the PDBe graph API;
``FixturePDBeKBClient`` reads ``<directory>/pdbe_kb/ligand_sites__<accession>.json``. Both
raise ``RecordNotFoundError`` when PDBe-KB holds no ligand sites for the protein (the API
answers 404) and ``ConnectorError`` on failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sabueso.core.errors import ConnectorError, RecordNotFoundError

PDBE_GRAPH_API = "https://www.ebi.ac.uk/pdbe/graph-api"


#: PDBe-KB data kinds: the graph API path and what a missing record means.
KINDS = {
    "ligand_sites": "ligand sites",
    "interface_residues": "interface residues",
}


class OnlinePDBeKBClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def _fetch(self, kind: str, accession: str) -> Dict[str, Any]:
        url = f"{PDBE_GRAPH_API}/uniprot/{kind}/{accession}"
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        missing = f"PDBe-KB has no {KINDS[kind]} for {accession}"
        try:
            with urlopen(url, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise RecordNotFoundError(missing) from exc
            raise ConnectorError(
                f"PDBe-KB request for {accession} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(
                f"PDBe-KB request for {accession} failed: {exc}"
            ) from exc
        record = data.get(accession)
        if not record:
            raise RecordNotFoundError(missing)
        return {"accession": accession, "retrieved_at": retrieved_at, "record": record}

    def ligand_sites(self, accession: str) -> Dict[str, Any]:
        return self._fetch("ligand_sites", accession)

    def interface_residues(self, accession: str) -> Dict[str, Any]:
        return self._fetch("interface_residues", accession)


class FixturePDBeKBClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def _read(self, kind: str, accession: str) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(f"PDBe-KB request for {accession} failed (simulated)")
        path = self.directory / "pdbe_kb" / f"{kind}__{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"PDBe-KB has no {KINDS[kind]} for {accession}")
        record = json.loads(path.read_text(encoding="utf-8"))
        return {
            "accession": accession,
            "retrieved_at": self.retrieved_at,
            "record": record,
        }

    def ligand_sites(self, accession: str) -> Dict[str, Any]:
        return self._read("ligand_sites", accession)

    def interface_residues(self, accession: str) -> Dict[str, Any]:
        return self._read("interface_residues", accession)
