"""gnomAD: population frequencies of protein changes (``annotations.population_variants``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request

#: Every protein-level variant, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000


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
        canonical = context.transcripts["canonical"]
        requests = []
        for gene in genes:
            # The Ensembl transcripts UniProt states encode its canonical isoform.
            transcripts = sorted(
                {
                    x["id"].split(".")[0]
                    for x in context.xrefs("Ensembl")
                    if x["id"].split(".")[0] in canonical
                    and any(
                        p.get("key") == "GeneId"
                        and str(p.get("value")).split(".")[0] == gene
                        for p in x.get("properties") or []
                    )
                }
            )
            requests.append(
                Request(
                    gene,
                    {"source": self.source, "identifier": gene},
                    {"canonical_transcripts": transcripts},
                )
            )
        return requests

    def fetch(self, client, request, options):
        from sabueso.core.errors import RecordNotFoundError

        response = client.variants(request.identifier)
        on_canonical = {}
        for transcript in request.args["canonical_transcripts"]:
            try:
                on_canonical[transcript] = client.transcript_variants(transcript)
            except RecordNotFoundError:
                on_canonical[transcript] = None
        return {**response, "on_canonical": on_canonical}

    def map(self, context, request, response, options):
        from sabueso.mappings.gnomad import map_variants, merged

        limit = options.get("limit", DEFAULT_LIMIT)
        on_canonical = response.get("on_canonical") or {}
        variants, without = merged(
            response["record"]["variants"],
            [
                answer["record"]
                for _, answer in sorted(on_canonical.items())
                if answer is not None
            ],
        )
        mapped = map_variants(
            variants[:limit],
            context.anchor,
            context.transcripts,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added" if variants else "not_found",
            "version": response.get("version"),
            "count": len(mapped["source_assertions"]),
            "without_protein_change": without,
            "truncated": len(variants) > limit,
            "total_count": len(variants),
            "canonical_transcripts": [
                {
                    "transcript": transcript,
                    "version": answer["record"]["transcript"].get("transcript_version"),
                }
                if answer is not None
                else {"transcript": transcript, "not_found": True}
                for transcript, answer in sorted(on_canonical.items())
            ],
        }


ENRICHER = GnomAD()
