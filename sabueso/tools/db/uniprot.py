"""UniProt: record access (``OnlineUniProtClient``, ``FixtureUniProtClient``), and a
protein card from one UniProt record.

These helpers map a single UniProt entry into a card. They do **not** resolve the
entity: a secondary, demerged or isoform accession is taken as given, no identity links
are added, and no enrichment runs. The card's fields come from that one record, so the
aggregator's subject guard holds (uibcdf/sabueso#21). To resolve a query into a protein
entity, with its identity links, structures and enrichments, use
``resolve_protein_card``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._record import online, source_record


def load_json(path: str | Path) -> Dict[str, Any]:
    """Load UniProt JSON from a local file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _now_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def create_protein_card_from_json(
    uniprot_json: Dict[str, Any], retrieved_at: str | None = None
) -> Any:
    """Create a Protein Card from one UniProt record (offline, no entity resolution)."""
    from sabueso.core.aggregator import build_card_from_mapping
    from sabueso.mappings.uniprot import map_protein

    mapping = map_protein(uniprot_json, retrieved_at=retrieved_at or _now_date())
    accession = uniprot_json.get("primaryAccession")
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        entity_subjects={f"uniprot:{accession}"} if accession else None,
    )


def create_protein_card_from_file(
    path: str | Path, retrieved_at: str | None = None
) -> Any:
    """Create a Protein Card from a UniProt JSON file."""
    return create_protein_card_from_json(load_json(path), retrieved_at=retrieved_at)


def create_protein_card(
    uniprot_id: str, retrieved_at: str | None = None, data_dir: str | Path = "temp_data"
) -> Any:
    """
    Create a Protein Card by UniProt ID using a local JSON fixture.

    This is an offline helper. It expects a file named <ID>.json in data_dir.
    """
    path = Path(data_dir) / f"{uniprot_id}.json"
    return create_protein_card_from_file(path, retrieved_at=retrieved_at)


def fetch_uniprot_json(uniprot_id: str) -> Dict[str, Any]:
    """Deprecated: use ``get_entry(accession)["record"]`` (#49)."""
    from sabueso._private.smonitor.outcomes import report_deprecated

    report_deprecated(
        "sabueso.tools.db.uniprot.fetch_uniprot_json",
        'sabueso.tools.db.uniprot.get_entry(accession)["record"]',
    )
    entry, _ = OnlineUniProtClient().fetch_entry(uniprot_id)
    return entry


def create_protein_card_online(uniprot_id: str, retrieved_at: str | None = None) -> Any:
    """Deprecated: use ``sabueso.resolve(accession)``, which resolves the entity (#49)."""
    from sabueso._private.smonitor.outcomes import report_deprecated

    report_deprecated(
        "sabueso.create_protein_card_online", "sabueso.resolve(accession)"
    )
    entry, retrieved = OnlineUniProtClient().fetch_entry(uniprot_id)
    return create_protein_card_from_json(entry, retrieved_at=retrieved_at or retrieved)


# --- Record access (moved from sabueso.resolver.uniprot_client, uibcdf/sabueso#49) ---


UNIPROT_REST = "https://rest.uniprot.org/uniprotkb"
SEARCH_FIELDS = "accession,reviewed,organism_name,organism_id,length,sequence"
SEARCH_SIZE = 500


def search_query(name: str, organism: int | str, include_subtaxa: bool = False) -> str:
    """UniProt query for a protein name within an organism (optionally its subtree)."""
    if isinstance(organism, int) or str(organism).isdigit():
        field = "taxonomy_id" if include_subtaxa else "organism_id"
        scope = f"{field}:{organism}"
    else:
        scope = f'organism_name:"{organism}"'
    return f'(protein_name:"{name}") AND ({scope})'


