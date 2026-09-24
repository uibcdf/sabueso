"""PubChem database tools (minimal)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load PubChem JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def create_compound_card_from_json(
    pubchem_json: Dict[str, Any], retrieved_at: str
) -> Any:
    """Create a SmallMolecule Card from one PubChem compound record (offline).

    The card is anchored at the compound's standard InChIKey
    (``sabueso:small_molecule:inchikey:<key>``), like every small molecule card
    (uibcdf/sabueso#25). A record without one raises ``SchemaError``.
    """
    from sabueso.mappings.pubchem import map_compound
    from sabueso.tools.card.small_molecule import single_molecule_card

    cid = str(
        map_compound(pubchem_json, retrieved_at)["fields"].get("identifiers.pubchem")
        or ""
    )
    return single_molecule_card(
        pubchem={"retrieved_at": retrieved_at, "compounds": {cid: pubchem_json}}
    )


def create_compound_card_from_file(path: str | Path, retrieved_at: str) -> Any:
    """Create a SmallMolecule Card from a PubChem JSON file."""
    return create_compound_card_from_json(load_json(path), retrieved_at=retrieved_at)


PUBCHEM_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid"
PROPERTIES = (
    "MolecularWeight,MolecularFormula,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
    "RotatableBondCount,InChI,InChIKey,SMILES,ConnectivitySMILES"
)


class OnlinePubChemClient:
    """PubChem PUG REST: the property table of a compound, by CID."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def compound(self, cid: str) -> Dict[str, Any]:
        url = f"{PUBCHEM_PUG}/{cid}/property/{quote(PROPERTIES, safe=',')}/JSON"
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with urlopen(url, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (400, 404):
                raise RecordNotFoundError(f"PubChem has no compound {cid}") from exc
            raise ConnectorError(
                f"PubChem request for {cid} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"PubChem request for {cid} failed: {exc}") from exc
        return {"retrieved_at": retrieved_at, "record": data}


class FixturePubChemClient:
    """Saved PubChem responses: ``<directory>/pubchem/<cid>.json``, or
    ``<directory>/<cid>.json`` as the older fixtures are laid out."""

    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def compound(self, cid: str) -> Dict[str, Any]:
        if str(cid) in self.failing:
            raise ConnectorError(f"PubChem request for {cid} failed (simulated)")
        for path in (
            self.directory / "pubchem" / f"{cid}.json",
            self.directory / f"{cid}.json",
        ):
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                return {"retrieved_at": self.retrieved_at, "record": data}
        raise RecordNotFoundError(f"PubChem has no compound {cid}")


def fetch_pubchem_json(cid: str) -> Dict[str, Any]:
    """Deprecated: use ``get_compound(cid)["record"]`` (#49)."""
    from sabueso._private.smonitor.outcomes import report_deprecated

    report_deprecated(
        "sabueso.tools.db.pubchem.fetch_pubchem_json",
        'sabueso.tools.db.pubchem.get_compound(cid)["record"]',
    )
    return OnlinePubChemClient().compound(cid)["record"]


def create_compound_card_online(cid: str, retrieved_at: str) -> Any:
    """Deprecated: use ``sabueso.resolve("pubchem:<cid>")``, which links the compound's
    records across sources (#50)."""
    from sabueso._private.smonitor.outcomes import report_deprecated

    report_deprecated(
        "sabueso.create_compound_card_online", 'sabueso.resolve("pubchem:<cid>")'
    )
    data = OnlinePubChemClient().compound(cid)["record"]
    return create_compound_card_from_json(data, retrieved_at=retrieved_at)


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_compound(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The PubChem property table of a compound, by CID, in a provenance envelope."""
    response = online(client, OnlinePubChemClient).compound(identifier)
    return source_record(
        "PubChem",
        "compound",
        {"cid": identifier},
        response.get("retrieved_at"),
        None,
        response.get("record"),
    )
