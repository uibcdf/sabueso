"""AlphaFold DB: predicted models (``has_predicted_structure``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class AlphaFold(Enricher):
    option = "predicted_structures"
    source = "AlphaFold DB"
    registry_id = "alphafold_db"
    areas = ("relationships.has_predicted_structure",)
    client_option = "alphafold_client"
    stage = "after_chembl"
    not_found_detail = False

    def client(self):
        from sabueso.tools.db.alphafold import OnlineAlphaFoldClient

        return OnlineAlphaFoldClient()

    def fetch(self, client, request, options):
        return client.prediction(request.identifier)

    def map(self, context, request, response, options):
        from sabueso.mappings.alphafold import map_predictions

        mapped = map_predictions(
            response,
            context.anchor,
            response.get("retrieved_at", ""),
            sequence_md5=(context.entry.get("sequence") or {}).get("md5"),
        )
        versions = sorted(
            {r["qualifiers"]["model_version"] for r in mapped["relationships"]} - {None}
        )
        return mapped, {
            "status": "added",
            "version": "; ".join(f"v{v}" for v in versions) or None,
            "count": len(mapped["relationships"]),
        }


ENRICHER = AlphaFold()
