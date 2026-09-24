"""PDB Chemical Component Dictionary (CCD) records of structure ligands (uibcdf/sabueso#25).

A structure lists its ligands by chemical-component code (e.g. ``BTS``, ``SO4``). The
wwPDB Chemical Component Dictionary gives each code its chemistry: name, formula, type,
SMILES and a standard InChI/InChIKey. That InChIKey is what lets a structure ligand be
recognised as the same molecule that other sources describe
(``sabueso.tools.card.small_molecule``).

``components(comp_ids)`` returns ``{retrieved_at, components, missing}``: the records found,
keyed by code, and the requested codes that the CCD does not hold. RCSB omits unknown
codes from a batch without an error, so ``missing`` is computed, never assumed empty.
``OnlineCCDClient`` queries the RCSB GraphQL service; ``FixtureCCDClient`` reads
``<directory>/pdb_ccd/<CODE>.json``. Both raise ``ConnectorError`` on failures.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sabueso.core.errors import ConnectorError

RCSB_GRAPHQL = "https://data.rcsb.org/graphql"
COMPONENTS_QUERY = """query($ids: [String!]!) { chem_comps(comp_ids: $ids) {
  chem_comp { id name formula type formula_weight pdbx_release_status }
  rcsb_chem_comp_descriptor { InChI InChIKey SMILES SMILES_stereo }
} }"""


def _codes(comp_ids: Iterable[str]) -> List[str]:
    return sorted({c.upper() for c in comp_ids if c})


class OnlineCCDClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def components(self, comp_ids: Iterable[str]) -> Dict[str, Any]:
        codes = _codes(comp_ids)
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not codes:
            return {"retrieved_at": retrieved_at, "components": {}, "missing": []}
        body = json.dumps(
            {"query": COMPONENTS_QUERY, "variables": {"ids": codes}}
        ).encode("utf-8")
        request = Request(
            RCSB_GRAPHQL, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"CCD request for {codes} failed: {exc}") from exc
        if data.get("errors"):
            raise ConnectorError(f"CCD request for {codes} failed: {data['errors']}")
        found = {
            record["chem_comp"]["id"]: record
            for record in (data.get("data") or {}).get("chem_comps") or []
            if record and record.get("chem_comp")
        }
        return {
            "retrieved_at": retrieved_at,
            "components": found,
            "missing": [c for c in codes if c not in found],
        }


class FixtureCCDClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def components(self, comp_ids: Iterable[str]) -> Dict[str, Any]:
        codes = _codes(comp_ids)
        if self.failing & set(codes):
            raise ConnectorError(f"CCD request for {codes} failed (simulated)")
        found: Dict[str, Any] = {}
        for code in codes:
            path = self.directory / "pdb_ccd" / f"{code}.json"
            if path.is_file():
                found[code] = json.loads(path.read_text(encoding="utf-8"))
        return {
            "retrieved_at": self.retrieved_at,
            "components": found,
            "missing": [c for c in codes if c not in found],
        }
