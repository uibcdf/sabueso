"""Europe PMC: the publications whose text mentions the protein (``mentioned_in``)."""

from __future__ import annotations

from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.enrichers import Enricher, Request


class EuropePMC(Enricher):
    option = "europepmc"
    source = "Europe PMC"
    registry_id = "europepmc"
    areas = ("relationships.mentioned_in",)
    option_kind = "options"
    record_kinds = (None, "located_accession_annotations")

    def record(self, context, options):
        record = super().record(context, options)
        if "article_ids" in options:
            record.update(
                data="located_accession_annotations",
                article_ids=list(options["article_ids"]),
            )
        return record

    def terms_source(self, options):
        return "Europe PMC Annotations" if "article_ids" in options else self.source

    def requests(self, context, options):
        if "article_ids" not in options:
            return super().requests(context, options)
        return [
            Request(
                article_id,
                {
                    "source": self.source,
                    "identifier": article_id,
                    "article_ids": [article_id],
                    "data": "located_accession_annotations",
                },
            )
            for article_id in options["article_ids"]
        ]

    def client(self):
        from sabueso.tools.db.europepmc import OnlineEuropePMCClient

        return OnlineEuropePMCClient()

    def fetch(self, client, request, options):
        if "article_ids" in options:
            from sabueso.mappings.europepmc import validate_annotation_articles

            try:
                response = client.annotations([request.identifier])
            except RecordNotFoundError as exc:
                # A missing fixture is an unavailable answer, not an empty answer.
                raise ConnectorError(str(exc)) from exc
            validate_annotation_articles(response["record"], request.identifier)
            return response
        from sabueso.tools.db.europepmc import DEFAULT_LIMIT

        return client.mentions(request.identifier, options.get("limit", DEFAULT_LIMIT))

    def map(self, context, request, response, options):
        if "article_ids" in options:
            from sabueso.mappings.europepmc import map_annotations

            mapped = map_annotations(
                response["record"],
                context.anchor,
                response.get("retrieved_at", ""),
                request.identifier,
            )
            return mapped, {
                "status": "added",
                "version": response.get("version"),
                "count": len(mapped["relationships"]),
                "annotation_count": len(mapped["source_assertions"]),
                "returned_annotations": sum(
                    len(a["annotations"]) for a in response["record"]
                ),
                "detail": "Only accession-number annotations that explicitly state this UniProt accession are included; an empty answer does not establish absence in the article.",
            }
        from sabueso.mappings.europepmc import map_mentions
        from sabueso.tools.db.europepmc import DEFAULT_LIMIT

        record = response["record"]
        mapped = map_mentions(
            record,
            context.anchor,
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
            "truncated": record["hitCount"] > len(record["articles"]),
            "total_count": record["hitCount"],
            "limit": options.get("limit", DEFAULT_LIMIT),
        }


ENRICHER = EuropePMC()
