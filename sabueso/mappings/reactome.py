"""Reactome events → ``participates_in`` relationships (protein → pathway/reaction; #83).

One relationship per Reactome event that maps the card's UniProt accession: the
lowest-level pathways naming it and the reactions it takes part in. Qualifiers keep
Reactome's ``kind`` (``pathway`` or ``reaction``), the event's name and species,
``is_inferred`` (inferred by Reactome from orthology, for non-human species) and, for a
pathway, its ``ancestors``: each path up to a top-level pathway, as Reactome states it.
"""

from __future__ import annotations

from typing import Any, Dict

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Reactome"


def map_pathways(
    record: Dict[str, Any], accession: str, retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    assertions, relationships = [], []
    ancestors = record.get("ancestors") or {}
    for kind, events in (
        ("pathway", record.get("pathways")),
        ("reaction", record.get("reactions")),
    ):
        for event in sorted(events or [], key=lambda e: e.get("stId") or ""):
            st_id = event.get("stId")
            if not st_id:
                continue
            assertion = make_source_assertion(
                "relationships.participates_in",
                {**event, "ancestors": ancestors.get(st_id)}
                if kind == "pathway"
                else event,
                SOURCE,
                st_id,
                retrieved_at,
                subject_ref=f"uniprot:{accession}",
            )
            if version is not None:
                assertion["source"]["version"] = str(version)
            assertions.append(assertion)
            qualifiers = {
                "kind": kind,
                "name": event.get("displayName"),
                "species": event.get("speciesName"),
                "is_inferred": event.get("isInferred"),
            }
            if kind == "pathway":
                qualifiers["ancestors"] = [
                    [{"id": e.get("stId"), "name": e.get("displayName")} for e in path]
                    for path in ancestors.get(st_id) or []
                ]
            relationships.append(
                make_relationship(
                    f"uniprot:{accession}",
                    "participates_in",
                    f"reactome:{st_id}",
                    qualifiers={k: v for k, v in qualifiers.items() if v is not None},
                    source_assertion_ids=[assertion["id"]],
                )
            )
    return {"source_assertions": assertions, "relationships": relationships}
