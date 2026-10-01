"""UniRef: a protein's sequence clusters and the entries they relate it to (#103)."""

from __future__ import annotations

from sabueso.enrichers import Enricher


class UniRef(Enricher):
    option = "uniref"
    source = "UniProt"
    data = "uniref"
    registry_id = "uniref"
    areas = ("identifiers.uniref", "relationships.clustered_with")

    @property
    def match(self):
        return {"source": self.source, "data": self.data}

    def client(self):
        from sabueso.tools.db.uniref import OnlineUniRefClient

        return OnlineUniRefClient()

    def record(self, context, options):
        return {"source": self.source, "data": self.data, "identifier": context.anchor}

    def fetch(self, client, request, options):
        from sabueso.core.errors import RecordNotFoundError
        from sabueso.mappings.uniref import cluster_ids

        clusters = client.clusters(request.identifier)
        uniref90 = cluster_ids(clusters["record"]).get("uniref90")
        if uniref90 is None:
            raise RecordNotFoundError(
                f"UniProt places {request.identifier} in no UniRef90 cluster"
            )
        members = client.members(uniref90)
        return {
            "retrieved_at": clusters.get("retrieved_at", ""),
            "version": clusters.get("version") or members.get("version"),
            "clusters": clusters["record"],
            "members": members["record"],
            "truncated": members.get("truncated", False),
        }

    def map(self, context, request, response, options):
        from sabueso.mappings.uniref import map_uniref

        mapped, outcome = map_uniref(
            response["clusters"],
            response["members"],
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "truncated": response.get("truncated", False),
            **outcome,
        }


ENRICHER = UniRef()
