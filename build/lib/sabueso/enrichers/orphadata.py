"""Orphanet: rare disorders associated with a gene (``associated_with``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class Orphadata(Enricher):
    option = "orphadata"
    source = "Orphanet"
    registry_id = "orphadata"
    areas = ("relationships.associated_with",)
    organisms = (9606,)
    coverage_detail = "Orphanet covers Homo sapiens genes only"

    def client(self):
        from sabueso.tools.db.orphadata import OnlineOrphadataClient

        return OnlineOrphadataClient()

    def fetch(self, client, request, options):
        return client.associations(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.orphadata import map_associations

        mapped = map_associations(
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


ENRICHER = Orphadata()
