"""PHI-base: phenotypes of pathogen mutants (``annotations.pathogen_phenotypes``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class PHIBase(Enricher):
    option = "phi_base"
    source = "PHI-base"
    registry_id = "phi_base"
    areas = ("annotations.pathogen_phenotypes",)

    def client(self):
        from sabueso.tools.db.phi_base import OnlinePHIBaseClient

        return OnlinePHIBaseClient()

    def fetch(self, client, request, options):
        return client.phenotypes(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.phi_base import map_phenotypes

        mapped = map_phenotypes(
            response["sessions"],
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["source_assertions"]),
        }


ENRICHER = PHIBase()
