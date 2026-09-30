"""gnomAD: population frequencies of a human gene's variants (#83).

gnomAD states, per variant, its allele count, allele number and frequency in exomes and
genomes, and its consequence on a transcript (``transcript_id``, with ``hgvsc`` and
``hgvsp``). Asked for a gene (the Ensembl gene id the UniProt entry cross-references),
it states each variant's consequence on one of the gene's transcripts, the one it
ranks most severe. Asked for a transcript, it states each variant's consequence on that
transcript, with the transcript's version (#85).

``variants(gene)`` returns ``{"retrieved_at", "version", "record": {"gene", "variants"}}``,
where ``gene`` keeps gnomAD's canonical and MANE Select transcripts, and ``version`` the
dataset asked (``gnomad_r4``); the API states no finer release.
``transcript_variants(transcript)`` returns the same shape with ``record: {"transcript",
"variants"}``. Both raise ``RecordNotFoundError`` when gnomAD has no such gene or
transcript. ``OnlineGnomADClient`` uses the GraphQL API (no key; data CC0 1.0, some
annotations under other terms, none of which Sabueso reads); ``FixtureGnomADClient``
reads ``<directory>/gnomad/<ENSG or ENST>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from urllib.error import HTTPError, URLError

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.tools.db._http import request, stamp, urlopen
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
TRANSCRIPT_QUERY = (
    """
query($transcript: String!) {
  transcript(transcript_id: $transcript, reference_genome: GRCh38) {
    transcript_id transcript_version gene_id
    variants(dataset: %s) {
      variant_id consequence hgvsp hgvsc transcript_id transcript_version flags
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

    def _ask(self, query: str, kind: str, identifier: str) -> Dict[str, Any]:
        retrieval = stamp(SOURCE)
        body = json.dumps({"query": query, "variables": {kind: identifier}}).encode(
            "utf-8"
        )
        try:
            with urlopen(  # nosec - trusted endpoint
                request(API, data=body, headers={"Content-Type": "application/json"}),
                timeout=self.timeout,
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise ConnectorError(f"gnomAD request failed: {exc}") from exc
        found = (data.get("data") or {}).get(kind)
        if found is None:
            if data.get("errors") and "not found" not in str(data["errors"]).lower():
                raise ConnectorError(f"gnomAD answered with errors: {data['errors']}")
            raise RecordNotFoundError(f"gnomAD has no {kind} {identifier}")
        variants = found.pop("variants") or []
        return {
            "retrieved_at": retrieval.value,
            "version": DATASET,
            "record": {kind: found, "variants": variants},
        }

    def variants(self, gene: str) -> Dict[str, Any]:
        return self._ask(QUERY, "gene", gene)

    def transcript_variants(self, transcript: str) -> Dict[str, Any]:
        return self._ask(TRANSCRIPT_QUERY, "transcript", transcript)


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

    def _read(self, kind: str, identifier: str) -> Dict[str, Any]:
        if identifier in self.failing:
            raise ConnectorError(f"gnomAD request for {identifier} failed (simulated)")
        path = self.directory / f"{identifier}.json"
        if not path.is_file():
            raise RecordNotFoundError(f"gnomAD has no {kind} {identifier}")
        saved = json.loads(path.read_text(encoding="utf-8"))
        return {"retrieved_at": self.retrieved_at, **saved}

    def variants(self, gene: str) -> Dict[str, Any]:
        return self._read("gene", gene)

    def transcript_variants(self, transcript: str) -> Dict[str, Any]:
        return self._read("transcript", transcript)


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


@arg_digest()
def get_transcript_variants(
    identifier: str, client: Any = None, skip_digestion: bool = False
):
    """gnomAD's variants of a transcript (an Ensembl transcript id), each with its
    consequence on that transcript, and their frequencies."""
    response = online(client, OnlineGnomADClient).transcript_variants(identifier)
    return source_record(
        SOURCE,
        "transcript_variants",
        {"ensembl_transcript": identifier, "dataset": DATASET},
        response.get("retrieved_at"),
        response.get("version"),
        response["record"],
    )
