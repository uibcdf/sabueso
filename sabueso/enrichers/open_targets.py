"""Open Targets: target–disease associations (``associated_with``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request, RequestPrerequisiteMissing


class OpenTargets(Enricher):
    option = "open_targets"
    source = "Open Targets"
    registry_id = "open_targets"
    areas = ("relationships.associated_with",)
    organisms = (9606,)
    coverage_detail = "Open Targets covers Homo sapiens genes only"
    option_kind = "options"
    historical_parameters = {"limit": "limit"}

    def client(self):
        from sabueso.tools.db.open_targets import OnlineOpenTargetsClient

        return OnlineOpenTargetsClient()

    def requests(self, context, options):
        genes = sorted(
            {v.split(".")[0] for v, _ in context.xref_properties("Ensembl", "GeneId")}
        )
        if not genes:
            raise RequestPrerequisiteMissing(
                "the entry cross-references no Ensembl gene"
            )
        return [Request(g, {"source": self.source, "identifier": g}) for g in genes]

    def fetch(self, client, request, options):
        from sabueso.tools.db.open_targets import DEFAULT_LIMIT

        return client.associations(
            request.identifier, options.get("limit", DEFAULT_LIMIT)
        )

    def map(self, context, request, response, options):
        from sabueso.mappings.open_targets import lists_protein, map_associations

        if not lists_protein(response["record"]["target"], context.anchor):
            return None, {
                "status": "not_found",
                "detail": f"Open Targets does not list {context.anchor} among "
                f"{request.identifier}'s products",
            }
        mapped = map_associations(
            response["record"],
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        count = response["record"].get("count") or 0
        return mapped, {
            "status": "added" if mapped["relationships"] else "not_found",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
            "truncated": count > len(response["record"]["rows"]),
            "total_count": count,
        }


ENRICHER = OpenTargets()
