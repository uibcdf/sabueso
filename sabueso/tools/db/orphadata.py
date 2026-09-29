"""Orphadata (Orphanet): genes associated with rare diseases (#82, #83).

Orphanet curates, per rare disorder, the genes associated with it: the type of
association (e.g. "Disease-causing germline mutation(s) in"), its status ("Assessed"),
and the publications that validate it. Each gene states its UniProt (Swiss-Prot)
accession, so a card joins through an identifier the source states.

The data is published as one XML file (``en_product6.xml``, CC BY 4.0), dated in its
header. ``OnlineOrphadataClient`` downloads it (about 22 MB) and indexes it once per
process, in memory; nothing is written. The version recorded is the file's date. ``FixtureOrphadataClient`` reads
``<directory>/orphadata/en_product6.xml``.

``associations(accession)`` returns ``{"retrieved_at", "version", "record": [row,
...]}``, one row per disorder–gene association naming the accession. It raises
``RecordNotFoundError`` when no association names it.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET  # nosec - a trusted source's own file
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import request
from sabueso.tools.db._record import online, source_record

SOURCE = "Orphanet"
URL = "https://www.orphadata.com/data/xml/en_product6.xml"

_MEMORY: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}


def _text(node: Any, path: str) -> str | None:
    found = node.find(path) if node is not None else None
    return found.text.strip() if found is not None and found.text else None


def parse_release(xml: bytes) -> tuple:
    """``(version, {accession: [row, ...]})`` of an ``en_product6.xml`` file."""
    root = ET.fromstring(xml)  # nosec - a trusted source's own file
    version = (root.get("date") or "")[:10] or None
    index: Dict[str, List[Dict[str, Any]]] = {}
    for disorder in root.iter("Disorder"):
        code = _text(disorder, "OrphaCode")
        base = {
            "orpha_code": code,
            "disorder_name": _text(disorder, "Name"),
            "disorder_type": _text(disorder, "DisorderType/Name"),
            "disorder_group": _text(disorder, "DisorderGroup/Name"),
        }
        for association in disorder.iter("DisorderGeneAssociation"):
            gene = association.find("Gene")
            refs = {
                _text(r, "Source"): _text(r, "Reference")
                for r in (gene.iter("ExternalReference") if gene is not None else [])
            }
            accession = refs.get("SwissProt")
            if not accession:
                continue
            validation = _text(association, "SourceOfValidation")
            row = {
                **base,
                "gene_symbol": _text(gene, "Symbol"),
                "gene_name": _text(gene, "Name"),
                "ensembl_gene": refs.get("Ensembl"),
                "hgnc": refs.get("HGNC"),
                "omim": refs.get("OMIM"),
                "association_type": _text(
                    association, "DisorderGeneAssociationType/Name"
                ),
                "association_status": _text(
                    association, "DisorderGeneAssociationStatus/Name"
                ),
                "validation": [v.replace("[PMID]", "") for v in validation.split("_")]
                if validation
                else [],
            }
            index.setdefault(accession, []).append(
                {k: v for k, v in row.items() if v not in (None, "", [])}
            )
    return version, index


class OnlineOrphadataClient:
    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout

    def _index(self) -> tuple:
        if _MEMORY:
            ((version, index),) = _MEMORY.items()
            return version, index
        try:
            with urlopen(request(URL), timeout=self.timeout) as resp:  # nosec - trusted
                payload = resp.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(f"Orphadata download failed: {exc}") from exc
        try:
            version, index = parse_release(payload)
        except ET.ParseError as exc:
            raise ConnectorError(f"Orphadata file is not valid XML: {exc}") from exc
        _MEMORY.clear()
        _MEMORY[version] = index
        return version, index

    def associations(self, accession: str) -> Dict[str, Any]:
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        version, index = self._index()
        if accession not in index:
            raise RecordNotFoundError(
                f"Orphadata ({version}) names no gene with UniProt {accession}"
            )
        return {
            "retrieved_at": retrieved_at,
            "version": version,
            "record": index[accession],
        }


class FixtureOrphadataClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.path = Path(directory) / "orphadata" / "en_product6.xml"
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def associations(self, accession: str) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(
                f"Orphadata request for {accession} failed (simulated)"
            )
        version, index = parse_release(self.path.read_bytes())
        if accession not in index:
            raise RecordNotFoundError(
                f"Orphadata names no gene with UniProt {accession}"
            )
        return {
            "retrieved_at": self.retrieved_at,
            "version": version,
            "record": index[accession],
        }


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_associations(identifier: str, client: Any = None, skip_digestion: bool = False):
    """Orphanet's rare-disorder associations of a gene, by its UniProt accession."""
    response = online(client, OnlineOrphadataClient).associations(identifier)
    return source_record(
        SOURCE,
        "associations",
        {"uniprot": identifier},
        response.get("retrieved_at"),
        response.get("version"),
        response["record"],
    )
