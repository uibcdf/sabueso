"""DISEASES: gene–disease associations per channel (``associated_with``)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request

DEFAULT_CHANNELS = ("knowledge", "experiments")


class DISEASES(Enricher):
    option = "diseases"
    source = "DISEASES"
    registry_id = "diseases_jensen"
    areas = ("relationships.associated_with",)
    organisms = (9606,)
    coverage_detail = "DISEASES covers Homo sapiens genes only"
    option_kind = "options"

    def client(self):
        from sabueso.tools.db.diseases import OnlineDISEASESClient

        return OnlineDISEASESClient()

    def record(self, context, options):
        channels = tuple(options.get("channels") or DEFAULT_CHANNELS)
        return {**super().record(context, options), "channels": channels}

    def requests(self, context, options):
        isoform_of = {
            value.split(".")[0]: isoform
            for value, isoform in context.xref_properties("Ensembl", "ProteinId")
        }
        if not isoform_of:
            raise NothingToAsk("the entry cross-references no Ensembl protein")
        record = self.record(context, options)
        return [
            Request(
                context.anchor,
                record,
                {"isoform_of": isoform_of, "channels": record["channels"]},
            )
        ]

    def fetch(self, client, request, options):
        return client.associations(
            sorted(request.args["isoform_of"]), request.args["channels"]
        )

    def map(self, context, request, response, options):
        from sabueso.mappings.diseases import map_associations

        versions = response.get("version") or {}
        mapped = map_associations(
            response["record"],
            context.anchor,
            request.args["isoform_of"],
            response.get("retrieved_at", ""),
            versions,
        )
        return mapped, {
            "status": "added" if mapped["relationships"] else "not_found",
            "version": "; ".join(f"{c} {v}" for c, v in sorted(versions.items()) if v)
            or None,
            "count": len(mapped["relationships"]),
        }


ENRICHER = DISEASES()
