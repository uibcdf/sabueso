"""Observe CCD and UniChem identity access without inferring molecular identity."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_responses = ContextVar("sabueso_chemical_identity_responses", default=None)


def note_response(payload, *, code=None):
    responses = _responses.get()
    if responses is not None:
        responses.append((code, deepcopy(payload)))


def observe(source, operation, *, fixture=False):
    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def observed(*args, **kwargs):
            bound = parameters.bind(*args, **kwargs)
            bound.apply_defaults()
            if source == "PDB CCD":
                # Materialize accepted iterables once before the generic observer
                # deep-copies its query; generators cannot be copied or consumed twice.
                from sabueso.tools.db.pdb_ccd import _codes

                bound.arguments["comp_ids"] = _codes(bound.arguments["comp_ids"])
            responses = []
            token = _responses.set(responses)

            def summary(result, query, is_fixture, requests):
                return summarize(
                    result,
                    query,
                    is_fixture,
                    requests,
                    responses,
                    source,
                    bound.arguments["self"],
                )

            try:
                return acquisition(
                    source, operation, fixture=fixture, summarize=summary
                )(function)(*bound.args, **bound.kwargs)
            finally:
                _responses.reset(token)

        return observed

    return decorate


def _ccd(result, query, fixture, requests, responses):
    failed = isinstance(result, Exception)
    codes = query["comp_ids"]
    found, pages = {}, []
    for code, payload in responses:
        page = {
            "response_identity": {
                "basis": "decoded_fixture_record"
                if fixture
                else "decoded_api_response",
                "hash": digest(canonical_json(payload)),
            }
        }
        if code is not None:
            found[code] = payload
            page["component_ids"] = [code]
        else:
            records = (
                ((payload.get("data") or {}).get("chem_comps") or [])
                if isinstance(payload, dict)
                else []
            )
            if not isinstance(records, list):
                records = []
            ids = []
            for record in records:
                chem = record.get("chem_comp") if isinstance(record, dict) else None
                if isinstance(chem, dict) and chem.get("id") in codes:
                    found[chem["id"]] = record
                    ids.append(chem["id"])
            page["component_ids"] = sorted(set(ids))
        pages.append(page)
    if not failed:
        found = result["components"]
    entries = []
    for code in codes:
        entry = {
            "component_id": code,
            "source_version": {"value": None, "basis": "not_stated"},
        }
        if code in found:
            chem = found[code].get("chem_comp") or {}
            entry.update(
                outcome="received",
                response_identity={
                    "basis": "decoded_component",
                    "hash": digest(canonical_json(found[code])),
                },
                revision_metadata={
                    k: deepcopy(chem[k])
                    for k in (
                        "pdbx_release_status",
                        "pdbx_initial_date",
                        "pdbx_modified_date",
                    )
                    if chem.get(k) is not None
                },
            )
        else:
            entry["outcome"] = (
                _terminal(result, fixture, requests)
                if failed
                else "unavailable"
                if fixture
                else "empty"
            )
        entries.append(entry)
    outcomes = {e["outcome"] for e in entries}
    outcome = (
        _terminal(result, fixture, requests)
        if failed
        else next(iter(outcomes))
        if len(outcomes) == 1
        else "partial"
        if outcomes
        else "not_queried"
    )
    if failed and found:
        outcome = "partial"
    return {
        "outcome": outcome,
        "count": len(found),
        "entries": entries,
        "completed_ids": sorted(found) if fixture or failed else list(codes),
        "missing": [c for c in codes if c not in found],
        "pages": pages,
        "completed_pages": [p for p in pages if p["component_ids"]],
    }


def _unichem(result, fixture, requests, responses):
    failed = isinstance(result, Exception)
    selected = None
    returned_count = 0
    pages = []
    for _, payload in responses:
        compounds = payload.get("compounds") or [] if isinstance(payload, dict) else []
        if fixture:
            compounds = (
                [payload]
                if isinstance(payload, dict)
                and payload
                and not payload.get("not_found")
                else []
            )
        if not isinstance(compounds, list):
            compounds = []
        selected = (
            compounds[0] if compounds and isinstance(compounds[0], dict) else None
        )
        returned_count += len(compounds)
        pages.append(
            {
                "returned_compound_count": len(compounds),
                "response_identity": {
                    "basis": "decoded_fixture_record"
                    if fixture
                    else "decoded_api_response",
                    "hash": digest(canonical_json(payload)),
                },
            }
        )
    outcome = (
        _terminal(result, fixture, requests)
        if failed
        else "received"
        if result.get("compound")
        else "empty"
    )
    if failed and isinstance(result, RecordNotFoundError) and pages and not selected:
        outcome = "empty"
    if failed and selected:
        outcome = "partial"
    lookup = {
        "returned_compound_count": returned_count,
        "selection_basis": "first_returned_compound_existing_client_policy",
        "uci": deepcopy((selected or {}).get("uci")),
        "standard_inchikey": deepcopy((selected or {}).get("standardInchiKey")),
        "source_records": deepcopy((selected or {}).get("sources") or []),
        "source_records_basis": "UniChem statements; linked databases were not consulted by this operation",
    }
    return {
        "outcome": outcome,
        "count": int(selected is not None),
        "identity_lookup": lookup,
        "pages": pages,
        "completed_pages": pages if selected else [],
    }


def summarize(result, query, fixture, requests, responses, source, client):
    failed = isinstance(result, Exception)
    metadata = (
        _ccd(result, query, fixture, requests, responses)
        if source == "PDB CCD"
        else _unichem(result, fixture, requests, responses)
    )
    metadata.update(
        source_version={"value": None, "basis": "not_stated"},
        response_identity={
            "basis": "decoded_completed_pages" if failed else "decoded_client_result",
            "hash": digest(canonical_json(metadata["pages"] if failed else result)),
        },
    )
    if not failed:
        metadata["retrieved_at"] = result.get("retrieved_at")
    elif responses and fixture:
        metadata["retrieved_at"] = client.retrieved_at
    if metadata["outcome"] == "partial":
        metadata.update(
            incomplete=True,
            terminal_outcome=_terminal(result, fixture, requests) if failed else None,
        )
    return metadata
