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


def map_equivalences(answers: Dict[str, Any], accession: str) -> Dict[str, Any]:
    """``same_as`` (id → ``mondo:<term>``) for each id MONDO states is the same disease
    as one of its terms, each backed by a MONDO SourceAssertion (#90)."""
    assertions, relationships = [], []
    for curie, answer in sorted(answers.items()):
        mondo = answer.get("mondo")
        if not mondo or curie == mondo:
            continue
        made = make_source_assertion(
            "relationships.same_as",
            {"equivalent_id": curie, "mondo": mondo, "name": answer.get("name")},
            SOURCE,
            mondo,
            answer.get("retrieved_at") or "",
            subject_ref=curie,
        )
        if answer.get("version") is not None:
            made["source"]["version"] = str(answer["version"])
        assertions.append(made)
        qualifiers = {"basis": "mondo_equivalence@1", "source": SOURCE}
        if answer.get("name"):
            qualifiers["mondo_name"] = answer["name"]
        relationships.append(
            make_relationship(
                curie,
                "same_as",
                disease_ref(mondo),
                qualifiers=qualifiers,
                source_assertion_ids=[made["id"]],
            )
        )
    return {"source_assertions": assertions, "relationships": relationships}


HIERARCHY_RULE = "mondo_hierarchy@1"


def map_hierarchy(chains: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """``subclass_of`` (``mondo:<term>`` → ``mondo:<broader term>``) for each chain of
    ``is_a`` statements MONDO makes between two terms a card reaches (#90).

    Each step is a MONDO SourceAssertion. A chain of one step is MONDO's statement; a
    longer one is its transitive closure, which Sabueso derives
    (``mondo_hierarchy@1``) and records with every step's SourceAssertion.
    """
    from sabueso.core.relationship_store import make_derivation

    assertions: Dict[str, Dict[str, Any]] = {}
    relationships = []
    for chain in chains:
        ids = []
        for step in chain:
            made = make_source_assertion(
                "relationships.subclass_of",
                {"parent": step["parent"]},
                SOURCE,
                step["term"],
                step.get("retrieved_at") or "",
                subject_ref=disease_ref(step["term"]),
            )
            if step.get("version") is not None:
                made["source"]["version"] = str(step["version"])
            assertions.setdefault(made["id"], made)
            ids.append(made["id"])
        path = [chain[0]["term"]] + [step["parent"] for step in chain]
        relationships.append(
            make_relationship(
                disease_ref(path[0]),
                "subclass_of",
                disease_ref(path[-1]),
                qualifiers={"source": SOURCE, "path": path},
                source_assertion_ids=ids,
                derivation=make_derivation(
                    HIERARCHY_RULE,
                    inputs=["MONDO is_a"],
                    parameters={"steps": len(chain)},
                )
                if len(chain) > 1
                else None,
            )
        )
    return {
        "source_assertions": list(assertions.values()),
        "relationships": relationships,
    }
