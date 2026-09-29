"""MONDO: which of a protein's disease ids are the same disease (``same_as``, #90)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, NothingToAsk, Request


class DiseaseIdentity(Enricher):
    option = "disease_identity"
    source = "MONDO"
    registry_id = "mondo"
    areas = ("relationships.same_as (MONDO)",)
    client_option = "mondo_client"
    #: Last: it reads the diseases every other source put on the card.
    stage = "after_bioactivity"

    def client(self):
        from sabueso.tools.db.mondo import OnlineMONDOClient

        return OnlineMONDOClient()

    def requests(self, context, options):
        from sabueso.core.diseases import disease_statements

        fields, relationships = {}, []
        for mapping in context.mappings:
            fields.update(mapping.get("fields") or {})
            relationships.extend(mapping.get("relationships") or [])
        statements = disease_statements(fields.get, relationships)
        if not statements:
            raise NothingToAsk("the card names no disease")
        curies = sorted({s["curie"] for s in statements if s.get("curie")})
        unmapped = sorted({s["ref"] for s in statements if not s.get("curie")})
        return [
            Request(
                context.anchor,
                {"source": self.source, "identifier": context.anchor},
                {"curies": curies, "unmapped": unmapped},
            )
        ]

    def fetch(self, client, request, options):
        answers = {}
        for curie in request.args["curies"]:
            if curie.startswith("MONDO:"):
                term = client.term(curie)
                record = term["record"]
                answers[curie] = {
                    "version": term.get("version"),
                    "retrieved_at": term.get("retrieved_at"),
                    "mondo": None if record.get("obsolete") else curie,
                    "obsolete": bool(record.get("obsolete")),
                }
                continue
            answer = client.equivalent(curie)
            if answer.get("mondo"):
                record = client.term(answer["mondo"])["record"]
                answer["name"] = record.get("name")
            answers[curie] = answer
        return answers

    def map(self, context, request, response, options):
        from sabueso.mappings.mondo import map_equivalences

        mapped = map_equivalences(response, context.anchor)
        ungrouped = [
            {
                "curie": c,
                "reason": "obsolete_term"
                if a.get("obsolete")
                else "no_stated_equivalence",
            }
            for c, a in sorted(response.items())
            if not a.get("mondo")
        ]
        versions = sorted({a.get("version") for a in response.values()} - {None})
        return mapped, {
            "status": "added" if mapped["relationships"] else "not_found",
            "version": "; ".join(versions) or None,
            "count": len(mapped["relationships"]),
            "ids": len(response),
            "ungrouped": ungrouped
            + [
                {"curie": r, "reason": "namespace_not_mapped"}
                for r in request.args["unmapped"]
            ],
        }


ENRICHER = DiseaseIdentity()
