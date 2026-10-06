"""Observe MONDO index lookups separately from release retrieval and reuse."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from hashlib import sha256

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_lookup = ContextVar("sabueso_mondo_lookup", default=None)


class ObservedIndex(tuple):
    """Keep the release receipt for exactly the index held by the existing cache."""

    def __new__(cls, index, origin):
        result = super().__new__(cls, index)
        result.origin = deepcopy(origin)
        return result


def document(payload, *, asset=None, retrieved_at=None, requests=(), fixture=False):
    origin = {
        "response_identity": {
            "basis": "obo_file_bytes",
            "hash": sha256(payload).hexdigest(),
        },
        "format_declared": any(
            line.startswith(b"format-version:") for line in payload.splitlines()
        ),
        "scope": "fixture_subset" if fixture else "downloaded_release_file",
        "retrieved_at": retrieved_at,
        "requests": deepcopy(list(requests)),
        "asset": deepcopy(asset),
        "checksum": {
            "basis": "published_asset_digest"
            if asset and asset.get("sha256")
            else "not_stated",
            "verified": False if asset and asset.get("sha256") else None,
        },
    }
    state = _lookup.get()
    if state is not None:
        state["document"] = deepcopy(origin)
    return origin


def note_index(index, origin=None, *, reused=False):
    state = _lookup.get()
    if state is not None:
        state.update(index=index, document=deepcopy(origin), reused=reused)


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            state = {}
            token = _lookup.set(state)
            try:
                return acquisition(
                    "MONDO",
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, state
                    ),
                )(function)(*args, **kwargs)
            finally:
                _lookup.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, state):
    from sabueso.tools.db.mondo import normalize

    failed = isinstance(result, Exception)
    index, origin = state.get("index"), state.get("document")
    identifier = normalize(next(iter(query.values())))
    valid = (
        index is not None
        and identifier is not None
        and (origin is None or origin["format_declared"])
    )
    version = index[0] if index is not None else None
    term = index[1].get(identifier) if index is not None else None
    equivalent = index[2].get(identifier) if index is not None else None
    is_term = "mondo_id" in query
    statements = []
    if not is_term and equivalent:
        statements = [
            deepcopy(xref)
            for xref in index[1][equivalent]["xrefs"]
            if xref["id"] == identifier and xref["equivalent"]
        ]
    payload = (
        term
        if is_term
        else {
            "query": identifier,
            "mondo": equivalent,
            "equivalence_statements": statements,
        }
    )
    outcome = _terminal(result, fixture, requests) if failed else "received"
    if fixture and isinstance(result, FileNotFoundError):
        outcome = "unavailable"
    if valid and (not failed or isinstance(result, RecordNotFoundError)):
        matched = term is not None if is_term else equivalent is not None
        outcome = "received" if matched else "empty"
        if fixture and failed:
            outcome = "unavailable"
    elif index is not None:
        outcome = "unobserved"
    count = (
        (int(term is not None) if is_term else int(equivalent is not None))
        if valid
        else None
    )
    original_requests = (origin or {}).get("requests", [])
    original_time = (origin or {}).get("retrieved_at")
    metadata = {
        "outcome": outcome,
        "normalized_query": {"identifier": identifier},
        "count": count,
        "count_basis": "matching_index_term"
        if is_term
        else "stated_equivalence_in_index",
        "source_version": {
            "value": version,
            "basis": "obo_header_data_version"
            if version is not None and origin is not None
            else "cached_index_declared_version"
            if version is not None
            else "not_stated",
        },
        "response_identity": {
            "basis": "decoded_term_record" if is_term else "decoded_equivalence_lookup",
            "hash": digest(canonical_json(payload)),
        }
        if valid
        else {"basis": "not_evaluated", "hash": None},
        "identity_lookup": {
            "kind": "term" if is_term else "equivalent",
            "index_scope": (origin or {}).get(
                "scope",
                "unobserved_cached_index" if index is not None else "not_observed",
            ),
            "index_reused": state.get("reused", False),
            "index_origin": deepcopy(origin),
            "indexed_term_count": len(index[1]) if index is not None else None,
            "indexed_equivalence_count": len(index[2]) if index is not None else None,
            "equivalence_statements": statements,
            "definition_references": deepcopy(
                (term or {}).get("definition", {}).get("references", [])
            ),
            "identity_basis": "source_stated_MONDO:equivalentTo_not_names_or_related_xrefs",
            "absence_basis": "lookup_scope_only; fixture_subsets_do_not_establish_release_absence",
            "reference_basis": "MONDO declarations; referenced terminologies and publications were not consulted",
            "client_retrieved_at": None if failed else result.get("retrieved_at"),
            "client_time_basis": "fixture_supplied_time"
            if fixture
            else "original_release_response"
            if original_time is not None
            else "client_construction_clock_fallback_for_unobserved_index",
        },
    }
    if original_time is not None:
        metadata["retrieved_at"] = original_time
        metadata["retrieved_at_basis"] = (
            "fixture_supplied_time" if fixture else "original_release_response"
        )
    elif index is not None:
        metadata["retrieved_at"] = None
        metadata["retrieved_at_basis"] = "original_release_time_not_observed"
    if state.get("reused"):
        metadata["access"] = "mixed" if requests else "memory"
    if original_requests:
        metadata["identity_lookup"]["original_release_requests"] = deepcopy(
            original_requests
        )
    return metadata
