"""NCBI Taxonomy: the organism's ranked lineage (``annotations.taxonomy``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request


class Taxonomy(Enricher):
    option = "taxonomy"
    source = "NCBI Taxonomy"
    registry_id = "ncbi_taxonomy"
    areas = ("annotations.taxonomy",)
    stage = "after_chembl"

    def client(self):
        from sabueso.tools.db.ncbi_taxonomy import OnlineNCBITaxonomyClient

        return OnlineNCBITaxonomyClient()

    def requests(self, context, options):
        return [
            Request(context.taxon, {"source": self.source, "identifier": context.taxon})
        ]

    def fetch(self, client, request, options):
        """The organism's record, then its ancestors' (one lookup each)."""
        if request.identifier is None:
            return {"organism": {"record": []}, "lineage": None}
        organism = client.taxa([request.identifier])
        lineage = None
        if organism["record"]:
            lineage = client.taxa(organism["record"][0].get("lineage") or [])
        return {"organism": organism, "lineage": lineage}

    def map(self, context, request, response, options):
        from sabueso.mappings.ncbi_taxonomy import map_taxonomy

        organism, lineage = response["organism"], response["lineage"]
        if not organism["record"]:
            return None, {"status": "not_found"}
        taxon = organism["record"][0]
        mapped = map_taxonomy(
            taxon, lineage["record"], context.anchor, organism.get("retrieved_at", "")
        )
        return mapped, {
            "status": "added",
            "count": len(taxon.get("lineage") or []),
            **({"missing": lineage["missing"]} if lineage.get("missing") else {}),
        }


ENRICHER = Taxonomy()
