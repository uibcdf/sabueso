"""Observe taxonomy batches without interpreting missing local files as absence."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_ncbi_taxonomy_pages", default=None)


def note_page(ids, payload, *, fixture=False):
    page = {
        "query": {"tax_ids": list(ids)},
        "outcome": "unobserved",
        "response_identity": {
            "basis": "decoded_fixture_taxon" if fixture else "decoded_datasets_page",
            "hash": digest(canonical_json(payload)),
        },
    }
    pages = _pages.get()
    if pages is not None:
        pages.append(page)
    return page


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(self, tax_ids):
            from sabueso.tools.db.ncbi_taxonomy import _ids

            # Consume a one-shot iterable before the shared observer copies the query.
            ids = _ids(tax_ids)
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "NCBI Taxonomy",
                    "taxa",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: _summarize(
                        result, query, local, requests, pages
                    ),
                )(function)(self, ids)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def _summarize(result, query, fixture, requests, pages):
    failed = isinstance(result, Exception)
    ids = query["tax_ids"]
    completed = [page for page in pages if page["outcome"] == "received"]
    answered = {t for page in completed for t in page["query"]["tax_ids"]}
    received = sorted({t for page in completed for t in page["received_ids"]})
    unavailable = [
        page["query"]["tax_ids"][0]
        for page in pages
        if page["outcome"] == "unavailable"
    ]
    missing = [t for t in ids if t in answered and t not in received]
    terminal = _terminal(result, fixture, requests) if failed else None
    outcome = (
        ("partial" if completed else terminal)
        if failed
        else "not_queried"
        if not ids
        else ("partial" if completed else "unavailable")
        if unavailable
        else "received"
        if received
        else "empty"
    )
    metadata = {
        "outcome": outcome,
        "count": len(received),
        "normalized_query": {"tax_ids": list(ids)},
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "completed_ids": received,
        "missing": missing,
        "incomplete": failed or bool(unavailable),
        "source_version": {"value": None, "basis": "not_stated"},
        "response_identity": {
            "basis": "completed_page_receipts" if failed else "decoded_client_record",
            "hash": digest(canonical_json(completed if failed else result["record"])),
        },
        "taxonomy_context": {
            "rule": "ncbi_taxonomy_observation@1",
            "scope": "fixture_subset" if fixture else "queried_datasets_taxa",
            "missing_basis": "not_returned_by_completed_source_batch",
            "unavailable_ids": unavailable,
            "unanswered_ids": [t for t in ids if t not in answered],
            "version_basis": "API_route_version_is_not_a_taxonomy_record_revision",
            "reference_basis": "resource_description_only; taxonomic_publications_not_queried",
        },
    }
    if failed:
        metadata["terminal_outcome"] = terminal
    else:
        metadata["retrieved_at"] = result["retrieved_at"]
    return metadata
