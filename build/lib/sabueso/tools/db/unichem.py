"""UniChem cross-references of a chemical structure (uibcdf/sabueso#25).

UniChem (EMBL-EBI) groups the records that many chemistry resources hold for one
standard InChI. Given a standard InChIKey, it lists the compound records of ChEMBL,
PubChem, DrugBank, the PDB chemical components, BindingDB and others. Sabueso uses it to
connect a small molecule with its records in sources that it has not queried directly
(``sabueso.tools.card.small_molecule``).

``compound(inchikey)`` returns ``{retrieved_at, compound}``, where ``compound`` holds
``uci`` (the UniChem compound id), ``standardInchiKey`` and ``sources`` (``id``,
``shortName``, ``compoundId``). ``OnlineUniChemClient`` queries the UniChem REST API;
``FixtureUniChemClient`` reads ``<directory>/unichem/<INCHIKEY>.json``. Both raise
``RecordNotFoundError`` when UniChem holds no such structure and ``ConnectorError`` on
failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sabueso.core.errors import ConnectorError, RecordNotFoundError

UNICHEM_API = "https://www.ebi.ac.uk/unichem/api/v1/compounds"
SOURCE_FIELDS = ("id", "shortName", "compoundId")


def _compound(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "uci": record.get("uci"),
        "standardInchiKey": record.get("standardInchiKey"),
        "inchi": (record.get("inchi") or {}).get("inchi"),
        "sources": sorted(
            ({k: s.get(k) for k in SOURCE_FIELDS} for s in record.get("sources") or []),
            key=lambda s: (s["id"] or 0, str(s["compoundId"])),
        ),
    }


class OnlineUniChemClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def compound(self, inchikey: str) -> Dict[str, Any]:
        body = json.dumps({"type": "inchikey", "compound": inchikey}).encode("utf-8")
        request = Request(
            UNICHEM_API, data=body, headers={"Content-Type": "application/json"}
        )
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(
                f"UniChem request for {inchikey} failed: {exc}"
            ) from exc
        compounds = data.get("compounds") or []
        if not compounds:
            raise RecordNotFoundError(f"UniChem has no compound {inchikey}")
        return {"retrieved_at": retrieved_at, "compound": _compound(compounds[0])}


class FixtureUniChemClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def compound(self, inchikey: str) -> Dict[str, Any]:
        if inchikey in self.failing:
            raise ConnectorError(f"UniChem request for {inchikey} failed (simulated)")
        path = self.directory / "unichem" / f"{inchikey}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"UniChem has no compound {inchikey}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {"retrieved_at": self.retrieved_at, "compound": saved}
