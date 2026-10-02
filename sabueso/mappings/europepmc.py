"""Europe PMC accession mentions and derived structure mention context (#92).

One relationship per article whose text mentions the protein's UniProt accession
(``uniprot:<acc>`` → the publication), backed by a Europe PMC SourceAssertion. The
accession is written in the paper; Europe PMC found it by text mining, so each
SourceAssertion records ``acquisition: {method: database, origin: text_mining}``.

A publication is ``pubmed:<pmid>``, else ``doi:<doi>``, else Europe PMC's own id
(``europepmc:<source>:<id>``). Qualifiers: ``source``, ``mention``
(``uniprot_accession``), ``title``, ``journal``, ``year``, ``open_access``, and
``preprint`` for a preprint.

Explicit article annotations retain native locations. A printed PDB code with a
matching PDBe tag yields ``structure_mentioned_in`` only through supported
source-stated ``has_structure`` associations already mapped on the card. Raw mention
assertions are about the PDB entry; the protein context carries the named rule
``structure_mention_context@1`` and both legs of support, never whole-entry identity.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict

from sabueso.core.errors import ConnectorError
from sabueso.core.relationship_store import make_derivation, make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "Europe PMC"
MENTION = "uniprot_accession"
ANNOTATION_MAPPING = "located_accession_mapping@2"
STRUCTURE_MENTION_RULE = "structure_mention_context@1"
PDB_ID = re.compile(r"[0-9][A-Za-z0-9]{3}\Z")


def structure_associations(mappings: list[dict], accession: str) -> dict:
    """Supported source-stated has_structure links already on this card.

    The whole PDB entry is not an identity for the protein: it may be a complex or
    chimera. No structure is fetched or selected, and a derived-only link is refused.
    """
    assertions = {
        a["id"]: a for mapping in mappings for a in mapping.get("source_assertions", [])
    }
    protein = f"uniprot:{accession}"
    associations = {}
    for mapping in mappings:
        for rel in mapping.get("relationships", []):
            if (
                rel.get("predicate") != "has_structure"
                or rel.get("subject_ref") != protein
            ):
                continue
            namespace, _, identifier = str(rel.get("object_ref", "")).partition(":")
            if namespace != "pdb" or not PDB_ID.fullmatch(identifier):
                continue
            structure = f"pdb:{identifier.upper()}"
            support = []
            for sa_id in rel.get("source_assertion_ids", []):
                assertion = assertions.get(sa_id) or {}
                value = assertion.get("asserted_value")
                if (
                    assertion.get("field_path") == "relationships.has_structure"
                    and isinstance(value, dict)
                    and str(value.get("object_ref", "")).upper() == structure.upper()
                    and value.get("subject_ref", protein) == protein
                    and (
                        assertion.get("subject_ref") == protein
                        or (
                            assertion.get("subject_ref") == structure
                            and value.get("subject_ref") == protein
                        )
                    )
                ):
                    support.append(sa_id)
            if not support:
                continue
            context = associations.setdefault(
                structure,
                {
                    "protein_ref": protein,
                    "structure_ref": structure,
                    "relationship_ids": [],
                    "source_assertion_ids": [],
                    "scope": "entry_association",
                },
            )
            context["relationship_ids"] = sorted(
                set(context["relationship_ids"] + [rel["id"]])
            )
            context["source_assertion_ids"] = sorted(
                set(context["source_assertion_ids"] + support)
            )
    return associations


def pdb_annotation(annotation: dict) -> tuple[str, list[dict]] | None:
    """The printed legacy PDB code and matching source-native PDBe tag/URI."""
    exact, tags = annotation.get("exact"), annotation.get("tags")
    if (
        annotation.get("type") != "Accession Numbers"
        or annotation.get("subType") != "PDBe"
        or not isinstance(exact, str)
        or not PDB_ID.fullmatch(exact)
        or not isinstance(tags, list)
    ):
        return None
    matching = []
    for tag in tags:
        if (
            not isinstance(tag, dict)
            or not isinstance(tag.get("name"), str)
            or tag["name"].upper() != exact.upper()
        ):
            continue
        uri = tag.get("uri")
        if not isinstance(uri, str):
            continue
        namespace, _, code = uri.rpartition("/pdbe/pdb:")
        if (
            namespace in ("http://identifiers.org", "https://identifiers.org")
            and code.upper() == exact.upper()
        ):
            matching.append(tag)
    return (f"pdb:{exact.upper()}", matching) if matching else None


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
    records: list[dict],
    accession: str,
    retrieved_at: str,
    requested: str,
    structures: dict | None = None,
) -> Dict[str, Any]:
    """Source-native accession mentions, each with its own assertion and locator.

    A direct mention requires the printed UniProt accession and its native tag. A
    printed PDB code with a matching PDBe tag yields derived structure context only
    through a supported source-stated has_structure association. Names do not
    establish identity. The provider's
    pipeline version is not stated. Sabueso imports its annotations as database data.
    """
    assertions, relationships, unlinked = [], [], []
    structures = structures or {}
    subject = f"uniprot:{accession}"
    for article in records:
        identities = annotation_article_ids(article)
        publication = (
            f"pubmed:{article['extId']}"
            if article.get("source") == "MED"
            else f"europepmc:{article['source']}:{article['extId']}"
        )
        locations, support, structure_occurrences = [], [], {}
        for annotation in article["annotations"]:
            pdb = pdb_annotation(annotation)
            if pdb:
                structure, matching = pdb
                context = structures.get(structure)
                if context is None:
                    unlinked.append(
                        {
                            "structure_ref": structure,
                            "annotation_id": annotation.get("id"),
                            "reason": "no_supported_has_structure_on_card",
                        }
                    )
                    continue
                made = make_source_assertion(
                    "relationships.mentioned_in",
                    {"article": identities, "annotation": deepcopy(annotation)},
                    SOURCE,
                    f"{article['source']}:{article['extId']}",
                    retrieved_at,
                    subject_ref=structure,
                    acquisition={"method": "database", "origin": "text_mining"},
                )
                made["source_metadata"] = {
                    "content_kind": "located_accession_annotation",
                    "requested_article": requested,
                    "article": identities,
                    "identity_basis": {
                        "kind": "stated_pdb_accession",
                        "accession": structure.split(":", 1)[1],
                        "tags": deepcopy(matching),
                    },
                }
                occurrences = structure_occurrences.setdefault(structure, {})
                if made["id"] not in occurrences:
                    assertions.append(made)
                    occurrences[made["id"]] = {
                        "annotation": deepcopy(annotation),
                        "source_assertion_id": made["id"],
                    }
                continue
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
        for structure, occurrences in sorted(structure_occurrences.items()):
            context = deepcopy(structures[structure])
            support = sorted(occurrences)
            relationships.append(
                make_relationship(
                    subject,
                    "structure_mentioned_in",
                    publication,
                    qualifiers={
                        "source": SOURCE,
                        "mention": "pdb_accession",
                        "article": identities,
                        "structure_ref": structure,
                        "structure_context": context,
                        "locations": [
                            occurrences[identifier] for identifier in support
                        ],
                    },
                    source_assertion_ids=support,
                    derivation=make_derivation(
                        STRUCTURE_MENTION_RULE,
                        inputs=sorted(
                            set(
                                support
                                + context["relationship_ids"]
                                + context["source_assertion_ids"]
                            )
                        ),
                        parameters={
                            "protein_ref": subject,
                            "structure_ref": structure,
                            "scope": "entry_association",
                        },
                    ),
                )
            )
    return {
        "source_assertions": assertions,
        "relationships": relationships,
        "unlinked_pdb_mentions": unlinked,
    }


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
