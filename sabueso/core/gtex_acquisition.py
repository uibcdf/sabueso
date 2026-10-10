"""Observe GTEx tissue access without treating requested labels as revisions."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import ConnectorError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_gtex_pages", default=None)


def note_response(dataset, payload, *, fixture=False):
    page = {
        "query": {"dataset": dataset},
        "outcome": "failed",
        "response_identity": {
            "basis": "decoded_fixture_envelope" if fixture else "decoded_api_page",
            "hash": digest(canonical_json(payload)),
        },
    }
    pages = _pages.get()
    if pages is not None:
        pages.append(page)
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("data"), list)
        or not all(isinstance(row, dict) for row in payload["data"])
    ):
        raise ConnectorError("GTEx response does not state a tissue data list")
    rows = payload["data"]
    page.update(
        outcome="received" if rows else "empty",
        count=len(rows),
        tissue_ids=[row.get("tissueSiteDetailId") for row in rows],
    )
    return rows


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "GTEx",
                    "tissues",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: _summarize(
                        result, query, local, requests, pages
                    ),
                )(function)(*args, **kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def _summarize(result, query, fixture, requests, pages):
    failed = isinstance(result, Exception)
    completed = [p for p in pages if p["outcome"] in {"received", "empty"}]
    terminal = _terminal(result, fixture, requests) if failed else None
    # The established client maps both HTTP codes to RecordNotFoundError. Keep
    # that interpretation explicit; a 422 is not a native dataset-absence claim.
    from .errors import RecordNotFoundError

    if (
        failed
        and isinstance(result, RecordNotFoundError)
        and any(request.get("status") in {404, 422} for request in requests)
    ):
        terminal = "not_found"
    count = sum(p["count"] for p in completed) if completed else None
    if failed and completed and count == 0:
        terminal = "empty"
    outcome = (
        "empty"
        if failed and completed and count == 0
        else terminal
        if failed
        else "received"
        if count
        else "empty"
    )
    metadata = {
        "outcome": outcome,
        "count": count,
        "count_basis": "returned_tissue_rows; not_card_selected_terms",
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "incomplete": failed and outcome not in {"empty", "not_found"},
        "source_version": {"value": None, "basis": "not_stated"},
        "tissue_context": {
            "rule": "gtex_tissue_observation@1",
            "requested_dataset": query["dataset"],
            "dataset_basis": "caller_request_parameter",
            "client_version_basis": "requested_dataset_label; native_revision_not_stated",
            "scope": "fixture_subset"
            if fixture
            else "single_tissue_site_detail_response",
            "items_per_page": None if fixture else 250,
            "completeness": "not_established",
            "identity_basis": "native_tissue_site_detail_ids; shared_ontology_terms_do_not_merge_tissues",
            "absence_basis": "received_empty_page_or_client_HTTP_404_422_interpretation; not_global_absence",
            "reference_basis": "resource_description_only; tissue_publications_not_queried",
        },
    }
    if completed:
        metadata["response_identity"] = {
            "basis": "completed_page_receipts" if failed else "decoded_client_record",
            "hash": digest(canonical_json(completed if failed else result["record"])),
        }
    if failed:
        metadata["terminal_outcome"] = terminal
    else:
        metadata["retrieved_at"] = result["retrieved_at"]
    return metadata
