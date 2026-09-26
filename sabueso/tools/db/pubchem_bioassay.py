"""PubChem BioAssay: the assays PubChem links to a protein (uibcdf/sabueso#68).

Many PubChem assays are deposited by other databases, ChEMBL and BindingDB above all,
and state it: ``SourceName`` and ``SourceID`` name the depositor and its own assay id.
Sabueso records such data as copies with a declared origin (``copy_of``). They are
pointers: grouped with the original when the card holds it, and leading to it when it
does not. They are never counted as independent confirmations.

``assays(accession)`` returns ``{accession, retrieved_at, record}``, where ``record``
holds:

- ``aids``: the assay ids linked to the protein;
- ``summaries``: per assay, the name, depositor and its assay id;
- ``concise``: per assay, the table of results. Each row holds the SID, the CID, the
  outcome, the target accession, the value in µM, the activity name and the PubMed id.
  The relation of a value (``>``) is not in this table;
- ``inchikeys``: the InChIKey PubChem states for each CID, so molecules are anchored
  without computing anything.

``OnlinePubChemBioAssayClient`` queries PUG REST; ``FixturePubChemBioAssayClient`` reads
``<directory>/pubchem_bioassay/<accession>.json``.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
#: PubChem asks for no more than five requests per second.
PAUSE = 0.25


class OnlinePubChemBioAssayClient:
    def __init__(self, timeout: float = 90.0) -> None:
        self.timeout = timeout

    def _get(self, path: str) -> Dict[str, Any]:
        try:
            with urlopen(f"{PUG}/{path}", timeout=self.timeout) as resp:  # nosec
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise RecordNotFoundError(f"PubChem has no {path}") from exc
            raise ConnectorError(
                f"PubChem request {path} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"PubChem request {path} failed: {exc}") from exc
        time.sleep(PAUSE)
        return data

    def assays(self, accession: str) -> Dict[str, Any]:
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        info = self._get(f"protein/accession/{accession}/aids/JSON")
        aids = info["InformationList"]["Information"][0].get("AID") or []
        if not aids:
            raise RecordNotFoundError(f"PubChem links no assay to {accession}")
        summaries = []
        for i in range(0, len(aids), 50):
            chunk = ",".join(map(str, aids[i : i + 50]))
            summaries += self._get(f"assay/aid/{chunk}/summary/JSON")["AssaySummaries"][
                "AssaySummary"
            ]
        concise = {
            aid: self._get(f"assay/aid/{aid}/concise/JSON")["Table"] for aid in aids
        }
        cids = sorted(
            {
                row["Cell"][2]
                for t in concise.values()
                for row in t.get("Row") or []
                if row["Cell"][2]
            }
        )
        inchikeys: Dict[str, str] = {}
        for i in range(0, len(cids), 100):
            chunk = ",".join(cids[i : i + 100])
            table = self._get(f"compound/cid/{chunk}/property/InChIKey/JSON")
            for prop in table["PropertyTable"]["Properties"]:
                inchikeys[str(prop["CID"])] = prop.get("InChIKey")
        return {
            "accession": accession,
            "retrieved_at": retrieved_at,
            "record": {
                "aids": aids,
                "summaries": summaries,
                "concise": {str(k): v for k, v in concise.items()},
                "inchikeys": inchikeys,
            },
        }


class FixturePubChemBioAssayClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def assays(self, accession: str) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(f"PubChem request for {accession} failed (simulated)")
        path = self.directory / "pubchem_bioassay" / f"{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"PubChem links no assay to {accession}")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["concise"] = {str(k): v for k, v in record["concise"].items()}
        return {
            "accession": accession,
            "retrieved_at": self.retrieved_at,
            "record": record,
        }


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_assays(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The assays PubChem links to a UniProt protein, with their depositors and results."""
    response = online(client, OnlinePubChemBioAssayClient).assays(identifier)
    return source_record(
        "PubChem BioAssay",
        "assays",
        {"accession": identifier},
        response.get("retrieved_at"),
        None,
        response.get("record"),
    )
