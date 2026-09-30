"""Europe PMC: the publications whose text mentions a protein's accession (#92).

Europe PMC mines the text of abstracts and open-access full texts for database
accession numbers (UniProt, PDB, …). An article whose text states ``P60174`` is found by
``ACCESSION_ID:P60174 AND ACCESSION_TYPE:uniprot``: the accession is written in the
paper, and Europe PMC found it by text mining (``hasTMAccessionNumbers``). This is not
UniProt's curated references (``UNIPROT_PUBS``), which reach the card as
``described_in``.

Only stated accessions are used. Europe PMC's gene and protein annotations ground a
*name* to an entry, without the organism: "triosephosphate isomerase" in a paper on the
human deficiency is tagged with a yeast entry (Q9C401). That is identity by name, and
Sabueso does not use it.

``mentions(accession, limit)`` returns ``{"retrieved_at", "version", "record":
{"query", "hitCount", "articles": [...]}}``: the first ``limit`` articles of the search,
newest first, with their ids and bibliographic data. It raises ``RecordNotFoundError``
when no article mentions the accession.

``OnlineEuropePMCClient`` pages the REST search (no key; ``version`` is the service's
version, e.g. 6.9). ``FixtureEuropePMCClient`` reads
``<directory>/europepmc/<ACCESSION>.json``.

Terms: EMBL-EBI places no restrictions of its own on the data and expects attribution;
each article keeps its licence. Sabueso keeps ids and bibliographic data, not text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import request, stamp, urlopen
from sabueso.tools.db._record import online, source_record

SOURCE = "Europe PMC"
SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
#: Every mention up to a safety ceiling, unless ``europepmc={"limit": n}`` asks for
#: fewer; a cut is reported (#88).
DEFAULT_LIMIT = 5000
PAGE = 1000
KEPT = (
    "id",
    "source",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "journalTitle",
    "pubYear",
    "isOpenAccess",
    "firstPublicationDate",
)


def query(accession: str) -> str:
    return f"ACCESSION_ID:{accession} AND ACCESSION_TYPE:uniprot"


class OnlineEuropePMCClient:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout

    def mentions(self, accession: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        retrieval = stamp()
        articles, cursor, hits, version = [], "*", 0, None
        while len(articles) < limit:
            params = {
                "query": query(accession),
                "format": "json",
                "resultType": "lite",
                "pageSize": min(PAGE, limit - len(articles)),
                "cursorMark": cursor,
            }
            try:
                with urlopen(  # nosec - trusted endpoint
                    request(f"{SEARCH}?{urlencode(params)}"), timeout=self.timeout
                ) as resp:
                    page = json.loads(resp.read().decode("utf-8"))
            except HTTPError as exc:
                raise ConnectorError(
                    f"Europe PMC search for {accession} failed: HTTP {exc.code}"
                ) from exc
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                raise ConnectorError(
                    f"Europe PMC search for {accession} failed: {exc}"
                ) from exc
            version, hits = page.get("version"), int(page.get("hitCount") or 0)
            results = (page.get("resultList") or {}).get("result") or []
            articles += [
                {k: r[k] for k in KEPT if r.get(k) is not None} for r in results
            ]
            following = page.get("nextCursorMark")
            if not results or not following or following == cursor:
                break
            cursor = following
        if not hits:
            raise RecordNotFoundError(
                f"No Europe PMC article mentions UniProt {accession}", version=version
            )
        return {
            "retrieved_at": retrieval.value,
            "version": version,
            "record": {
                "query": query(accession),
                "hitCount": hits,
                "articles": articles[:limit],
            },
        }


class FixtureEuropePMCClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def mentions(self, accession: str, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
        if accession in self.failing:
            raise ConnectorError(
                f"Europe PMC search for {accession} failed (simulated)"
            )
        path = self.directory / "europepmc" / f"{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(
                f"No Europe PMC article mentions UniProt {accession}"
            )
        saved = json.loads(path.read_text(encoding="utf-8"))
        record = dict(saved["record"])
        record["articles"] = record["articles"][:limit]
        return {"retrieved_at": self.retrieved_at, **saved, "record": record}


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_mentions(
    identifier: str,
    limit: int = DEFAULT_LIMIT,
    client: Any = None,
    skip_digestion: bool = False,
):
    """The Europe PMC articles whose text mentions a UniProt accession."""
    response = online(client, OnlineEuropePMCClient).mentions(identifier, limit)
    record = response["record"]
    return source_record(
        SOURCE,
        "mentions",
        {"uniprot": identifier, "limit": limit},
        response.get("retrieved_at"),
        response.get("version"),
        record,
        truncated=record["hitCount"] > len(record["articles"]),
    )
