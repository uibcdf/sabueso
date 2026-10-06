"""Observe indexed Orphanet associations and their original XML release receipt."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from hashlib import sha256

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_lookup = ContextVar("sabueso_orphadata_lookup", default=None)


class ObservedIndex(tuple):
    def __new__(cls, index, origin):
        result = super().__new__(cls, index)
        result.origin = deepcopy(origin)
        return result


def document(payload, retrieved_at, requests=(), *, fixture=False):
    origin = {
        "response_identity": {
            "basis": "xml_file_bytes",
            "hash": sha256(payload).hexdigest(),
        },
        "retrieved_at": retrieved_at,
        "requests": deepcopy(list(requests)),
        "scope": "fixture_subset" if fixture else "downloaded_release_file",
        "published_checksum": "not_stated",
    }
    note_index(None, origin)
    return origin


def note_index(index, origin=None, *, reused=False):
    state = _lookup.get()
    if state is not None:
        state.update(index=index, origin=deepcopy(origin), reused=reused)


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            state = {}
            token = _lookup.set(state)
            try:
                return acquisition(
                    "Orphanet",
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, operation, state
                    ),
                )(function)(*args, **kwargs)
            finally:
                _lookup.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, operation, state):
    from sabueso.tools.db.orphadata import genes_of

    failed = isinstance(result, Exception)
    index, origin = state.get("index"), state.get("origin")
    rows = (
        (
            genes_of(index[1], query["orpha_code"])
            if operation == "genes"
            else index[1].get(query["accession"], [])
        )
        if index is not None
        else None
    )
    outcome = _terminal(result, fixture, requests) if failed else "received"
    if index is not None and (not failed or isinstance(result, RecordNotFoundError)):
        outcome = (
            "received" if rows else "unavailable" if fixture and failed else "empty"
        )
    version = index[0] if index is not None else None
    metadata = {
        "outcome": outcome,
        "count": len(rows) if rows is not None else None,
        "count_basis": "indexed_SwissProt_association_rows_not_all_native_genes",
        "normalized_query": {"orpha_code": str(query["orpha_code"]).split(":")[-1]}
        if operation == "genes"
        else deepcopy(query),
        "source_version": {
            "value": version,
            "basis": "xml_header_date"
            if version is not None and origin is not None
            else "cached_index_declared_version"
            if version is not None
            else "not_stated",
        },
        "retrieved_at": (origin or {}).get("retrieved_at"),
        "retrieved_at_basis": "fixture_supplied_time"
        if fixture and origin
        else "original_release_response"
        if origin
        else "original_release_time_not_observed",
        "response_identity": {
            "basis": "decoded_index_rows" if rows is not None else "not_evaluated",
            "hash": digest(canonical_json(rows)) if rows is not None else None,
        },
        "association_context": {
            "direction": "disease_to_genes"
            if operation == "genes"
            else "protein_to_diseases",
            "index_origin": deepcopy(origin),
            "index_reused": state.get("reused", False),
            "index_scope": (origin or {}).get(
                "scope",
                "unobserved_cached_index" if index is not None else "not_observed",
            ),
            "indexed_accession_count": len(index[1]) if index is not None else None,
            "row_order": [
                {
                    "orpha_code": row.get("orpha_code"),
                    "gene_symbol": row.get("gene_symbol"),
                    "uniprot": row.get("uniprot", query.get("accession")),
                }
                for row in rows or []
            ],
            "validation_references": list(
                dict.fromkeys(
                    v for row in rows or [] for v in row.get("validation", [])
                )
            ),
            "identity_basis": "source_stated_SwissProt_xrefs; names_not_matched",
            "absence_basis": "indexed_SwissProt_associations_only; fixture_subset_not_global_absence",
            "reference_basis": "native_validation_pointers; cited_publications_not_fetched",
            "client_retrieved_at": None if failed else result.get("retrieved_at"),
            "client_time_basis": "fixture_supplied_time"
            if fixture
            else "original_release_response"
            if origin
            else "query_clock_fallback_for_unobserved_index",
        },
    }
    if state.get("reused"):
        metadata["access"] = "mixed" if requests else "memory"
    return metadata
