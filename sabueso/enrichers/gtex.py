"""GTEx: the ontology terms (UBERON, EFO) of the tissues the card's pext names (#102)."""

from __future__ import annotations

import re

from sabueso.enrichers import Enricher, NothingToAsk, Request

PEXT = "annotations.exon_usage_by_tissue"


class GTEx(Enricher):
    option = "gtex"
    source = "GTEx"
    registry_id = "gtex"
    areas = ("annotations.tissue_terms",)
    organisms = (9606,)
    coverage_detail = "GTEx samples human tissues only"

    def client(self):
        from sabueso.tools.db.gtex import OnlineGTExClient

        return OnlineGTExClient()

    def requests(self, context, options):
        keys, releases = set(), set()
        for mapping in context.mappings:
            for item in (mapping.get("fields") or {}).get(PEXT) or []:
                keys.update(t.get("tissue") for t in item.get("tissues") or [])
            for made in mapping.get("source_assertions") or []:
                if made.get("field_path") == PEXT:
                    releases.add(str((made.get("source") or {}).get("version") or ""))
        keys.discard(None)
        if not keys:
            raise NothingToAsk(
                "the card states no pext tissues (ask exon_usage=True as well)"
            )
        datasets = sorted({f"gtex_{m}" for r in releases for m in _gtex(r)})
        if len(datasets) != 1:
            raise NothingToAsk(
                f"the pext states no single GTEx release ({sorted(releases)})"
            )
        (dataset,) = datasets
        return [
            Request(
                dataset,
                {"source": self.source, "identifier": dataset},
                {"tissues": sorted(keys)},
            )
        ]

    def fetch(self, client, request, options):
        return client.tissues(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.gtex import map_tissue_terms

        mapped, outcome = map_tissue_terms(
            response["record"],
            request.args["tissues"],
            context.anchor,
            response.get("retrieved_at", ""),
            request.identifier,
        )
        return mapped, {"status": "added", "version": request.identifier, **outcome}


def _gtex(release: str):
    """``v10`` from gnomAD's pext release, ``gnomad_r4 pext (GTEx v10)``."""
    return re.findall(r"GTEx (v\d+)", release)


ENRICHER = GTEx()
