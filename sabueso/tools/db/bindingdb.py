"""BindingDB measured affinities of a protein (uibcdf/sabueso#66).

BindingDB curates binding affinities (Ki, Kd, IC50, EC50) from the literature and
patents, and imports part of ChEMBL. Its REST service, keyed by UniProt accession,
returns per record the monomer id, SMILES, affinity type, value in nanomolar (the
relation, if any, written in the value: ``">1.00e+5"``), PubMed id and DOI. It does not
state where a record came from (BindingDB curation or a ChEMBL import); the bulk
download does. So records from this service are compared with other sources by their
statement (``sabueso.core.measurements``), never by declared provenance.

Licence: data curated by BindingDB is CC BY 3.0, and data imported from ChEMBL keeps
ChEMBL's CC BY-SA 3.0. Records from this service carry no origin, so Sabueso treats
them as CC BY-SA 3.0.

``ligands(accession, cutoff)`` returns ``{accession, retrieved_at, record}`` with the
list of affinities. ``OnlineBindingDBClient`` queries the REST service;
``FixtureBindingDBClient`` reads ``<directory>/bindingdb/<accession>.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record

BINDINGDB_REST = "https://bindingdb.org/rest/getLigandsByUniprots"
#: No affinity cutoff by default (nanomolar): every record is kept, weak ones included.
DEFAULT_CUTOFF = 100_000_000


def _affinities(data: Dict[str, Any]) -> list:
    return (data.get("getLindsByUniprotsResponse") or {}).get("affinities") or []


class OnlineBindingDBClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    def ligands(self, accession: str, cutoff: float = DEFAULT_CUTOFF) -> Dict[str, Any]:
        query = urlencode(
            {"uniprot": accession, "cutoff": cutoff, "response": "application/json"}
        )
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(f"{BINDINGDB_REST}?{query}", timeout=self.timeout) as resp:  # nosec
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(
                f"BindingDB request for {accession} failed: {exc}"
            ) from exc
        records = _affinities(data)
        if not records:
            raise RecordNotFoundError(f"BindingDB has no affinities for {accession}")
        return {"accession": accession, "retrieved_at": retrieved_at, "record": records}


class FixtureBindingDBClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def ligands(self, accession: str, cutoff: float = DEFAULT_CUTOFF) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(
                f"BindingDB request for {accession} failed (simulated)"
            )
        path = self.directory / "bindingdb" / f"{accession}.json"
        records = (
            _affinities(json.loads(path.read_text(encoding="utf-8")))
            if path.is_file()
            else []
        )
        if not records:
            raise RecordNotFoundError(f"BindingDB has no affinities for {accession}")
        return {
            "accession": accession,
            "retrieved_at": self.retrieved_at,
            "record": records,
        }


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_affinities(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The affinities BindingDB holds for a UniProt protein."""
    response = online(client, OnlineBindingDBClient).ligands(identifier)
    return source_record(
        "BindingDB",
        "affinities",
        {"accession": identifier},
        response.get("retrieved_at"),
        None,
        response.get("record"),
    )
