"""Source-stated article identity and bibliography, separately from text extraction."""

import re
from copy import deepcopy

from .errors import ConnectorError, SchemaError
from .snapshot import canonical_json, digest
from .source_assertion_store import generate_source_assertion_id, make_source_assertion

FIELDS = (
    "id",
    "source",
    "pmid",
    "pmcid",
    "doi",
    "title",
    "authorString",
    "authorList",
    "journalInfo",
    "pubYear",
    "firstPublicationDate",
    "license",
    "isOpenAccess",
    "fullTextUrlList",
    "fullTextIdList",
    "pubTypeList",
    "pageInfo",
)
IDENTIFIER = re.compile(r"pubmed:[1-9][0-9]*|pmc:PMC[1-9][0-9]*|doi:10\.[0-9]{4,9}/\S+")


def normalize(identifier):
    from sabueso._private.argdigest._shared import refuse

    if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
        raise refuse(
            "identifier",
            identifier,
            "sabueso.tools.db.europepmc.get_article",
            "expected pubmed:<id>, pmc:PMC<id> or doi:10.<...>",
        )
    return identifier


def query(identifier):
    normalize(identifier)
    kind, value = identifier.split(":", 1)
    if kind == "pubmed":
        return f"EXT_ID:{value} AND SRC:MED"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'{"PMCID" if kind == "pmc" else "DOI"}:"{escaped}"'


def fixture_name(identifier):
    normalize(identifier)
    kind, value = identifier.split(":", 1)
    return f"{kind}__{digest(value)[7:] if kind == 'doi' else value}.json"


def matches(article, identifier):
    if not isinstance(article, dict):
        return False
    kind, value = identifier.split(":", 1)
    if kind == "pubmed":
        return article.get("pmid") == value or (
            article.get("source") == "MED" and article.get("id") == value
        )
    if kind == "pmc":
        return article.get("pmcid") == value or (
            article.get("source") == "PMC" and article.get("id") == value
        )
    return (
        isinstance(article.get("doi"), str)
        and article["doi"].casefold() == value.casefold()
    )


def project(article):
    return {key: deepcopy(article[key]) for key in FIELDS if key in article}


