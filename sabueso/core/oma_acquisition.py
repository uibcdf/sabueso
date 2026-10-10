"""Observe OMA statements separately from UniProt entry-name resolution."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature

from .errors import ConnectorError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_oma_pages", default=None)


def note_response(
    payload,
    *,
    kind="rows",
    fixture=False,
    url=None,
    release=None,
    link=None,
    names=None,
):
    continuation = next(
        (
            part.split(";")[0].strip().strip("<>")
            for part in (link or "").split(",")
            if 'rel="next"' in part
        ),
        None,
    )
    page = {
        "outcome": "failed",
        "url": url,
        "next_url": continuation,
        "source_version": {
            "value": release,
            "basis": "X-UniProt-Release" if release is not None else "not_stated",
        },
        "response_identity": {
            "basis": "decoded_fixture_record" if fixture else "decoded_api_response",
            "hash": digest(canonical_json(payload)),
        },
    }
    if names is not None:
        page["requested_names"] = list(names)
    pages = _pages.get()
    if pages is not None:
        pages.append(page)
    if kind == "protein":
        valid = isinstance(payload, dict) and any(
            payload.get(key) for key in ("omaid", "canonicalid", "entry_nr")
        )
        count = 1
    elif kind == "names" and fixture:
        valid = isinstance(payload, dict) and all(
            isinstance(key, str) and isinstance(value, str) and value
            for key, value in payload.items()
        )
        count = len(payload) if valid else None
    else:
        rows = (
            payload.get("results")
            if kind == "names" and isinstance(payload, dict)
            else payload
        )
        valid = isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
        count = len(rows) if valid else None
    if not valid:
        source = "UniProt entry-name" if kind == "names" and not fixture else "OMA"
        raise ConnectorError(
            f"{source} {kind} response does not state the required record container"
        )
    page.update(outcome="received" if count else "empty", count=count)


def note_name_resolution(mapping):
    pages = _pages.get()
    if pages:
        page = pages[-1]
        page["resolved_names"] = deepcopy(mapping)
        page["unresolved_names"] = sorted(
            {name for name in page["requested_names"] if isinstance(name, str) and name}
            - set(mapping)
        )


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            # Materialize once before the common observer deep-copies the query.
            # This preserves iterable/generator inputs without consuming them twice.
            if operation == "oma_entry_names":
                bound = signature(function).bind(*args, **kwargs)
                bound.arguments["names"] = list(bound.arguments["names"])
                args, kwargs = bound.args, bound.kwargs
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "UniProt" if operation == "oma_entry_names" else "OMA",
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
    failed = isinstance(result, Exception)
    completed = [page for page in pages if page["outcome"] in {"received", "empty"}]
    received = sum(page["count"] for page in completed) if completed else None
    names = operation == "oma_entry_names"
    delivered = (
        None
        if failed
        else len(result)
        if names
        else 1
        if operation == "oma_protein"
        else len(result["record"])
    )
    terminal = _terminal(result, fixture, requests) if failed else None
    versions = list(
        dict.fromkeys(page["source_version"]["value"] for page in completed)
    )
    stated = [value for value in versions if value is not None]
    continuation = [page["next_url"] for page in completed if page["next_url"]]
    metadata = {
        "outcome": "partial"
        if failed and completed
        else terminal
        if failed
        else "not_queried"
        if not completed
        else "received"
        if delivered
        else "empty",
        "count": received if failed else delivered if completed else None,
        "count_basis": "completed_response_rows; no_client_result_returned"
        if failed
        else "returned_name_mappings; not_received_search_rows"
        if names
        else "returned_client_rows; not_card_selected_relations",
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "source_version": {
            "value": stated[0] if len(stated) == 1 and None not in versions else None,
            "basis": "conflicting_responses"
            if len(stated) > 1
            else "partly_not_stated"
            if stated and None in versions
            else "X-UniProt-Release"
            if stated
            else "not_stated",
        },
        "truncated": None if failed else bool(continuation),
        "incomplete": failed or bool(continuation),
        "orthology_context": {
            "rule": "oma_operation_observation@1",
            "resource": "UniProtKB" if names else "OMA",
            "scope": "fixture_subset"
            if fixture
            else "one_response_per_name_batch"
            if names
            else "single_native_response",
            "query": deepcopy(query),
            "received_rows": received,
            "returned_items": delivered,
            "continuations_not_followed": continuation,
            "completeness": "not_established",
            "identity_basis": "source_stated_xrefs_and_seq_match; orthology_and_shared_names_never_entity_identity",
            "selection_basis": "client_rows_precede_enricher_taxon_and_limit_selection; card_quality_reports_mapping_count",
            "reference_basis": "resource_description_only; entry_and_method_publications_not_queried",
        },
    }
    if names:
        metadata["orthology_context"].update(
            requested_names=sorted({name for name in query["names"] if name}),
            resolved_names=None if failed else deepcopy(result),
            resolution_basis="existing_client_policy; unique_accession_among_rows_not_marked_Inactive"
            if not fixture
            else "fixture_declared_name_mapping",
        )
    if completed:
        metadata["response_identity"] = {
            "basis": "completed_response_receipts"
            if failed
            else "decoded_client_result",
            "hash": digest(
                canonical_json(
                    completed if failed else result if names else result["record"]
                )
            ),
        }
    if failed:
        metadata["terminal_outcome"] = terminal
    elif not names:
        metadata["retrieved_at"] = result["retrieved_at"]
    return metadata
