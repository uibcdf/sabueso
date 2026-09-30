"""KLIFS: a kinase's classification, pocket and the conformations of its structures."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request

#: Every KLIFS structure of the kinase, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000


class KLIFS(Enricher):
    option = "klifs"
    source = "KLIFS"
    registry_id = "klifs"
    areas = (
        "annotations.kinase_classification",
        "annotations.kinase_structures",
        "annotations.kinase_pocket",
    )
    option_kind = "options"

    def client(self):
        from sabueso.tools.db.klifs import OnlineKLIFSClient

        return OnlineKLIFSClient()

    def requests(self, context, options):
        # The author numbering RCSB states for the card's structures places the pocket.
        return [
            Request(
                context.anchor,
                self.record(context, options),
                {"entry": context.entry, "numbering": context.author_numbering()},
            )
        ]

    def fetch(self, client, request, options):
        from sabueso.core.errors import RecordNotFoundError
        from sabueso.mappings.klifs import reference
        from sabueso.tools.db.klifs import kinases_of

        listing = client.kinases()
        stated = kinases_of(listing["record"], request.identifier)
        if not stated:
            raise RecordNotFoundError(
                f"KLIFS states no kinase for {request.identifier}"
            )
        kinases = []
        for listed in stated:
            kinase = client.kinase(listed["kinase_ID"])["record"]
            rows = client.structures(listed["kinase_ID"])["record"]
            chosen = reference(
                kinase, rows, request.args["entry"], request.args["numbering"]
            )
            residues = (
                client.pocket(chosen["structure_ID"])["record"] if chosen else None
            )
            kinases.append(
                {
                    "kinase": kinase,
                    "structures": rows,
                    "reference": chosen,
                    "pocket": residues,
                }
            )
        return {"retrieved_at": listing.get("retrieved_at", ""), "kinases": kinases}

    def map(self, context, request, response, options):
        from sabueso.mappings.klifs import map_kinases

        mapped, outcome = map_kinases(
            response["kinases"],
            context.anchor,
            context.entry,
            request.args["numbering"],
            response.get("retrieved_at", ""),
            options.get("limit", DEFAULT_LIMIT),
        )
        return mapped, {"status": "added", **outcome}


ENRICHER = KLIFS()
