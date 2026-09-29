"""MedGen concept ids → their MedGen records (``same_as``, rule ``medgen_concept@1``, #90).

One ``same_as`` per concept id MedGen answered: ``MEDGEN:C1860808`` →
``MEDGEN:349893``, backed by a MedGen SourceAssertion. It lets a condition named only by
a MedGen concept id reach MONDO, whose equivalences name MedGen records by UID.
"""

from __future__ import annotations

from typing import Any, Dict

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "MedGen"
RULE = "medgen_concept@1"


def map_concepts(
    record: Dict[str, str], retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    assertions, relationships = [], []
    for concept, uid in sorted(record.items()):
        subject = f"MEDGEN:{concept}"
        made = make_source_assertion(
            "relationships.same_as",
            {"concept_id": concept, "uid": uid},
            SOURCE,
            uid,
            retrieved_at,
            subject_ref=subject,
        )
        if version is not None:
            made["source"]["version"] = str(version)
        assertions.append(made)
        relationships.append(
            make_relationship(
                subject,
                "same_as",
                f"MEDGEN:{uid}",
                qualifiers={"basis": RULE, "source": SOURCE},
                source_assertion_ids=[made["id"]],
            )
        )
    return {"source_assertions": assertions, "relationships": relationships}
