# Frozen original B4 predicates from 2eb6114 / SDK200.
# Private consistency expectations only; preserve these meanings.
"""Original retained article bibliography/terms projection; no source intake."""

import re
from copy import deepcopy

from ..snapshot import canonical_json, digest


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
