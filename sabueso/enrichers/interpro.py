"""InterPro: family site residues (``features_positional.family_site``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class FamilySites(Enricher):
    option = "family_sites"
    source = "InterPro"
    registry_id = "interpro"
    areas = ("features_positional.family_site",)
    client_option = "interpro_client"

    def client(self):
        from sabueso.tools.db.interpro import OnlineInterProClient

        return OnlineInterProClient()

    def fetch(self, client, request, options):
        return client.site_residues(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.interpro import map_family_sites

        mapped = map_family_sites(response, response.get("retrieved_at", ""))
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["source_assertions"]),
        }


ENRICHER = FamilySites()
