"""STRING: functional associations (``functionally_associated_with``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request


class STRING(Enricher):
    option = "string"
    source = "STRING"
    registry_id = "string"
    areas = ("relationships.functionally_associated_with",)
    option_kind = "options"
    stage = "after_structures"
    not_found_detail = False

    def client(self):
        from sabueso.tools.db.stringdb import OnlineStringClient

        return OnlineStringClient()

    def record(self, context, options):
        return {
            "source": self.source,
            "identifier": context.anchor,
            "species": context.taxon,
            **options,
        }

    def requests(self, context, options):
        return [Request(context.anchor, self.record(context, options))]

    def fetch(self, client, request, options):
        return client.partners(request.identifier, request.record["species"], **options)

    def map(self, context, request, response, options):
        from sabueso.mappings.stringdb import map_string_partners

        mapped = map_string_partners(
            response, context.anchor, response.get("retrieved_at", "")
        )
        return mapped, {
            "required_score": response.get("query", {}).get("required_score"),
            "limit": response.get("query", {}).get("limit"),
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
            # STRING states no total: a cut is "more than count", never a total.
            "truncated": bool(response.get("truncated")),
        }


ENRICHER = STRING()
