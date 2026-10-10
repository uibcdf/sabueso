"""ClinVar: variants and their classification (``annotations.clinical_variants``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request


class ClinVar(Enricher):
    option = "clinvar"
    source = "ClinVar"
    registry_id = "clinvar"
    areas = ("annotations.clinical_variants",)
    organisms = (9606,)
    coverage_detail = "ClinVar covers human variants only"
    option_kind = "options"
    historical_parameters = {"limit": "limit"}

    def client(self):
        from sabueso.tools.db.clinvar import OnlineClinVarClient

        return OnlineClinVarClient()

    def _genes(self, context):
        return sorted({x["id"] for x in context.xrefs("GeneID")})

    def record(self, context, options):
        return {**super().record(context, options), "genes": self._genes(context)}

    def requests(self, context, options):
        if not self._genes(context):
            raise NothingToAsk("the entry cross-references no NCBI Gene id")
        return [Request(context.anchor, self.record(context, options))]

    def fetch(self, client, request, options):
        from sabueso.tools.db.clinvar import DEFAULT_LIMIT

        return client.variants(
            request.record["genes"], options.get("limit", DEFAULT_LIMIT)
        )

    def map(self, context, request, response, options):
        from sabueso.mappings.clinvar import map_variants

        mapped = map_variants(
            response["record"],
            context.anchor,
            context.transcripts,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added" if response["record"] else "not_found",
            "version": response.get("version"),
            "count": len(response["record"]),
            "truncated": response.get("truncated", False),
            "total_count": response.get("total_count"),
        }


ENRICHER = ClinVar()
