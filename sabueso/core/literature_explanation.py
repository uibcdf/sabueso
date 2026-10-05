"""Explain stored publication links, including both legs of structure context."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .relationship_store import make_derivation

RULE = "literature_explanation@1"


def _citation_ref(citation: dict) -> str | None:
    if citation.get("pubmed"):
        return f"pubmed:{citation['pubmed']}"
    if citation.get("doi"):
        return f"doi:{citation['doi']}"
    return None


def literature_basis(card: Any, publication: dict) -> tuple[list[dict], list[str]]:
    """Stored relationships and assertions represented by one literature-view row.

    Primary citations and measurement counts have no relationship IDs in that view;
    recover their links only through the citation fields stored on the same card.
    """
    ref = publication["publication_ref"]
    relationships = []
    for rel in card.relationships():
        q = rel.get("qualifiers") or {}
        direct = (
            rel["predicate"]
            in {"described_in", "mentioned_in", "structure_mentioned_in"}
            and rel["object_ref"] == ref
        )
        primary = (
            rel["predicate"] == "has_structure"
            and _citation_ref(q.get("primary_citation") or {}) == ref
        )
        measurement = (
            rel["predicate"] == "has_bioactivity"
            and _citation_ref(q.get("document") or {}) == ref
        )
        if direct or primary or measurement:
            relationships.append(rel)
    assertions = sorted(
        {
            row["source_assertion_id"]
            for key in ("curated", "supports", "article_metadata")
            for row in publication.get(key, [])
        }
    )
    return sorted(relationships, key=lambda r: r["id"]), assertions


def _support(card: Any, ids: list[str], pin: str) -> list[dict]:
    if not ids:
        return []
    return [
        {**record, "source_assertion_ref": f"{pin}#{record['id']}"}
        for record in card.explain(sorted(set(ids)), skip_digestion=True)
    ]


def explain_literature(card: Any, publication_ref: str) -> dict:
    """Read the current card or a loaded historical pin, without acquiring knowledge."""
    pin = card.pinned_ref()
    publication = next(
        (
            p
            for p in card.literature()["publications"]
            if p["publication_ref"] == publication_ref
        ),
        None,
    )
    relationships, ids = (
        literature_basis(card, publication) if publication else ([], [])
    )
    links = []
    requested = set()
    missing = False
    for rel in relationships:
        assertions = _support(card, rel.get("source_assertion_ids") or [], pin)
        missing |= any(not a["found"] for a in assertions)
        for identifier in rel.get("source_assertion_ids") or []:
            sa = card.source_assertion_store.get(identifier) or {}
            article = (sa.get("source_metadata") or {}).get("requested_article")
            if article:
                requested.add(article)
        contexts = []
        q = rel.get("qualifiers") or {}
        candidates = [q["structure_context"]] if q.get("structure_context") else []
        candidates += (rel.get("qualifier_conflicts") or {}).get(
            "structure_context"
        ) or []
        for context in candidates:
            structural = []
            for identifier in context.get("relationship_ids") or []:
                held = card.relationship_store.get(identifier)
                found = held is not None
                support = _support(
                    card, (held or {}).get("source_assertion_ids") or [], pin
                )
                missing |= not found or any(not a["found"] for a in support)
                structural.append(
                    {
                        "relationship_ref": f"{pin}#{identifier}",
                        "found": found,
                        "relationship": held,
                        "source_assertions": support,
                    }
                )
            support = _support(card, context.get("source_assertion_ids") or [], pin)
            missing |= any(not a["found"] for a in support)
            contexts.append(
                {
                    "context": context,
                    "relationships": structural,
                    "source_assertions": support,
                }
            )
        links.append(
            {
                "relationship_ref": f"{pin}#{rel['id']}",
                "relationship": rel,
                "source_assertions": assertions,
                "structure_contexts": contexts,
            }
        )
    support = _support(card, ids, pin)
    missing |= any(not a["found"] for a in support)
    if publication_ref.startswith("pubmed:"):
        requested.add("MED:" + publication_ref.split(":", 1)[1])
    elif publication_ref.startswith("europepmc:"):
        requested.add(publication_ref[len("europepmc:") :])
    requests = [
        r
        for r in card.quality.get("enrichments") or []
        if r.get("source") == "Europe PMC"
        and r.get("data") == "located_accession_annotations"
        and set(r.get("article_ids") or []).intersection(requested)
    ]
    unlinked = [
        {"request": r.get("article_ids"), "mapping": r.get("mapping"), **row}
        for r in requests
        for row in r.get("unlinked_pdb_mentions") or []
    ]
    return deepcopy(
        {
            "rule": make_derivation(
                RULE, inputs=[pin], parameters={"publication_ref": publication_ref}
            ),
            "card_ref": pin,
            "publication_ref": publication_ref,
            "status": "partial"
            if missing
            else "on_card"
            if publication
            else "not_on_card",
            "reason": "missing_stored_support"
            if missing
            else None
            if publication
            else "no_stored_publication_link",
            "publication": publication,
            "links": links,
            "source_assertions": support,
            "annotation_requests": requests,
            "unlinked_pdb_mentions": unlinked,
            "support_basis": "stored_relationships_and_source_assertions",
        }
    )
