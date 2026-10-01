"""UniRef: the sequence clusters UniProt places an entry in (#103).

UniProt clusters every sequence at three identity levels: UniRef100 (identical
sequences and their fragments), UniRef90 and UniRef50 (at least 90% and 50% identity
to the cluster's seed, over 80% of the longer sequence). Each cluster lists its members:
UniProtKB entries (by entry name and accessions) and UniParc sequences without an entry,
each with its organism, length and its own UniRef100 cluster.

A cluster is UniProt's statement of sequence similarity. It is never identity: two
members are related sequences, possibly of different strains or species, and Sabueso
does not merge them.

- ``clusters(accession)``: the UniRef100, UniRef90 and UniRef50 clusters of an entry
  (one request);
- ``members(cluster_id)``: a cluster's members (500 per request).

Each answer is ``{"retrieved_at", "version", "record"}``, ``version`` the UniProt release
the service states. ``OnlineUniRefClient`` queries UniProt's REST API (CC BY 4.0, as
UniProtKB); ``FixtureUniRefClient`` reads ``<directory>/uniref/``: ``clusters_<acc>.json``
and ``members_<cluster>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import stamp, urlopen
from sabueso.tools.db._record import online, source_record

SOURCE = "UniProt"
API = "https://rest.uniprot.org/uniref"
PAGE = 500
#: Members of a cluster kept, at most; a cut is reported.
MAX_MEMBERS = 5000


class OnlineUniRefClient:
    def __init__(self, timeout: float = 120.0) -> None:
        self.timeout = timeout

    def _get(self, url: str) -> tuple:
        try:
            with urlopen(url, timeout=self.timeout, expect_json=True) as resp:
                return (
                    json.loads(resp.read().decode("utf-8")),
                    resp.headers.get("X-UniProt-Release"),
                    resp.headers.get("Link"),
                )
        except HTTPError as exc:
            if exc.code == 404:
                raise RecordNotFoundError(f"UniRef has no {url}") from exc
            raise ConnectorError(f"UniRef request failed: {exc}") from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"UniRef request failed: {exc}") from exc

    def clusters(self, accession: str) -> Dict[str, Any]:
        retrieval = stamp(SOURCE)
        query = urlencode(
            {
                "query": f"uniprot_id:{accession}",
                "fields": "id,name,count,identity",
                "format": "json",
                "size": 10,
            }
        )
        found, release, _ = self._get(f"{API}/search?{query}")
        return {
            "retrieved_at": retrieval.value,
            "version": release,
            "record": [
                {
                    "id": c.get("id"),
                    "level": c.get("entryType"),
                    "member_count": c.get("memberCount"),
                }
                for c in found.get("results") or []
            ],
        }

    def members(self, cluster_id: str) -> Dict[str, Any]:
        retrieval = stamp(SOURCE)
        url = (
            f"{API}/{cluster_id}/members?{urlencode({'format': 'json', 'size': PAGE})}"
        )
        members: List[Dict[str, Any]] = []
        release = None
        while url and len(members) < MAX_MEMBERS:
            found, release, link = self._get(url)
            members.extend(found.get("results") or [])
            url = _next(link)
        return {
            "retrieved_at": retrieval.value,
            "version": release,
            "record": members[:MAX_MEMBERS],
            "truncated": bool(url) or len(members) > MAX_MEMBERS,
        }


def _next(link: str | None) -> str | None:
    """The next page of a paginated answer (``Link: <url>; rel="next"``)."""
    for part in (link or "").split(","):
        if 'rel="next"' in part:
            return part.split(";")[0].strip().strip("<>")
    return None


class FixtureUniRefClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory) / "uniref"
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def _read(self, name: str) -> Dict[str, Any]:
        if name in self.failing:
            raise ConnectorError(f"UniRef request for {name} failed (simulated)")
        path = self.directory / f"{name}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"UniRef has no {name}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {"retrieved_at": self.retrieved_at, **saved}

    def clusters(self, accession: str) -> Dict[str, Any]:
        return self._read(f"clusters_{accession}")

    def members(self, cluster_id: str) -> Dict[str, Any]:
        return {"truncated": False, **self._read(f"members_{cluster_id}")}


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_clusters(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The UniRef100, UniRef90 and UniRef50 clusters UniProt places an entry in."""
    response = online(client, OnlineUniRefClient).clusters(identifier)
    return source_record(
        SOURCE,
        "uniref_clusters",
        {"uniprot": identifier},
        response.get("retrieved_at"),
        response.get("version"),
        {"clusters": response["record"]},
    )
