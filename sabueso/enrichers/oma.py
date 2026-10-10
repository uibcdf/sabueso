"""OMA: the orthologs of a protein (``ortholog_of``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher

#: Every ortholog, up to a safety ceiling; a cut is reported.
DEFAULT_LIMIT = 5000


class OMA(Enricher):
    option = "oma"
    source = "OMA"
    registry_id = "oma"
    areas = ("relationships.ortholog_of",)
    option_kind = "options"
    historical_parameters = {
        "limit": "limit",
        "rel_type": "filters.rel_type",
        "taxa": "filters.taxa",
    }

    def client(self):
        from sabueso.tools.db.oma import OnlineOMAClient

        return OnlineOMAClient()

    def fetch(self, client, request, options):
        from sabueso.core.errors import ConnectorError, RecordNotFoundError
        from sabueso.mappings.oma import joined, mapped_to, names_of

        accession = request.identifier
        xrefs = client.xrefs(accession)["record"]
        if joined(xrefs, accession) is None:
            target = mapped_to(xrefs, accession)
            if not target:
                raise RecordNotFoundError(f"OMA states no exact match for {accession}")
            # Name the entry OMA chose by its own canonical id (often another strain's
            # UniProt entry), so that its card can be asked (#103).
            canonical = None
            try:
                canonical = client.protein(target["oma_id"])["record"].get(
                    "canonicalid"
                )
            except (RecordNotFoundError, ConnectorError):
                pass
            named = (
                f"{target['oma_id']} ({canonical})" if canonical else target["oma_id"]
            )
            raise RecordNotFoundError(
                f"OMA maps {accession} to {named}, whose sequence is not the "
                f"accession's (seq_match {target.get('seq_match')}); its orthologs are "
                "not joined"
            )
        found = client.orthologs(accession, options.get("rel_type"))
        orthologs = found["record"]
        taxa = options.get("taxa")
        if taxa is not None:
            orthologs = [
                o for o in orthologs if (o.get("species") or {}).get("taxon_id") in taxa
            ]
        names = names_of(orthologs[: options.get("limit", DEFAULT_LIMIT)])
        return {
            "retrieved_at": found.get("retrieved_at", ""),
            "orthologs": orthologs,
            "accessions": client.accessions(names) if names else {},
            "names": names,
        }

    def map(self, context, request, response, options):
        from sabueso.mappings.oma import map_orthologs

        mapped, outcome = map_orthologs(
            response["orthologs"],
            response["accessions"],
            context.anchor,
            response.get("retrieved_at", ""),
            options.get("limit", DEFAULT_LIMIT),
        )
        filters = {
            k: options[k] for k in ("rel_type", "taxa") if options.get(k) is not None
        }
        return mapped, {
            "status": "added" if outcome["count"] else "not_found",
            **outcome,
            **({"filters": filters} if filters else {}),
            "entry_names_resolved": len(response["accessions"]),
            "entry_names_unresolved": len(response["names"])
            - len(response["accessions"]),
        }


ENRICHER = OMA()
