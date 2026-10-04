"""Detached source-operation provenance and bibliography (#108, MOLI #36).

These records describe observed access, not SourceAssertions or a MOLI ProjectRecord.
Applications choose their persistence; no implicit journal or project path is created.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature
from uuid import uuid4

from . import attribution as adapter

_collectors: ContextVar[tuple] = ContextVar(
    "sabueso_acquisition_collectors", default=()
)
_aggregated_sources: ContextVar[tuple] = ContextVar(
    "sabueso_aggregated_acquisition_sources", default=()
)
FORMAT = "sabueso.source_acquisition@1"
TRACE_FORMAT = "sabueso.acquisition_trace@1"
COVERAGE = {
    "sources": ["UniProt", "Europe PMC", "RCSB PDB", "ChEMBL"],
    "boundary": "built_in_entry_search_mentions_annotations_structure_chembl_clients",
    "other_sources_and_custom_clients": "not_observed",
}


@contextmanager
def collecting():
    records = []
    token = _collectors.set((*_collectors.get(), records))
    try:
        yield records
    finally:
        _collectors.reset(token)


def _trace(records, result_status, card=None):
    trace = {
        "format": TRACE_FORMAT,
        "id": "sabueso:acquisition-trace:" + str(uuid4()),
        "coverage": deepcopy(COVERAGE),
        "result_status": result_status,
        "records": deepcopy(records),
    }
    if card is not None:
        try:
            trace["card_ref"] = card.pinned_ref()
        except Exception as error:
            trace["recording_error"] = f"{type(error).__name__}: {error}"
            adapter._warning("source acquisition card pin", trace["recording_error"])
    return trace


def capture_acquisitions(function):
    """Attach original runtime records without changing scientific serialization."""

    @wraps(function)
    def captured(*args, **kwargs):
        with collecting() as records:
            try:
                result = function(*args, **kwargs)
            except Exception as error:
                error.acquisition_trace = _trace(records, "failed")
                raise
        if isinstance(result, tuple):
            card, resolution = result
            trace = _trace(records, resolution.status, card)
            resolution._acquisition_trace = deepcopy(trace)
            if card is not None:
                card._acquisition_trace = deepcopy(trace)
        elif isinstance(result, dict):
            result["acquisition_trace"] = _trace(records, "returned")
        else:
            trace = _trace(records, getattr(result, "status", "returned"))
            if hasattr(result, "snapshot_id"):
                try:
                    trace["packet_snapshot_id"] = result.snapshot_id()
                    trace["card_refs"] = {
                        role: entity["ref"] for role, entity in result.entities.items()
                    }
                except Exception as error:
                    trace["recording_error"] = f"{type(error).__name__}: {error}"
                    adapter._warning(
                        "source acquisition packet pin", trace["recording_error"]
                    )
            result._acquisition_trace = trace
        return result

    return captured


def _response(operation, result):
    if operation == "entry":
        entry, retrieved = result
        return (
            entry,
            retrieved,
            (entry.get("entryAudit") or {}).get("entryVersion"),
            "entry_version",
            1,
        )
    if operation == "search":
        return (
            result,
            result.get("retrieved_at"),
            result.get("release"),
            "database_release",
            len(result.get("results") or []),
        )
    payload = result["record"]
    count = (
        len(payload.get("articles") or [])
        if operation == "mentions"
        else sum(len(article["annotations"]) for article in payload)
    )
    return (
        payload,
        result.get("retrieved_at"),
        result.get("version"),
        "service_version" if operation == "mentions" else "not_stated",
        count,
    )


def _terminal(error, fixture, requests):
    from .errors import NotArchivedError, OfflineError, RecordNotFoundError

    chain = []
    while error is not None and error not in chain:
        chain.append(error)
        error = error.__cause__ or error.__context__
    if any(isinstance(item, (NotArchivedError, OfflineError)) for item in chain):
        return "not_queried"
    if fixture and getattr(chain[0], "acquisition_outcome", None) == "unavailable":
        return "unavailable"
    if isinstance(chain[0], RecordNotFoundError):
        if fixture:
            return "unavailable"
        if any(request.get("status") == 404 for request in requests):
            return "not_found"
        return "empty" if requests else "unobserved"
    return "failed"


def missing_fixture(message):
    """Keep the existing client exception while declaring local unavailability."""
    from .errors import ConnectorError

    error = ConnectorError(message)
    error.acquisition_outcome = "unavailable"
    return error


def acquisition(source, operation, *, fixture=False, summarize=None, aggregate=False):
    """Instrument a built-in client method; its original result/exception is preserved."""

    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def observed(*args, **kwargs):
            if source in _aggregated_sources.get():
                return function(*args, **kwargs)
            from sabueso import __version__
            from sabueso.tools.db import _http

            bound = parameters.bind(*args, **kwargs)
            bound.apply_defaults()
            query = {
                key: deepcopy(value)
                for key, value in bound.arguments.items()
                if key != "self"
            }
            record = {
                "format": FORMAT,
                "id": "sabueso:source-acquisition:" + str(uuid4()),
                "source": source,
                "operation": operation,
                "query": query,
                "producer": {
                    "name": "sabueso",
                    "version": __version__,
                    "version_basis": "runtime_package_metadata",
                },
                "started_at": _http._clock(),
            }
            with _http.observing_requests() as requests:
                token = _aggregated_sources.set(
                    (*_aggregated_sources.get(), source)
                    if aggregate
                    else _aggregated_sources.get()
                )
                try:
                    result = function(*args, **kwargs)
                except Exception as error:
                    record.update(
                        outcome=_terminal(error, fixture, requests),
                        error={"type": type(error).__name__, "message": str(error)},
                    )
                    if summarize is not None:
                        try:
                            record.update(summarize(error, query, fixture, requests))
                        except Exception as recording_error:
                            record["recording_error"] = (
                                f"{type(recording_error).__name__}: {recording_error}"
                            )
                            adapter._warning(
                                "source acquisition", record["recording_error"]
                            )
                    if record["outcome"] in {"empty", "not_found"}:
                        record["count"] = 0
                    if requests and not fixture:
                        record["retrieved_at"] = _http._STAMP.get().value
                    if (
                        operation == "mentions"
                        and getattr(error, "version", None) is not None
                    ):
                        record["source_version"] = {
                            "value": error.version,
                            "basis": "service_version",
                        }
                    _finish(record, requests, fixture)
                    raise
                else:
                    try:
                        if summarize is not None:
                            record.update(summarize(result, query, fixture, requests))
                        else:
                            payload, retrieved, version, basis, count = _response(
                                operation, result
                            )
                            from .snapshot import canonical_json, digest

                            record.update(
                                outcome="received" if count else "empty",
                                count=count,
                                retrieved_at=retrieved,
                                source_version={"value": version, "basis": basis},
                                response_identity={
                                    "basis": "decoded_client_result",
                                    "hash": digest(canonical_json(payload)),
                                },
                            )
                    except Exception as error:
                        record.update(
                            outcome="unobserved",
                            recording_error=f"{type(error).__name__}: {error}",
                        )
                        adapter._warning(
                            "source acquisition", record["recording_error"]
                        )
                    _finish(record, requests, fixture)
                    return result
                finally:
                    _aggregated_sources.reset(token)

        return observed

    return decorate


def _finish(record, requests, fixture):
    from sabueso.tools.db._http import _clock

    record["finished_at"] = _clock()
    record["requests"] = deepcopy(requests)
    routes = {request["route"] for request in requests}
    record["access"] = (
        "fixture"
        if fixture
        else next(iter(routes))
        if len(routes) == 1
        else "mixed"
        if routes
        else "unobserved"
    )
    record["network_attempts"] = sum(
        request["network_attempts"] for request in requests
    )
    record["received_responses"] = sum(
        request["outcome"] == "received" for request in requests
    )
    record.setdefault(
        "retrieved_at",
        next((r.get("retrieved_at") for r in requests if r.get("retrieved_at")), None),
    )
    record.setdefault("source_version", {"value": None, "basis": "not_stated"})
    try:
        record["provider"] = _credit(record)
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        record["provider"] = {"status": "failed", "reason": reason, "attribution": None}
        adapter._warning("source acquisition bibliography", reason)
    for collector in _collectors.get():
        collector.append(deepcopy(record))
    for run in adapter._runs.get():
        run._acquisitions.append(deepcopy(record))


def _credit(record):
    from .attribution_bibliography import descriptions, software
    from .snapshot import canonical_json, digest

    record["bibliography"] = [software(), *descriptions(record["source"])]
    record["bibliography_gaps"] = []
    primary_ids = set()
    primary_role = "structure_primary_citation"
    if record["source"] == "RCSB PDB":
        from .attribution_bibliography import structure_citations

        citations, gaps = structure_citations(record.get("entries", []))
        primary_ids = {item["id"] for item in citations}
        record["bibliography"] = list(
            {
                item["id"]: item for item in [*record["bibliography"], *citations]
            }.values()
        )
        record["bibliography_gaps"].extend(gaps)
    if record["source"] == "ChEMBL":
        from .attribution_bibliography import chembl_citations

        citations, gaps = chembl_citations(record.get("documents", {}))
        primary_ids = {item["id"] for item in citations}
        primary_role = "measurement_primary_citation"
        record["bibliography"].extend(citations)
        record["bibliography_gaps"].extend(gaps)
        if (
            record["operation"] in {"bioactivities", "assay_activities"}
            and not citations
        ):
            record["bibliography_gaps"].append(
                "measurement_document_citations_not_returned"
            )
        if record["operation"] in {"indications", "indications_for"}:
            record["bibliography_gaps"].append(
                "indication_reference_metadata_not_declared"
            )
    if record["operation"] == "annotations":
        record["bibliography_gaps"].append(
            "article_and_annotation_provider_citations_not_declared"
        )
    completed_partial = record["outcome"] == "partial" and (
        record.get("completed_ids") or record.get("completed_pages")
    )
    if (
        record["outcome"] not in ("received", "empty", "not_found")
        and not completed_partial
    ):
        return {
            "status": "not_attempted",
            "reason": "source_access_not_completed",
            "attribution": None,
        }
    backend = None
    try:
        backend = adapter._load_backend()
        context = {
            key: deepcopy(record[key])
            for key in (
                "id",
                "producer",
                "source",
                "operation",
                "query",
                "outcome",
                "access",
                "retrieved_at",
                "source_version",
                "network_attempts",
                "requests",
            )
        }
        for key in (
            "entries",
            "completed_ids",
            "pages",
            "completed_pages",
            "total_count",
            "truncated",
            "missing",
            "incomplete",
        ):
            if key in record:
                context[key] = deepcopy(record[key])
        resource = "sabueso:source-access:" + digest(
            canonical_json(
                {
                    key: record[key]
                    for key in ("source", "operation", "query", "source_version")
                }
            )
        )
        with backend.capture("sabueso.source_access", context=context) as capture:
            with backend.scope("sabueso.source_access"):
                for item in record["bibliography"]:
                    backend.register_item(**item)
                backend.register_item(
                    id=resource,
                    type="dataset",
                    title=f"{record['source']} {record['operation']} access",
                )
                backend.track_item(
                    record["bibliography"][0]["id"],
                    roles=["executed_software"],
                    context=context,
                )
                backend.track_item(resource, roles=["resource_access"], context=context)
                for item in record["bibliography"][1:]:
                    backend.track_item(
                        item["id"],
                        roles=[
                            primary_role
                            if item["id"] in primary_ids
                            else "resource_description"
                        ],
                        context=context,
                    )
        return {
            "status": "available",
            "version": backend.__version__,
            "attribution": capture.attribution.to_dict(),
        }
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        adapter._warning("source acquisition", reason)
        return {
            "status": "failed",
            "version": getattr(backend, "__version__", None),
            "reason": reason,
            "attribution": None,
        }