def search_key(name: str, organism: int | str, include_subtaxa: bool = False) -> str:
    """File stem used for saved search responses."""
    suffix = "_subtaxa" if include_subtaxa else ""
    return f"{name.replace(' ', '_')}__{str(organism).replace(' ', '_')}{suffix}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class OnlineUniProtClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def fetch_entry(self, accession: str) -> Tuple[Dict[str, Any], str]:
        request = Request(
            f"{UNIPROT_REST}/{accession}.json", headers={"Accept": "application/json"}
        )
        retrieved_at = _now()
        try:
            with urlopen(request, timeout=self.timeout) as resp:  # nosec - trusted endpoint
                return json.loads(resp.read().decode("utf-8")), retrieved_at
        except HTTPError as exc:
            if exc.code == 404:
                raise RecordNotFoundError(f"UniProt has no record {accession}") from exc
            raise ConnectorError(
                f"UniProt request for {accession} failed: HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectorError(
                f"UniProt request for {accession} failed: {exc}"
            ) from exc

    def search(
        self, name: str, organism: int | str, include_subtaxa: bool = False
    ) -> Dict[str, Any]:
        """Search entries by protein name and organism.

        ``total`` may exceed ``len(results)`` when the search is truncated.
        """
        query = search_query(name, organism, include_subtaxa)
        params = urlencode(
            {
                "query": query,
                "fields": SEARCH_FIELDS,
                "format": "json",
                "size": SEARCH_SIZE,
            }
        )
        retrieved_at = _now()
        try:
            with urlopen(  # nosec - trusted endpoint
                f"{UNIPROT_REST}/search?{params}", timeout=self.timeout
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                total = int(resp.headers.get("X-Total-Results", len(results)))
                release = resp.headers.get("X-UniProt-Release")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"UniProt search {query!r} failed: {exc}") from exc
        return {
            "query": query,
            "total": total,
            "release": release,
            "retrieved_at": retrieved_at,
            "results": results,
        }


class FixtureUniProtClient:
    """Serve saved UniProt REST responses.

    Entries come from ``<directory>/<accession>.json`` and searches from
    ``<directory>/uniprot_search/<search_key>.json``. Identifiers or search keys listed in
    ``failing`` simulate a source failure.
    """

    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def fetch_entry(self, accession: str) -> Tuple[Dict[str, Any], str]:
        if accession in self.failing:
            raise ConnectorError(f"UniProt request for {accession} failed (simulated)")
        path = self.directory / f"{accession}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"UniProt has no record {accession}")
        return json.loads(path.read_text(encoding="utf-8")), self.retrieved_at

    def search(
        self, name: str, organism: int | str, include_subtaxa: bool = False
    ) -> Dict[str, Any]:
        key = search_key(name, organism, include_subtaxa)
        if key in self.failing:
            raise ConnectorError(f"UniProt search {key} failed (simulated)")
        path = self.directory / "uniprot_search" / f"{key}.json"
        if not path.is_file():
            raise ConnectorError(f"No saved UniProt search response for {key}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {**saved, "retrieved_at": self.retrieved_at}


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_entry(identifier: str, client: Any = None, skip_digestion: bool = False):
    """The UniProtKB entry of an accession, in a provenance envelope.

    ``version`` is the entry version. Raises RecordNotFoundError or ConnectorError.
    """
    entry, retrieved_at = online(client, OnlineUniProtClient).fetch_entry(identifier)
    version = (entry.get("entryAudit") or {}).get("entryVersion")
    return source_record(
        "UniProt", "entry", {"accession": identifier}, retrieved_at, version, entry
    )


@arg_digest()
def search(
    name: str,
    organism: int | str,
    include_subtaxa: bool = False,
    client: Any = None,
    skip_digestion: bool = False,
):
    """UniProtKB entries whose protein name matches, within an organism (NCBI taxonomy
    id or name; ``include_subtaxa`` adds strains and other taxa below it)."""
    result = online(client, OnlineUniProtClient).search(name, organism, include_subtaxa)
    return source_record(
        "UniProt",
        "search",
        {"name": name, "organism": organism, "include_subtaxa": include_subtaxa},
        result.get("retrieved_at"),
        result.get("release"),
        {"total": result.get("total"), "results": result.get("results")},
    )
