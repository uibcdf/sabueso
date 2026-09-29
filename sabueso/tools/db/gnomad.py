"""gnomAD: population frequencies of a human gene's variants (#83).

gnomAD states, per variant, its allele count, allele number and frequency in exomes and
genomes, and its consequence on one transcript (``transcript_id``, with ``hgvsc`` and
``hgvsp``). A gene is asked for by the Ensembl gene id the UniProt entry
cross-references.

``variants(gene)`` returns ``{"retrieved_at", "version", "record": {"gene", "variants"}}``,
where ``gene`` keeps gnomAD's canonical and MANE Select transcripts, and ``version`` the
dataset asked (``gnomad_r4``); the API states no finer release. It raises
``RecordNotFoundError`` when gnomAD has no such gene. ``OnlineGnomADClient`` uses the
GraphQL API (no key; data CC0 1.0, some annotations under other terms, none of which
Sabueso reads); ``FixtureGnomADClient`` reads ``<directory>/gnomad/<ENSG>.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import request
from sabueso.tools.db._record import online, source_record

SOURCE = "gnomAD"
API = "https://gnomad.broadinstitute.org/api"
DATASET = "gnomad_r4"
QUERY = (
    """
query($gene: String!) {
  gene(gene_id: $gene, reference_genome: GRCh38) {
    gene_id symbol canonical_transcript_id
    mane_select_transcript { ensembl_id refseq_id }
    variants(dataset: %s) {
      variant_id consequence hgvsp hgvsc transcript_id flags
      exome { ac an af } genome { ac an af }
    }
  }
}
"""
    % DATASET
)


class OnlineGnomADClient:
    def __init__(self, timeout: float = 120.0) -> None:
        self.timeout = timeout

    def variants(self, gene: str) -> Dict[str, Any]:
        retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        body = json.dumps({"query": QUERY, "variables": {"gene": gene}}).encode("utf-8")
        try:
            with urlopen(  # nosec - trusted endpoint
                request(API, data=body, headers={"Content-Type": "application/json"}),
                timeout=self.timeout,
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"gnomAD request failed: {exc}") from exc
        found = (data.get("data") or {}).get("gene")
        if found is None:
            if data.get("errors") and "not found" not in str(data["errors"]).lower():
                raise ConnectorError(f"gnomAD answered with errors: {data['errors']}")
            raise RecordNotFoundError(f"gnomAD has no gene {gene}")
        variants = found.pop("variants") or []
        return {
            "retrieved_at": retrieved_at,
            "version": DATASET,
            "record": {"gene": found, "variants": variants},
        }


class FixtureGnomADClient:
    def __init__(
        self,
        directory: str | Path = "temp_data",
        retrieved_at: str = "fixture",
        failing: set[str] | None = None,
    ) -> None:
        self.directory = Path(directory) / "gnomad"
        self.retrieved_at = retrieved_at
        self.failing = set(failing or ())

    def variants(self, gene: str) -> Dict[str, Any]:
        if gene in self.failing:
            raise ConnectorError(f"gnomAD request for {gene} failed (simulated)")
        path = self.directory / f"{gene}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"gnomAD has no gene {gene}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {"retrieved_at": self.retrieved_at, **saved}


# --- Public source access (uibcdf/sabueso#49) -----------------------------------------


@arg_digest()
def get_variants(identifier: str, client: Any = None, skip_digestion: bool = False):
    """gnomAD's variants of a gene (an Ensembl gene id), with their frequencies."""
    response = online(client, OnlineGnomADClient).variants(identifier)
    return source_record(
        SOURCE,
        "variants",
        {"ensembl_gene": identifier, "dataset": DATASET},
        response.get("retrieved_at"),
        response.get("version"),
        response["record"],
    )
