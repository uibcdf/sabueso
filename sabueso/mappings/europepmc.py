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

from copy import deepcopy
from typing import Any, Dict

from sabueso.core.errors import ConnectorError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Europe PMC"
MENTION = "uniprot_accession"


def annotation_article_ids(article: Dict[str, Any]) -> Dict[str, Any]:
    """Only identifiers the annotation response itself states."""
    return {
        key: deepcopy(article[key])
        for key in ("source", "extId", "pmcid", "fullTextIdList")
        if article.get(key)
    }


def validate_annotation_articles(records: Any, requested: str) -> None:
    """Refuse unrelated or unreadable answers; never infer a MED/PMC equivalence."""
    if not isinstance(records, list):
        raise ConnectorError("Europe PMC annotations returned an unreadable record")
    for article in records:
        if not isinstance(article, dict) or not isinstance(
            article.get("annotations"), list
        ):
            raise ConnectorError(
                "Europe PMC annotations returned an unreadable article"
            )
        from sabueso._private.argdigest.argument.article_ids import ARTICLE_ID

        if not ARTICLE_ID.fullmatch(f"{article.get('source')}:{article.get('extId')}"):
            raise ConnectorError(
                "Europe PMC annotations returned an unreadable article id"
            )
        ids = {f"{article.get('source')}:{article.get('extId')}"}
        if article.get("pmcid"):
            ids.add(f"PMC:{article['pmcid']}")
        full_text_ids = article.get("fullTextIdList") or []
        if not isinstance(full_text_ids, list) or any(
            not isinstance(identifier, str) for identifier in full_text_ids
        ):
            raise ConnectorError(
                "Europe PMC annotations returned unreadable full-text ids"
            )
        ids.update(f"PMC:{identifier}" for identifier in full_text_ids)
        if requested not in ids:
            raise ConnectorError(
                f"Europe PMC returned an article not identified as {requested}"
            )
        if any(
            not isinstance(annotation, dict) for annotation in article["annotations"]
        ):
            raise ConnectorError(
                "Europe PMC annotations returned an unreadable annotation"
            )
        for annotation in article["annotations"]:
            if any(
                annotation.get(key) is not None and not isinstance(annotation[key], str)
                for key in (
                    "id",
                    "provider",
                    "section",
                    "prefix",
                    "exact",
                    "postfix",
                    "type",
                    "subType",
                )
            ):
                raise ConnectorError(
                    "Europe PMC annotations returned an unreadable locator"
                )
            tags = annotation.get("tags")
            if tags is not None and (
                not isinstance(tags, list)
                or any(not isinstance(tag, dict) for tag in tags)
            ):
                raise ConnectorError("Europe PMC annotations returned unreadable tags")


def map_annotations(
    records: list[dict], accession: str, retrieved_at: str, requested: str
) -> Dict[str, Any]:
    """Source-native accession mentions, each with its own assertion and locator.

    Both the printed accession and its UniProt tag must identify the card's anchor.
    Names and other accession types do not establish this relationship. The provider's
    pipeline version is not stated. Sabueso imports its annotations as database data.
    """
    assertions, relationships = [], []
    subject = f"uniprot:{accession}"
    for article in records:
        identities = annotation_article_ids(article)
        publication = (
            f"pubmed:{article['extId']}"
            if article.get("source") == "MED"
            else f"europepmc:{article['source']}:{article['extId']}"
        )
        locations, support = [], []
        for annotation in article["annotations"]:
            tags = annotation.get("tags")
            if (
                annotation.get("type") != "Accession Numbers"
                or annotation.get("subType") != "UniProt"
                or annotation.get("exact") != accession
                or not isinstance(tags, list)
            ):
                continue
            matching = [
                tag
                for tag in tags
                if isinstance(tag, dict)
                and tag.get("name") == accession
                and tag.get("uri")
                in {
                    f"http://identifiers.org/uniprot:{accession}",
                    f"https://identifiers.org/uniprot:{accession}",
                }
            ]
            if not matching:
                continue
            value = {"article": identities, "annotation": deepcopy(annotation)}
            made = make_source_assertion(
                "relationships.mentioned_in",
                value,
                SOURCE,
                f"{article['source']}:{article['extId']}",
                retrieved_at,
                subject_ref=subject,
                acquisition={"method": "database", "origin": "text_mining"},
            )
            made["source_metadata"] = {
                "content_kind": "located_accession_annotation",
                "requested_article": requested,
                "article": identities,
                "identity_basis": {
                    "kind": "stated_uniprot_accession",
                    "accession": accession,
                    "tags": deepcopy(matching),
                },
            }
            if made["id"] in support:
                continue
            assertions.append(made)
            support.append(made["id"])
            locations.append(
                {"annotation": deepcopy(annotation), "source_assertion_id": made["id"]}
            )
        if support:
            relationships.append(
                make_relationship(
                    subject,
                    "mentioned_in",
                    publication,
                    qualifiers={
                        "source": SOURCE,
                        "mention": MENTION,
                        "article": identities,
                        "locations": locations,
                    },
                    source_assertion_ids=support,
                )
            )
    return {"source_assertions": assertions, "relationships": relationships}


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
