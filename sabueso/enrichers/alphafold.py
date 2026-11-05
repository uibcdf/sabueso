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
    # A missing prediction-API record does not establish database-wide absence.
    not_found_detail = True

    def client(self):
        from sabueso.tools.db.alphafold import OnlineAlphaFoldClient

        return OnlineAlphaFoldClient()

    def fetch(self, client, request, options):
        from sabueso.core.errors import ConnectorError, RecordNotFoundError
        from sabueso.tools.db.alphafold import FixtureAlphaFoldClient

        try:
            return client.prediction(request.identifier)
        except RecordNotFoundError as exc:
            # This fixture implementation raises not-found only for a missing
            # local input. Keep its public client exception, but do not record
            # that input gap as a queried scientific absence on a new Card.
            if isinstance(client, FixtureAlphaFoldClient):
                raise ConnectorError(str(exc)) from exc
            raise

    def map(self, context, request, response, options):
        from sabueso.mappings.alphafold import map_predictions
        from sabueso.mappings.alphafold_modelcif_v1 import (
            FORMAT,
            map_modelcif_predictions,
        )

        if isinstance(response, dict) and response.get("native_format") == FORMAT:
            mapped = map_modelcif_predictions(
                response, context.anchor, response.get("retrieved_at", "")
            )
        else:
            mapped = map_predictions(
                response,
                context.anchor,
                response.get("retrieved_at", ""),
                sequence_md5=(context.entry.get("sequence") or {}).get("md5"),
                input_assertions=[
                    row
                    for mapping in context.mappings
                    for row in mapping.get("source_assertions", [])
                ],
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
