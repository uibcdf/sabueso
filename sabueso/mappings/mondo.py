"""A MONDO term → a disease card (#90).

The card is anchored at the MONDO term (``mondo:MONDO:0014221``). It holds what MONDO
states about it:

- ``identifiers.mondo``;
- ``identifiers.equivalent_ids``: the external ids MONDO states are the same disease
  (``MONDO:equivalentTo``). They are what joins other sources' diseases to this card;
- ``identifiers.related_ids``: the other xrefs, related terms that are *not* the same
  disease, kept apart so that they are never read as identity;
- ``names.canonical_name`` and ``names.synonyms`` (``{name, kind}``, the kind being
  MONDO's scope: ``exact_synonym``, ``related_synonym``, ``broad_synonym``,
  ``narrow_synonym``);
- ``annotations.definition`` (``{text, references}``) and ``annotations.disease_subsets``;
- ``subclass_of`` relationships to its parent terms, as MONDO states them.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "MONDO"


def disease_ref(mondo_id: str) -> str:
    return f"mondo:{mondo_id}"


def map_disease(
    term: Dict[str, Any], retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    subject = disease_ref(term["id"])
    fields: Dict[str, Any] = {}
    field_source_assertions: Dict[str, List[str]] = {}
    assertions: List[Dict[str, Any]] = []

    def assertion(path: str, value: Any) -> Dict[str, Any]:
        made = make_source_assertion(
            path, value, SOURCE, term["id"], retrieved_at, subject_ref=subject
        )
        if version is not None:
            made["source"]["version"] = str(version)
        assertions.append(made)
        return made

    def field(path: str, value: Any) -> None:
        if value in (None, "", []):
            return
        fields[path] = value
        field_source_assertions[path] = [assertion(path, value)["id"]]

    field("identifiers.mondo", term["id"])
    field(
        "identifiers.equivalent_ids",
        sorted(x["id"] for x in term.get("xrefs") or [] if x["equivalent"]),
    )
    field(
        "identifiers.related_ids",
        sorted(x["id"] for x in term.get("xrefs") or [] if not x["equivalent"]),
    )
    field("names.canonical_name", term.get("name"))
    field(
        "names.synonyms",
        [
            {"name": s["name"], "kind": f"{s['scope']}_synonym"}
            for s in term.get("synonyms") or []
        ],
    )
    field("annotations.definition", term.get("definition"))
    field("annotations.disease_subsets", sorted(term.get("subsets") or []))

    relationships = []
    for parent in term.get("parents") or []:
        made = assertion("relationships.subclass_of", {"parent": parent})
        relationships.append(
            make_relationship(
                subject,
                "subclass_of",
                disease_ref(parent),
                source_assertion_ids=[made["id"]],
            )
        )
    return {
        "fields": fields,
        "field_source_assertions": field_source_assertions,
        "source_assertions": assertions,
        "relationships": relationships,
    }
