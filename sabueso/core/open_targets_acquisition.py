"""Observe native association pages, counts and versions, never recompute scores."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_open_targets_pages", default=None)


def note_page(query, payload, *, fixture=False):
    pages = _pages.get()
    if pages is not None:
        pages.append((deepcopy(query), deepcopy(payload), fixture))


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "Open Targets",
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, operation, pages
                    ),
                )(function)(*args, **kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, operation, pages):
    from sabueso.tools.db.open_targets import _version, disease_id

    entity, collection = (
        ("disease", "associatedTargets")
        if operation == "targets"
        else ("target", "associatedDiseases")
    )
    failed = isinstance(result, Exception)
    receipts, versions, ids = [], [], []
    for variables, payload, local in pages:
        data = payload.get("data") if isinstance(payload, dict) else None
        record = payload.get("record") if local and isinstance(payload, dict) else None
        native = data.get(entity) if isinstance(data, dict) else None
        association = (
            record
            if local
            else native.get(collection)
            if isinstance(native, dict)
            else None
        )
        rows = association.get("rows") if isinstance(association, dict) else None
        count = association.get("count") if isinstance(association, dict) else None
        version = (
            payload.get("version")
            if local
            else _version(data.get("meta"))
            if isinstance(data, dict)
            else None
        )
        valid = (
            isinstance(rows, list)
            and type(count) is int
            and count >= len(rows)
            and all(isinstance(row, dict) for row in rows)
            and not (isinstance(payload, dict) and payload.get("errors"))
        )
        absent = isinstance(data, dict) and entity in data and native is None
        receipt = {
            "query": variables,
            "response_identity": {
                "basis": "decoded_fixture_envelope"
                if local
                else "decoded_graphql_page",
                "hash": digest(canonical_json(payload)),
            },
            "outcome": "received" if valid else "empty" if absent else "unobserved",
            "count": len(rows) if valid else 0 if absent else None,
            "total_count": count,
            "source_version": {
                "value": version,
                "basis": "fixture_declared_release"
                if local and version is not None
                else "graphql_meta_data_version"
                if version is not None
                else "not_stated",
            },
            "row_order": [
                deepcopy(
                    (
                        row.get("target" if operation == "targets" else "disease") or {}
                    ).get("id")
                )
                for row in rows
            ]
            if valid
            else [],
        }
        receipts.append(receipt)
        if valid or absent:
            versions.append(version)
            ids.extend(receipt["row_order"])
    completed = [p for p in receipts if p["outcome"] in {"received", "empty"}]
    record = None if failed else result.get("record")
    rows = (record or {}).get("rows", [])
    count = (
        (record or {}).get("count")
        if not failed
        else (completed[-1]["total_count"] if completed else None)
    )
    outcome = (
        _terminal(result, fixture, requests)
        if failed
        else "received"
        if rows
        else "empty"
    )
    if (
        failed
        and isinstance(result, RecordNotFoundError)
        and completed
        and all(p["outcome"] == "empty" for p in completed)
    ):
        outcome = "empty"
    elif failed and completed:
        outcome = "partial"
    elif not failed and (
        not completed or any(p["outcome"] == "unobserved" for p in receipts)
    ):
        outcome = "unobserved"
    returned = len(rows) if not failed else sum(p["count"] for p in completed)
    incomplete = failed or (count is not None and returned < count)
    metadata = {
        "outcome": outcome,
        "count": returned if completed else None,
        "count_basis": "native_returned_association_rows_not_built_cards",
        "total_count": count,
        "incomplete": incomplete,
        "truncated": not failed and count is not None and returned < count,
        "effective_limit": query["limit"],
        "cutoff_scope": "source_rows_distinct_from_deck_member_limit",
        "normalized_query": {
            "disease": disease_id(query["disease"]),
            "limit": query["limit"],
        }
        if operation == "targets"
        else deepcopy(query),
        "pages": receipts,
        "completed_pages": completed,
        "row_order": ids[:returned],
        "source_version": {
            "value": versions[-1]
            if versions and len(set(versions)) <= 1
            else getattr(result, "version", None)
            if failed
            else result.get("version"),
            "basis": "fixture_declared_release"
            if fixture
            and versions
            and versions[-1] is not None
            and len(set(versions)) <= 1
            else "graphql_meta_data_version"
            if versions and versions[-1] is not None and len(set(versions)) <= 1
            else "not_stated",
        },
        "response_identity": {
            "basis": "completed_page_receipts" if failed else "decoded_client_record",
            "hash": digest(canonical_json(completed if failed else record)),
        },
        "association_context": {
            "direction": "disease_to_targets"
            if operation == "targets"
            else "target_to_diseases",
            "scope": "fixture_subset" if fixture else "queried_graphql_pages",
            "score_basis": "Open Targets native scores and order; not recomputed or efficacy",
            "reference_basis": "aggregated associations; underlying evidence and publications not fetched",
            "absence_basis": "queried_entity_and_pages_only",
            "page_versions": deepcopy(versions),
            "versions_consistent": len(set(versions)) <= 1,
        },
    }
    if failed:
        metadata["terminal_outcome"] = _terminal(result, fixture, requests)
    else:
        metadata["retrieved_at"] = result.get("retrieved_at")
    return metadata
