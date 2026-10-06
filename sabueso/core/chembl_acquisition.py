"""Observe ChEMBL pages without changing client returns or exceptions (#108)."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature

from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_chembl_pages", default=None)
_COLLECTIONS = {
    "activity.json": ("activities", "activity_id"),
    "molecule.json": ("molecules", "molecule_chembl_id"),
    "drug_indication.json": ("drug_indications", "drugind_id"),
    "assay.json": ("assays", "assay_chembl_id"),
    "document.json": ("documents", "document_chembl_id"),
}


def note_page(path, params, payload):
    pages = _pages.get()
    if pages is None:
        return
    collection, key = _COLLECTIONS.get(path, (None, None))
    records = payload.get(collection) or [] if collection else []
    page = {
        "path": path,
        "query": deepcopy(params),
        "response_identity": {
            "basis": "decoded_api_page",
            "hash": digest(canonical_json(payload)),
        },
    }
    if collection:
        page.update(
            collection=collection,
            count=len(records),
            record_ids=[r[key] for r in records if r.get(key) is not None],
            page_meta=deepcopy(payload.get("page_meta") or {}),
        )
    if path == "document.json":
        page["documents"] = deepcopy(records)
    if path == "drug_indication.json":
        from .indication_bibliography import reference_rows

        page["indication_reference_rows"] = reference_rows(records)
    if path == "status.json":
        page["database_release"] = payload.get("chembl_db_version")
    pages.append(page)


def observe(operation, *, fixture=False):
    """Normalize iterables once, then observe the original logical operation."""

    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def observed(*args, **kwargs):
            bound = parameters.bind(*args, **kwargs)
            bound.apply_defaults()
            for name in ("chembl_ids", "assay_ids", "disease_ids"):
                if name in bound.arguments:
                    bound.arguments[name] = sorted(
                        {i for i in bound.arguments[name] if i}
                    )
            pages = []
            token = _pages.set(pages)
            client = bound.arguments["self"]

            def summary(result, query, is_fixture, requests):
                return summarize(
                    result, query, is_fixture, requests, operation, pages, client
                )

            try:
                return acquisition(
                    "ChEMBL", operation, fixture=fixture, summarize=summary
                )(function)(*bound.args, **bound.kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def _fixture_available(client, operation):
    if operation == "bioactivities":
        return True  # A missing target raises the existing client exception.
    directory = client.directory / "chembl"
    if operation == "assay_activities":
        import json

        return any(
            "activities" in json.loads(path.read_text(encoding="utf-8"))
            for path in directory.glob("CHEMBL*.json")
        )
    return (
        directory
        / ("molecules.json" if operation == "molecules" else "indications.json")
    ).is_file()


def summarize(result, query, fixture, requests, operation, pages, client):
    collection = (
        "activities"
        if operation in {"bioactivities", "assay_activities"}
        else "molecules"
        if operation == "molecules"
        else "drug_indications"
    )
    completed = [p for p in pages if p.get("collection") == collection]
    failed = isinstance(result, Exception)
    if failed:
        count = sum(p["count"] for p in completed)
        outcome = "partial" if completed else _terminal(result, fixture, requests)
        documents = {
            d["document_chembl_id"]: d
            for p in pages
            for d in p.get("documents", [])
            if d.get("document_chembl_id")
        }
        release = next(
            (p["database_release"] for p in pages if "database_release" in p), None
        )
        payload = {"completed_pages": completed, "error": type(result).__name__}
        retrieved = None
    else:
        data = (
            result.get("activities")
            if collection == "activities"
            else result.get("molecules")
            if collection == "molecules"
            else result.get("indications")
        )
        count = (
            sum(len(v) for v in (data or {}).values())
            if collection == "drug_indications"
            else len(data or [])
        )
        outcome = "received" if count else "empty"
        documents = deepcopy(result.get("documents") or {})
        release = result.get("version")
        payload = result
        retrieved = result.get("retrieved_at")
        if fixture and not _fixture_available(client, operation):
            outcome = "unavailable"
    if any(
        name in query and not query[name]
        for name in ("chembl_ids", "assay_ids", "disease_ids")
    ):
        outcome = "not_queried"
    metadata = {
        "outcome": outcome,
        "count": count,
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "documents": documents,
        "source_version": {
            "value": release,
            "basis": "database_release" if release is not None else "not_stated",
        },
        "response_identity": {
            "basis": "decoded_completed_pages" if failed else "decoded_client_result",
            "hash": digest(canonical_json(payload)),
        },
    }
    if retrieved is not None:
        metadata["retrieved_at"] = retrieved
    if release is not None:
        metadata["source_version"]["origin"] = (
            "status_response"
            if any("database_release" in p for p in pages)
            else "fixture"
            if fixture
            else "client_release_cache"
        )
        metadata["source_version"]["scope"] = (
            "client_reported_release_not_verified_per_page"
        )
    if not failed:
        for key in ("total_count", "truncated", "missing"):
            if key in result:
                metadata[key] = deepcopy(result[key])
    else:
        metadata["incomplete"] = True
    if operation in {"indications", "indications_for"}:
        from .indication_bibliography import reference_rows

        observations = [
            {
                "basis": "decoded_api_page",
                "page_index": index,
                "query": deepcopy(page["query"]),
                "response_identity": deepcopy(page["response_identity"]),
                "rows": deepcopy(page["indication_reference_rows"]),
            }
            for index, page in enumerate(pages)
            if "indication_reference_rows" in page
        ]
        if not observations and not failed and outcome == "received":
            observations.append(
                {
                    "basis": "decoded_client_result",
                    "query": deepcopy(query),
                    "response_identity": deepcopy(metadata["response_identity"]),
                    "rows": reference_rows(
                        row
                        for rows in (result.get("indications") or {}).values()
                        for row in rows
                    ),
                }
            )
        metadata["indication_reference_context"] = {
            "rule": "chembl_indication_references@1",
            "target_access": "not_queried_by_this_operation",
            "observations": observations,
        }
    return metadata
