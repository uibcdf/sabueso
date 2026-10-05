"""Observe explicit article metadata queries without crediting full-text reading."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .article_metadata import matches, project
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_response = ContextVar("sabueso_article_response", default=None)


def note_response(payload):
    state = _response.get()
    if state is not None:
        state["payload"] = deepcopy(payload)


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            state = {}
            token = _response.set(state)
            try:
                return acquisition(
                    "Europe PMC",
                    "article",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, state
                    ),
                )(function)(*args, **kwargs)
            finally:
                _response.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, state):
    failed = isinstance(result, Exception)
    payload = state.get("payload")
    results = payload.get("resultList") if isinstance(payload, dict) else None
    articles = results.get("result") if isinstance(results, dict) else None
    version = payload.get("version") if isinstance(payload, dict) else None
    total = payload.get("hitCount") if isinstance(payload, dict) else None
    entries = []
    for index, article in enumerate(articles if isinstance(articles, list) else []):
        valid = matches(article, query["identifier"])
        entries.append(
            {
                "record_index": index,
                "outcome": "received" if valid else "unobserved",
                "article": project(article) if isinstance(article, dict) else None,
                "response_identity": {
                    "basis": "decoded_article_record",
                    "hash": digest(canonical_json(article)),
                },
            }
        )
    outcome = _terminal(result, fixture, requests) if failed else "received"
    good = [e for e in entries if e["outcome"] == "received"]
    if failed and good:
        outcome = "partial"
    elif not failed:
        if result["record"]["truncated"]:
            outcome = "partial"
        elif total == 0:
            outcome = "empty"
    pages = (
        [
            {
                "response_identity": {
                    "basis": "decoded_fixture_metadata"
                    if fixture
                    else "decoded_api_response",
                    "hash": digest(canonical_json(payload)),
                }
            }
        ]
        if "payload" in state
        else []
    )
    metadata = {
        "outcome": outcome,
        "count": len(good) if isinstance(articles, list) else None,
        "count_basis": "received_matching_metadata_records_not_mentions_or_read_articles",
        "total_count": total,
        "entries": entries,
        "pages": pages,
        "completed_pages": pages if good else [],
        "source_version": {
            "value": version,
            "basis": "service_version" if version is not None else "not_stated",
        },
        "response_identity": {
            "basis": "decoded_received_response"
            if "payload" in state
            else "not_received",
            "hash": digest(canonical_json(payload)) if "payload" in state else None,
        },
        "article_context": {
            "scope": "explicit_article_metadata",
            "article_revision": "not_stated",
            "identity_basis": "source_stated_publication_identifiers",
            "text_access": "core_response_may_include_abstract_but_no_full_text_endpoint_or_link_is_consulted",
            "projection": "bibliography_identifiers_and_declared_license_without_abstract",
            "license_basis": "native_declaration_not_fragment_permission_or_inferred_license_version",
        },
    }
    if not failed:
        metadata.update(
            retrieved_at=result["retrieved_at"], truncated=result["record"]["truncated"]
        )
    if outcome == "partial":
        metadata["incomplete"] = True
    return metadata
