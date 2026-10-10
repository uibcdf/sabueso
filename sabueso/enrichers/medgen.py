"""MedGen: the record (UID) of each MedGen concept id naming a condition (#90)."""

from __future__ import annotations

from sabueso.enrichers import Enricher, Request, RequestPrerequisiteMissing


def concept_ids(context) -> list:
    """The MedGen concept ids (``C…``, ``CN…``) of the card's disease statements,
    ClinVar's placeholders left out."""
    from sabueso.core.diseases import CLINVAR_PLACEHOLDERS, disease_statements

    fields, relationships = {}, []
    for mapping in context.mappings:
        fields.update(mapping.get("fields") or {})
        relationships.extend(mapping.get("relationships") or [])
    return sorted(
        {
            c.split(":", 1)[1]
            for s in disease_statements(fields.get, relationships)
            for c in s["curies"]
            if c.startswith("MEDGEN:C") and c not in CLINVAR_PLACEHOLDERS
        }
    )


class MedGen(Enricher):
    option = "medgen"
    source = "MedGen"
    registry_id = "medgen"
    areas = ("relationships.same_as (MedGen)",)

    def client(self):
        from sabueso.tools.db.medgen import OnlineMedGenClient

        return OnlineMedGenClient()

    def requests(self, context, options):
        ids = concept_ids(context)
        if not ids:
            raise RequestPrerequisiteMissing(
                "no disease on the card is named by a MedGen concept id"
            )
        return [
            Request(
                context.anchor,
                {"source": self.source, "identifier": context.anchor},
                {"concept_ids": ids},
            )
        ]

    def fetch(self, client, request, options):
        return client.concepts(request.args["concept_ids"])

    def map(self, context, request, response, options):
        from sabueso.mappings.medgen import map_concepts

        mapped = map_concepts(
            response["record"],
            response.get("retrieved_at", ""),
            response.get("version"),
        )
        return mapped, {
            "status": "added" if response["record"] else "not_found",
            "version": response.get("version"),
            "count": len(mapped["relationships"]),
            "missing": response.get("missing") or [],
        }


ENRICHER = MedGen()
