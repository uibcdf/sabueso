"""SAbDab: antibody structures of this protein (``annotations.antibody_complexes``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request


class SAbDab(Enricher):
    option = "sabdab"
    source = "SAbDab"
    registry_id = "sabdab"
    areas = ("annotations.antibody_complexes",)

    def client(self):
        from sabueso.tools.db.sabdab import OnlineSAbDabClient

        return OnlineSAbDabClient()

    def requests(self, context, options):
        entries = sorted({x["id"].upper() for x in context.xrefs("PDB") if x.get("id")})
        if not entries:
            raise NothingToAsk("the entry cross-references no PDB structure")
        return [
            Request(
                context.anchor,
                {"source": self.source, "identifier": context.anchor},
                {"entries": entries},
            )
        ]

    def fetch(self, client, request, options):
        return client.complexes(request.args["entries"])

    def map(self, context, request, response, options):
        from sabueso.mappings.sabdab import map_complexes

        mapped = map_complexes(
            response["record"],
            context.anchor,
            context.entry,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        items = mapped["fields"].get("annotations.antibody_complexes", [])
        detail = (
            {}
            if items
            else {
                "detail": "SAbDab assigns no chain UniProt states is this protein, "
                "in its PDB entries, as an antibody's antigen"
            }
        )
        return mapped, {
            "status": "added" if items else "not_found",
            **detail,
            "version": response.get("version"),
            "checksum": response.get("checksum"),
            "count": len(items),
            "structures": sorted({i["structure"] for i in items}),
        }


ENRICHER = SAbDab()
