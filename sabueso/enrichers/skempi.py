"""SKEMPI 2.0: binding changes of interface mutations (``annotations.interface_mutations``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request, RequestPrerequisiteMissing


class SKEMPI(Enricher):
    option = "skempi"
    source = "SKEMPI"
    registry_id = "skempi"
    areas = ("annotations.interface_mutations",)

    def client(self):
        from sabueso.tools.db.skempi import OnlineSKEMPIClient

        return OnlineSKEMPIClient()

    def requests(self, context, options):
        entries = sorted({x["id"].upper() for x in context.xrefs("PDB") if x.get("id")})
        if not entries:
            raise RequestPrerequisiteMissing(
                "the entry cross-references no PDB structure"
            )
        return [
            Request(
                context.anchor,
                {"source": self.source, "identifier": context.anchor},
                {"entries": entries},
            )
        ]

    def fetch(self, client, request, options):
        return client.mutations(request.args["entries"])

    def map(self, context, request, response, options):
        from sabueso.mappings.skempi import map_rows

        mapped = map_rows(
            response["record"],
            context.anchor,
            context.entry,
            context.author_numbering(),
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        items = mapped["fields"].get("annotations.interface_mutations", [])
        mutations = [
            m for i in items for m in i["mutations"] if m["on"] == "this_protein"
        ]
        detail = (
            {}
            if items
            else {
                "detail": "SKEMPI has no row for a chain UniProt states is this "
                "protein, in its PDB entries"
            }
        )
        return mapped, {
            "status": "added" if items else "not_found",
            **detail,
            "version": response.get("version"),
            "checksum": response.get("checksum"),
            "count": len(items),
            "structures": sorted(response["record"]),
            "mutations_on_protein": len(mutations),
            "placed": sum(1 for m in mutations if "location" in m),
        }


ENRICHER = SKEMPI()
