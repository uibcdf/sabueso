"""Observe BindingDB affinity queries through REST, fixtures and installed mirrors."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_responses = ContextVar("sabueso_bindingdb_responses", default=None)


def note_response(payload):
    responses = _responses.get()
    if responses is not None:
        responses.append(deepcopy(payload))


def observe(*, fixture=False, mirror=False):
    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def observed(*args, **kwargs):
            client = parameters.bind(*args, **kwargs).arguments["self"]
            responses = []
            token = _responses.set(responses)

            def summary(result, query, is_fixture, requests):
                return summarize(
                    result, query, is_fixture, requests, responses, client, mirror
                )

            try:
                return acquisition(
                    "BindingDB", "affinities", fixture=fixture, summarize=summary
                )(function)(*args, **kwargs)
            finally:
                _responses.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, responses, client, mirror):
    from sabueso.tools.db.bindingdb import DEFAULT_CUTOFF, DEFAULT_LIMIT

    failed = isinstance(result, Exception)
    pages, received = [], []
    for payload in responses:
        envelope = (
            payload.get("getLindsByUniprotsResponse")
            if isinstance(payload, dict)
            else None
        )
        records = envelope.get("affinities") if isinstance(envelope, dict) else None
        if not isinstance(records, list) or any(
            not isinstance(r, dict) for r in records
        ):
            records = []
        received.extend(records)
        pages.append(
            {
                "count": len(records),
                "response_identity": {
                    "basis": "decoded_mirror_rows"
                    if mirror
                    else "decoded_api_response",
                    "hash": digest(canonical_json(payload)),
                },
            }
        )

    if failed:
        outcome = _terminal(result, fixture, requests)
        if isinstance(result, RecordNotFoundError) and pages and not received:
            outcome = "empty"
        elif received:
            outcome = "partial"
        records = received
        payload = {"completed_pages": pages, "error": type(result).__name__}
    else:
        records = result.get("record") or []
        outcome = "received" if records else "empty"
        payload = result

    # Only source-stated publication pointers and origins enter the receipt. A
    # declarative ChEMBL origin is not a directly consulted ChEMBL resource.
    publications, origins = {}, []
    for record in records:
        publication = {k: deepcopy(record[k]) for k in ("doi", "pmid") if record.get(k)}
        if publication:
            publications[digest(canonical_json(publication))] = publication
        origins.append(
            {
                "record_identity": digest(canonical_json(record)),
                "monomer_id": deepcopy(record.get("monomerid")),
                "data_source": deepcopy(record.get("data_source")),
                "basis": "source_stated" if record.get("data_source") else "not_stated",
            }
        )

    metadata = {
        "outcome": outcome,
        "count": len(records),
        "source_version": {"value": None, "basis": "not_stated"},
        "cutoff_scope": {
            "quantity": {
                "value": DEFAULT_CUTOFF if query["cutoff"] is None else query["cutoff"],
                "unit": "nM",
            },
            "basis": "fixture_not_reapplied"
            if fixture
            else "applied_to_local_index"
            if mirror
            else "submitted_to_rest",
        },
        "effective_limit": query["limit"] or DEFAULT_LIMIT
        if mirror
        else query["limit"],
        "pages": pages,
        "completed_pages": deepcopy(pages),
        "publications": list(publications.values()),
        "record_origins": origins,
        "response_identity": {
            "basis": "decoded_completed_pages" if failed else "decoded_client_result",
            "hash": digest(canonical_json(payload)),
        },
    }
    if not failed:
        metadata.update(
            retrieved_at=result.get("retrieved_at"),
            total_count=result.get("total_count"),
            truncated=result.get("total_count", 0) > len(records),
            record_order=result.get("record_order"),
        )
    elif pages:
        metadata.update(
            retrieved_at=client.installed_at
            if mirror
            else client.retrieved_at
            if fixture
            else next(
                (r.get("retrieved_at") for r in requests if r.get("retrieved_at")), None
            ),
            incomplete=outcome == "partial",
            count_basis="received_affinities_before_completion",
        )
    if mirror:
        manifest = deepcopy(client._release_info)
        metadata.update(
            access="mirror",
            source_version={
                "value": client.release,
                "basis": "installed_mirror_release",
                "scope": "indexed_release_manifest_not_live_rest_version",
            },
            mirror={
                "manifest": manifest,
                "manifest_identity": {
                    "basis": "client_manifest_at_initialization",
                    "hash": digest(canonical_json(manifest)),
                },
            },
            retrieved_at_basis="mirror_installation_time",
        )
    return metadata
