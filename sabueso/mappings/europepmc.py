"""Europe PMC mentions → ``mentioned_in`` relationships (#92).

One relationship per article whose text mentions the protein's UniProt accession
(``uniprot:<acc>`` → the publication), backed by a Europe PMC SourceAssertion. The
accession is written in the paper; Europe PMC found it by text mining, so each
SourceAssertion records ``acquisition: {method: database, origin: text_mining}``.

A publication is ``pubmed:<pmid>``, else ``doi:<doi>``, else Europe PMC's own id
(``europepmc:<source>:<id>``). Qualifiers: ``source``, ``mention``
(``uniprot_accession``), ``title``, ``journal``, ``year``, ``open_access``, and
``preprint`` for a preprint.
"""

from __future__ import annotations

from typing import Any, Dict

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Europe PMC"
MENTION = "uniprot_accession"


def publication_ref(article: Dict[str, Any]) -> str:
    if article.get("pmid"):
        return f"pubmed:{article['pmid']}"
    if article.get("doi"):
        return f"doi:{article['doi']}"
    return f"europepmc:{article.get('source')}:{article.get('id')}"


def map_mentions(
    record: Dict[str, Any], accession: str, retrieved_at: str, version: str | None
) -> Dict[str, Any]:
    subject = f"uniprot:{accession}"
    assertions, relationships = [], []
    for article in record.get("articles") or []:
        publication = publication_ref(article)
        made = make_source_assertion(
            "relationships.mentioned_in",
            {"accession": accession, "publication": publication},
            SOURCE,
            f"{article.get('source')}:{article.get('id')}",
            retrieved_at,
            subject_ref=subject,
            acquisition={"method": "database", "origin": "text_mining"},
        )
        if version is not None:
            made["source"]["version"] = str(version)
        made["source_metadata"] = {"query": record.get("query")}
        assertions.append(made)
        qualifiers = {
            "source": SOURCE,
            "mention": MENTION,
            "title": article.get("title"),
            "journal": article.get("journalTitle"),
            "year": article.get("pubYear"),
            "open_access": article.get("isOpenAccess") == "Y",
        }
        if article.get("source") == "PPR":
            qualifiers["preprint"] = True
        relationships.append(
            make_relationship(
                subject,
                "mentioned_in",
                publication,
                qualifiers={k: v for k, v in qualifiers.items() if v is not None},
                source_assertion_ids=[made["id"]],
            )
        )
    return {"source_assertions": assertions, "relationships": relationships}