def response(payload, identifier):
    """Refuse unrelated/unreadable results; retain every matching result, never pick."""
    try:
        articles = payload["resultList"]["result"]
        total = payload["hitCount"]
        if (
            type(total) is not int
            or total < 0
            or not isinstance(articles, list)
            or len(articles) > total
        ):
            raise ValueError("invalid result count or list")
        if any(not matches(article, identifier) for article in articles):
            raise ValueError("an article does not state the requested identifier")
        return {
            "requested_identifier": identifier,
            "query": query(identifier),
            "total_count": total,
            "articles": [project(a) for a in articles],
            "truncated": total > len(articles),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise ConnectorError(
            f"Europe PMC article metadata is unreadable: {error}"
        ) from error


def article_terms(article):
    """A licence literal is a declaration, not a normalized licence or fragment grant."""
    value = deepcopy(article.get("license"))
    return {
        "state": "declared" if value is not None else "unknown",
        "scope": "source_declared_article_license",
        "value": value,
        "basis": "Europe_PMC_core_license_field" if value is not None else "not_stated",
        "fragment_terms": "unknown",
        "license_version": "not_inferred",
    }


def citations(articles):
    items, gaps = [], []
    for article in articles:
        item = {"type": "article"}
        journal = article.get("journalInfo") or {}
        nested = (journal.get("journal") or {}) if isinstance(journal, dict) else {}
        for key, value in {
            "title": article.get("title"),
            "doi": article.get("doi"),
            "journal": nested.get("title") if isinstance(nested, dict) else None,
            "volume": journal.get("volume") if isinstance(journal, dict) else None,
            "number": journal.get("issue") if isinstance(journal, dict) else None,
            "pages": article.get("pageInfo"),
        }.items():
            if isinstance(value, str) and value:
                item[key] = value
        year = article.get("pubYear")
        if isinstance(year, (str, int)) and str(year).isdigit():
            item["year"] = int(year)
        authors = article.get("authorList") or {}
        authors = authors.get("author") if isinstance(authors, dict) else None
        if (
            isinstance(authors, list)
            and authors
            and all(
                isinstance(a, dict)
                and (
                    isinstance(a.get("fullName"), str)
                    and a["fullName"]
                    or isinstance(a.get("collectiveName"), str)
                    and a["collectiveName"]
                )
                for a in authors
            )
        ):
            item["authors"] = [
                {"literal": a["collectiveName"]}
                if isinstance(a.get("collectiveName"), str) and a["collectiveName"]
                else {"family": a["lastName"], "given": a.get("firstName", "")}
                if a.get("lastName")
                else {"literal": a["fullName"]}
                for a in authors
            ]
        elif isinstance(article.get("authorString"), str) and article["authorString"]:
            item["authors"] = [{"literal": article["authorString"]}]
            gaps.append("author_list_not_returned_preserved_native_author_string")
        if item.get("doi"):
            item["url"] = "https://doi.org/" + item["doi"]
        else:
            pmid = article.get("pmid") or (
                article.get("id") if article.get("source") == "MED" else None
            )
            if isinstance(pmid, str) and re.fullmatch(r"[1-9][0-9]*", pmid):
                item["url"] = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
        missing = [
            key
            for key in (
                "title",
                "authors",
                "year",
                "journal",
                "volume",
                "number",
                "pages",
            )
            if key not in item
        ]
        gaps.extend("article_" + key + "_not_stated" for key in missing)
        # Original incomplete/native forms cannot overwrite fuller host references.
        item["id"] = "sabueso:article-publication:" + digest(
            canonical_json(
                {
                    "citation": item,
                    "native_ids": {
                        k: article.get(k)
                        for k in ("id", "source", "pmid", "pmcid", "doi")
                    },
                }
            )
        )
        items.append(item)
    return items, sorted(set(gaps))


def prepare(envelope, publication):
    """Attach explicit metadata only when the returned source states this identity."""
    try:
        record = envelope["record"]
        articles = record["articles"]
        identifier = record["requested_identifier"]
        normalize(identifier)
        if (
            envelope["source"] != "Europe PMC"
            or envelope["kind"] != "article"
            or envelope["query"] != {"identifier": identifier}
            or record["query"] != query(identifier)
        ):
            raise ValueError("not an explicit Europe PMC article envelope")
        if (
            set(record)
            != {"requested_identifier", "query", "total_count", "articles", "truncated"}
            or type(record["total_count"]) is not int
            or type(record["truncated"]) is not bool
            or not isinstance(articles, list)
            or record["truncated"]
            or record["total_count"] != 1
            or len(articles) != 1
            or not matches(articles[0], identifier)
            or not matches(articles[0], publication)
        ):
            raise ValueError(
                "metadata is absent, ambiguous or does not state the fragment publication"
            )
        when = envelope["retrieved_at"]
        if not isinstance(when, str) or not when:
            raise ValueError("missing original metadata retrieval time")
        article = project(articles[0])
        if article != articles[0]:
            raise ValueError(
                "metadata must use the bibliographic projection without text"
            )
        version = envelope.get("version")
        original_trace = envelope.get("acquisition_trace")
        if original_trace is not None:
            records = original_trace["records"]
            if not isinstance(records, list) or any(
                r.get("source") != "Europe PMC"
                or r.get("operation") != "article"
                or r.get("query") != {"identifier": identifier}
                or r.get("source_version", {}).get("value") != version
                or r.get("retrieved_at") != when
                or r.get("outcome") != "received"
                or [
                    e.get("article")
                    for e in r.get("entries", [])
                    if e.get("outcome") == "received"
                ]
                != articles
                for r in records
            ):
                raise ValueError("original metadata receipt does not match the lookup")
        native = article.get("source"), article.get("id")
        record_id = (
            ":".join(native)
            if all(isinstance(v, str) and v for v in native)
            else identifier
        )
        assertion = make_source_assertion(
            "literature.article_metadata",
            article,
            "Europe PMC",
            record_id,
            when,
            subject_ref=publication,
        )
        assertion["source_metadata"] = {
            "content_kind": "article_metadata",
            "requested_identifier": identifier,
            "publication_ref": publication,
            "identity_basis": "source_stated_publication_identifier",
            "service_version": version,
            "version_basis": "service_version_not_article_revision",
        }
        # Binding aliases and service-version declarations are distinct support.
        # Include their explicit context in identity, never a retrieval timestamp.
        assertion["id"] = generate_source_assertion_id(
            "Europe PMC",
            record_id,
            "literature.article_metadata",
            {"article": article, "binding": assertion["source_metadata"]},
        )
        return {
            "format": "sabueso.article_metadata_binding@1",
            "publication_ref": publication,
            "envelope": {
                k: deepcopy(envelope[k])
                for k in (
                    "source",
                    "kind",
                    "query",
                    "retrieved_at",
                    "version",
                    "record",
                )
            },
            "source_assertion": assertion,
            "original_acquisition_trace": deepcopy(envelope.get("acquisition_trace")),
        }
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise SchemaError(f"Invalid article metadata binding: {error}") from error


def validate(binding, publication):
    envelope = deepcopy(binding["envelope"])
    envelope["acquisition_trace"] = deepcopy(binding.get("original_acquisition_trace"))
    expected = prepare(envelope, publication)
    expected["original_acquisition_trace"] = deepcopy(
        binding.get("original_acquisition_trace")
    )
    if expected != binding:
        raise SchemaError(
            "Article metadata binding does not match its original source support."
        )
    return deepcopy(binding)
