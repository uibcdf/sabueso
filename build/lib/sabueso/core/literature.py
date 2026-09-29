"""Which publications support which statements on a card (uibcdf/sabueso#41, part 1).

A publication reaches a card in three ways, and ``literature_view`` puts them together per
publication (``pubmed:<id>``, else ``doi:<doi>``, else UniProt's own citation id):

- a source cites it for a topic: ``described_in`` relationships, for example a UniProt
  reference with its scope (``X-RAY CRYSTALLOGRAPHY``, ``HOMODIMERIZATION``...);
- it is the primary citation of a structure on the card (RCSB, on ``has_structure``);
- measurements on the card come from it (ChEMBL documents, ``measurements``);
- a person curated what it states onto the card (``curated``, part 2 of #41, with the
  outcome of comparing it with other sources);
- a source gives it as evidence of a statement: the PubMed ids in a SourceAssertion's
  ``eco`` evidence, and UniProt's ``Ref.<n>`` evidences, resolved through the entry's
  reference numbers.

Nothing here reads a paper. How a publication bears on a project's hypotheses is Nextia
Evidence, not Sabueso's.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _summary(value: Any) -> Any:
    """A short, readable form of an asserted value."""
    if isinstance(value, dict):
        for key in (
            "description",
            "name",
            "reaction",
            "location",
            "text",
            "value",
            "object_ref",
        ):
            if value.get(key):
                return value[key]
        return None
    return value


def literature_view(card: Any) -> Dict[str, Any]:
    """``{"publications", "unresolved_eco"}``; publications in chronological order."""
    publications: Dict[str, Dict[str, Any]] = {}
    by_reference_number: Dict[Any, str] = {}

    def entry(ref: str) -> Dict[str, Any]:
        return publications.setdefault(
            ref,
            {
                "publication_ref": ref,
                "title": None,
                "journal": None,
                "year": None,
                "pubmed": ref.split(":", 1)[1] if ref.startswith("pubmed:") else None,
                "doi": ref.split(":", 1)[1] if ref.startswith("doi:") else None,
                "cited_by": [],
                "primary_citation_of": [],
                "supports": [],
                "curated": [],
                "measurements": 0,
            },
        )

    def fill(pub: Dict[str, Any], record: Dict[str, Any]) -> None:
        for key in ("title", "journal", "year", "pubmed", "doi"):
            if pub.get(key) is None and record.get(key) is not None:
                pub[key] = str(record[key]) if key == "year" else record[key]

    for rel in card.relationships("described_in"):
        q = rel.get("qualifiers", {})
        pub = entry(rel["object_ref"])
        fill(pub, q)
        sources = sorted(
            {
                card.source_assertion_store.get(sa)["source"]["name"]
                for sa in rel.get("source_assertion_ids", [])
                if card.source_assertion_store.get(sa)
            }
        )
        pub["cited_by"].append(
            {
                "sources": sources,
                "citation_type": q.get("citation_type"),
                "scope": q.get("scope") or [],
                "comments": q.get("comments") or [],
                "relationship_id": rel["id"],
            }
        )
        if q.get("reference_number") is not None:
            by_reference_number[f"Ref.{q['reference_number']}"] = rel["object_ref"]

    for rel in card.relationships("has_structure"):
        citation = rel.get("qualifiers", {}).get("primary_citation")
        if not citation:
            continue
        if citation.get("pubmed"):
            ref = f"pubmed:{citation['pubmed']}"
        elif citation.get("doi"):
            ref = f"doi:{citation['doi']}"
        else:
            continue
        pub = entry(ref)
        fill(pub, citation)
        pub["primary_citation_of"].append(rel["object_ref"])

    for rel in card.relationships("has_bioactivity"):
        document = rel.get("qualifiers", {}).get("document") or {}
        if document.get("pubmed"):
            ref = f"pubmed:{document['pubmed']}"
        elif document.get("doi"):
            ref = f"doi:{document['doi']}"
        else:
            continue
        pub = entry(ref)
        fill(pub, document)
        pub["measurements"] += 1

    outcomes = {
        r["source_assertion_id"]: r for r in card.quality.get("curation", []) or []
    }
    unresolved: List[Dict[str, Any]] = []
    for assertion in card.source_assertion_store.to_list():
        source = assertion.get("source") or {}
        if source.get("type") == "literature" and source.get("record_id"):
            curation = (assertion.get("source_metadata") or {}).get("curation") or {}
            record = outcomes.get(assertion["id"]) or {}
            entry(source["record_id"])["curated"].append(
                {
                    "field_path": assertion.get("field_path"),
                    "value": _summary(assertion.get("asserted_value")),
                    "locator": curation.get("locator"),
                    "quote": curation.get("quote"),
                    "curator": curation.get("curator"),
                    "curated_at": curation.get("curated_at"),
                    "outcome": record.get("outcome"),
                    "source_assertion_id": assertion["id"],
                }
            )
        for evidence in (assertion.get("source_metadata") or {}).get("eco") or []:
            source, identifier = evidence.get("source"), evidence.get("id")
            if source == "PubMed" and identifier:
                ref = f"pubmed:{identifier}"
            elif source == "Reference" and identifier in by_reference_number:
                ref = by_reference_number[identifier]
            else:
                if source == "Reference":
                    unresolved.append(
                        {"evidence": identifier, "source_assertion_id": assertion["id"]}
                    )
                continue
            entry(ref)["supports"].append(
                {
                    "field_path": assertion.get("field_path"),
                    "value": _summary(assertion.get("asserted_value")),
                    "eco_code": evidence.get("code"),
                    "source": (assertion.get("source") or {}).get("name"),
                    "source_assertion_id": assertion["id"],
                }
            )

    for pub in publications.values():
        pub["primary_citation_of"].sort()
        pub["supports"].sort(key=lambda s: (s["field_path"] or "", str(s["value"])))
    ordered = sorted(
        publications.values(), key=lambda p: (p["year"] or "9999", p["publication_ref"])
    )
    return {"publications": ordered, "unresolved_eco": unresolved}
