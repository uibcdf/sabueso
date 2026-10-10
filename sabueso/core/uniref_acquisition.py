"""Observe UniRef page scope without turning cluster similarity into identity."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import ConnectorError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_uniref_pages", default=None)


def note_response(
    payload, *, fixture=False, url=None, release=None, next_url=None, total=None
):
    page = {
        "outcome": "failed",
        "url": url,
        "source_version": {
            "value": release,
            "basis": "fixture_declared_release" if fixture else "X-UniProt-Release",
        },
        "next_url": next_url,
        "total_count_header": total,
        "response_identity": {
            "basis": "decoded_fixture_envelope" if fixture else "decoded_api_page",
            "hash": digest(canonical_json(payload)),
        },
    }
    if release is None:
        page["source_version"]["basis"] = "not_stated"
    pages = _pages.get()
    if pages is not None:
        pages.append(page)
    key = "record" if fixture else "results"
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get(key), list)
        or not all(isinstance(row, dict) for row in payload[key])
    ):
        raise ConnectorError(f"UniRef response does not state a {key} list")
    rows = payload[key]
    page.update(outcome="received" if rows else "empty", count=len(rows))


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "UniProt",
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: _summarize(
                        result, query, local, requests, pages, operation
                    ),
                )(function)(*args, **kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def _summarize(result, query, fixture, requests, pages, operation):
    from sabueso.tools.db.uniref import MAX_MEMBER_PAGES, MAX_MEMBERS, PAGE

    failed = isinstance(result, Exception)
    completed = [page for page in pages if page["outcome"] in {"received", "empty"}]
    terminal = _terminal(result, fixture, requests) if failed else None
    received = sum(page["count"] for page in completed) if completed else None
    versions = list(
        dict.fromkeys(page["source_version"]["value"] for page in completed)
    )
    stated = [version for version in versions if version is not None]
    version = {
        "value": stated[0] if len(stated) == 1 and None not in versions else None,
        "basis": "conflicting_pages"
        if len(stated) > 1
        else "partly_not_stated"
        if stated and None in versions
        else ("fixture_declared_release" if fixture else "X-UniProt-Release")
        if stated
        else "not_stated",
    }
    delivered = None if failed else len(result["record"])
    continuation = completed[-1]["next_url"] if completed else None
    truncated = None if failed else bool(result.get("truncated", False) or continuation)
    outcome = (
        "partial"
        if failed and completed
        else terminal
        if failed
        else "received"
        if delivered
        else "empty"
    )
    metadata = {
        "outcome": outcome,
        "count": delivered if not failed else received,
        "count_basis": "returned_client_rows"
        if not failed
        else "completed_page_rows; no_client_result_returned",
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "source_version": version,
        "truncated": truncated,
        "incomplete": failed or bool(truncated),
        "cluster_context": {
            "rule": "uniref_page_observation@1",
            "resource": "UniRef",
            "query": deepcopy(query),
            "scope": "fixture_subset"
            if fixture
            else "single_search_response"
            if operation == "uniref_clusters"
            else "linked_member_pages",
            "page_size": None
            if fixture
            else 10
            if operation == "uniref_clusters"
            else PAGE,
            "member_limit": MAX_MEMBERS
            if operation == "uniref_members" and not fixture
            else None,
            "received_rows": received,
            "returned_rows": delivered,
            "page_releases": versions,
            "continuation": continuation,
            "completeness": "not_established"
            if fixture or failed or truncated
            else "returned_route_exhausted; not_global_completeness",
            "client_version_basis": "compatibility_label; not_proof_of_coherent_page_releases",
            "identity_basis": "source_cluster_membership_is_similarity; never_entity_identity",
            "reference_basis": "resource_description_only; member_publications_not_queried",
        },
    }
    if operation == "uniref_members" and not fixture:
        pagination = {
            "rule": "uniref_member_pagination@1",
            "page_limit": MAX_MEMBER_PAGES,
            "requested_pages": max(
                len(pages), len({request["url"] for request in requests})
            ),
            "completed_pages": len(completed),
            "stop_reason": "request_failed"
            if failed
            else "member_limit"
            if truncated
            else "route_exhausted",
            "remaining_url": (
                requests[-1]["url"] if failed and requests else continuation
            ),
            "retry_basis": "shared_transport_limits; retries_are_not_new_logical_pages",
        }
        if failed:
            pagination.update(
                (getattr(result, "extra", None) or {}).get("uniref_pagination", {})
            )
        metadata["cluster_context"]["pagination"] = pagination
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
