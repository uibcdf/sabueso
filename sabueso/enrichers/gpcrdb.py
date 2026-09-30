"""GPCRdb: a receptor's classification, generic residue numbers and structure states."""

from __future__ import annotations

from sabueso.enrichers import Enricher

#: Every GPCRdb structure of the receptor, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000


class GPCRdb(Enricher):
    option = "gpcrdb"
    source = "GPCRdb"
    registry_id = "gpcrdb"
    areas = (
        "annotations.gpcr_classification",
        "annotations.gpcr_segments",
        "annotations.gpcr_residues",
        "annotations.gpcr_structures",
    )
    option_kind = "options"

    def client(self):
        from sabueso.tools.db.gpcrdb import OnlineGPCRdbClient

        return OnlineGPCRdbClient()

    def fetch(self, client, request, options):
        receptor = client.receptor(request.identifier)
        entry_name = receptor["record"]["entry_name"]
        return {
            "retrieved_at": receptor.get("retrieved_at", ""),
            "receptor": receptor["record"],
            "residues": client.residues(entry_name)["record"],
            "structures": client.structures(entry_name)["record"],
        }

    def map(self, context, request, response, options):
        from sabueso.mappings.gpcrdb import map_receptor

        mapped, outcome = map_receptor(
            response["receptor"],
            response["residues"],
            response["structures"],
            context.anchor,
            context.sequence or "",
            response.get("retrieved_at", ""),
            options.get("limit", DEFAULT_LIMIT),
        )
        return mapped, {"status": "added", **outcome}


ENRICHER = GPCRdb()
