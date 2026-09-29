"""Reactome: pathways and reactions (``participates_in``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class Reactome(Enricher):
    option = "reactome"
    source = "Reactome"
    registry_id = "reactome"
    areas = ("relationships.participates_in",)

    def client(self):
        from sabueso.tools.db.reactome import OnlineReactomeClient

        return OnlineReactomeClient()

    def fetch(self, client, request, options):
        return client.pathways(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.reactome import map_pathways

        mapped = map_pathways(
            response["record"],
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
        }


ENRICHER = Reactome()
