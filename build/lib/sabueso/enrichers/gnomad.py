"""gnomAD: population frequencies of protein changes (``annotations.population_variants``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request

DEFAULT_LIMIT = 1000


class GnomAD(Enricher):
    option = "gnomad"
    source = "gnomAD"
    registry_id = "gnomad"
    areas = ("annotations.population_variants",)
    organisms = (9606,)
    coverage_detail = "gnomAD covers human variants only"
    option_kind = "options"

    def client(self):
        from sabueso.tools.db.gnomad import OnlineGnomADClient

        return OnlineGnomADClient()

    def requests(self, context, options):
        genes = sorted(
            {v.split(".")[0] for v, _ in context.xref_properties("Ensembl", "GeneId")}
        )
        if not genes:
            raise NothingToAsk("the entry cross-references no Ensembl gene")
        return [Request(g, {"source": self.source, "identifier": g}) for g in genes]

    def fetch(self, client, request, options):
        return client.variants(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.gnomad import map_variants

        limit = options.get("limit", DEFAULT_LIMIT)
        variants = response["record"]["variants"]
        coding = [v for v in variants if v.get("hgvsp")]
        mapped = map_variants(
            coding[:limit],
            context.anchor,
            context.transcripts,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added" if coding else "not_found",
            "version": response.get("version"),
            "count": len(mapped["source_assertions"]),
            "without_protein_change": len(variants) - len(coding),
            "truncated": len(coding) > limit,
            "total_count": len(coding),
        }


ENRICHER = GnomAD()
