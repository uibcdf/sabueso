"""Europe PMC: the publications whose text mentions the protein (``mentioned_in``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class EuropePMC(Enricher):
    option = "europepmc"
    source = "Europe PMC"
    registry_id = "europepmc"
    areas = ("relationships.mentioned_in",)
    option_kind = "options"

    def client(self):
        from sabueso.tools.db.europepmc import OnlineEuropePMCClient

        return OnlineEuropePMCClient()

    def fetch(self, client, request, options):
        from sabueso.tools.db.europepmc import DEFAULT_LIMIT

        return client.mentions(request.identifier, options.get("limit", DEFAULT_LIMIT))

    def map(self, context, request, response, options):
        from sabueso.mappings.europepmc import map_mentions

        record = response["record"]
        mapped = map_mentions(
            record,
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
            "truncated": record["hitCount"] > len(record["articles"]),
            "total_count": record["hitCount"],
        }


ENRICHER = EuropePMC()
