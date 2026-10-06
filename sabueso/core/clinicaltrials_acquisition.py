"""Observe bounded native registry queries and reject unsupported absence (#127)."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from inspect import signature

from .errors import ConnectorError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_pages = ContextVar("sabueso_clinicaltrials_pages", default=None)


def normalize_ids(values):
    return sorted(
        {value.strip().upper() for value in values if value and value.strip()}
    )


def nct_id(study):
    protocol = study.get("protocolSection") if isinstance(study, dict) else None
    identification = (
        protocol.get("identificationModule") if isinstance(protocol, dict) else None
    )
    return identification.get("nctId") if isinstance(identification, dict) else None


def project(study):
    """Native identity/title/update and reference forms, without clinical inference."""
    protocol = study["protocolSection"]
    identification = protocol["identificationModule"]
    projected = {"identificationModule": deepcopy(identification)}
    status = protocol.get("statusModule")
    if isinstance(status, dict) and "lastUpdatePostDateStruct" in status:
        projected["statusModule"] = {
            "lastUpdatePostDateStruct": deepcopy(status["lastUpdatePostDateStruct"])
        }
    if "referencesModule" in protocol:
        projected["referencesModule"] = deepcopy(protocol["referencesModule"])
    return {"protocolSection": projected}


def _receipt(endpoint, query, payload, *, fixture=False):
    page = {
        "endpoint": endpoint,
        "query": deepcopy(query),
        "outcome": "unobserved",
        "response_identity": {
            "basis": "decoded_fixture_envelope" if fixture else "decoded_api_page",
            "hash": digest(canonical_json(payload)),
        },
        "entries": [],
    }
    pages = _pages.get()
    if pages is not None:
        pages.append(page)
    return page


def note_response(endpoint, query, payload):
    """Validate native page shape before absence or identity is interpreted."""
    page = _receipt(endpoint, query, payload)
    if not isinstance(payload, dict):
        raise ConnectorError(f"ClinicalTrials.gov {endpoint} has no object answer")
    if payload.get("error"):
        raise ConnectorError(f"ClinicalTrials.gov {endpoint} declares an error")
    if endpoint == "version":
        if not {"dataTimestamp", "apiVersion"}.intersection(payload):
            raise ConnectorError("ClinicalTrials.gov has no native version metadata")
        for key in ("dataTimestamp", "apiVersion"):
            if payload.get(key) is not None and not isinstance(payload[key], str):
                raise ConnectorError(f"ClinicalTrials.gov has an invalid {key}")
        page.update(
            outcome="received",
            data_timestamp=payload.get("dataTimestamp"),
            api_version=payload.get("apiVersion"),
        )
        return
    rows = payload.get("studies")
    if not isinstance(rows, list):
        raise ConnectorError("ClinicalTrials.gov has no native studies list")
    requested = set(query["filter.ids"].split(","))
    invalid = False
    for position, study in enumerate(rows):
        identifier = nct_id(study)
        valid = isinstance(identifier, str) and identifier in requested
        invalid |= not valid
        page["entries"].append(
            {
                "record_index": position,
                "nct_id": deepcopy(identifier),
                "outcome": "received" if valid else "unobserved",
                "study": project(study) if valid else None,
                "response_identity": {
                    "basis": "decoded_study_record",
                    "hash": digest(canonical_json(study)),
                },
            }
        )
    page.update(
        next_page_token=deepcopy(payload.get("nextPageToken")),
        total_count=deepcopy(payload.get("totalCount")),
    )
    token = payload.get("nextPageToken")
    if token is not None and (not isinstance(token, str) or not token):
        raise ConnectorError("ClinicalTrials.gov has an invalid continuation token")
    if invalid:
        raise ConnectorError(
            "ClinicalTrials.gov returned an unreadable or unrequested NCT identity"
        )
    page["outcome"] = "received"


def note_fixture(query, payload, selected):
    page = _receipt("fixture", query, payload, fixture=True)
    page.update(
        outcome="received",
        data_timestamp=payload.get("version"),
        api_version=payload.get("api_version"),
        entries=[
            {
                "record_index": index,
                "nct_id": identifier,
                "outcome": "received",
                "study": project(study),
                "response_identity": {
                    "basis": "decoded_study_record",
                    "hash": digest(canonical_json(study)),
                },
            }
            for index, (identifier, study) in enumerate(selected.items())
        ],
    )
    return page


def observe(operation, *, fixture=False):
    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def observed(*args, **kwargs):
            bound = parameters.bind(*args, **kwargs)
            bound.apply_defaults()
            bound.arguments["nct_ids"] = list(bound.arguments["nct_ids"])
            pages = []
            token = _pages.set(pages)
            try:
                return acquisition(
                    "ClinicalTrials.gov",
                    operation,
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, pages, operation
                    ),
                )(function)(*bound.args, **bound.kwargs)
            finally:
                _pages.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, pages, operation):
    failed = isinstance(result, Exception)
    entries = [
        {**deepcopy(entry), "page_index": index}
        for index, page in enumerate(pages)
        for entry in page["entries"]
    ]
    good = [entry for entry in entries if entry["outcome"] == "received"]
    completed = [
        page
        for page in pages
        if page["outcome"] == "received"
        or any(entry["outcome"] == "received" for entry in page["entries"])
    ]
    requested = normalize_ids(query["nct_ids"])
    terminal = _terminal(result, fixture, requests) if failed else None
    outcome = (
        ("partial" if completed else terminal)
        if failed
        else "not_queried"
        if not requested
        else "received"
        if result["record"]
        else "empty"
    )
    versions = [
        page.get("data_timestamp")
        for page in pages
        if page["outcome"] == "received"
        and (page["endpoint"] in {"version", "fixture"})
    ]
    version = versions[0] if versions else None
    metadata = {
        "outcome": outcome,
        "count": len({entry["nct_id"] for entry in good}),
        "count_basis": "distinct_requested_native_NCT_ids; page_occurrences_preserved",
        "normalized_query": {"nct_ids": requested},
        "entries": entries,
        "pages": deepcopy(pages),
        "completed_pages": deepcopy(completed),
        "incomplete": failed,
        "source_version": {
            "value": version,
            "basis": "fixture_declared_data_timestamp"
            if fixture and version is not None
            else "registry_data_timestamp"
            if version is not None
            else "not_stated",
            "origin": "fixture" if fixture else "version_endpoint",
            "scope": "client_reported_data_timestamp_not_verified_per_page",
        },
        "response_identity": {
            "basis": "completed_page_receipts" if failed else "decoded_client_record",
            "hash": digest(canonical_json(completed if failed else result["record"])),
        },
        "clinical_context": {
            "rule": "clinicaltrials_registry_observation@1",
            "scope": "explicit_registry_references"
            if operation == "study_references"
            else "existing_clinical_fields",
            "identity_basis": "requested_source_stated_NCT_ids; intervention_names_not_matched",
            "entry_revision_basis": "native_last_update_post_date; not_content_revision_or_publication_date",
            "reference_target_access": "not_queried_by_this_operation",
            "references_requested": operation == "study_references",
            "fixture_scope": "frozen_public_subset; unsaved_ids_unavailable"
            if fixture
            else None,
            "api_version": next(
                (
                    page.get("api_version")
                    for page in pages
                    if page["outcome"] == "received" and "api_version" in page
                ),
                None,
            ),
            "requested_nct_ids": requested,
            "received_nct_ids": sorted({entry["nct_id"] for entry in good}),
        },
    }
    if failed:
        metadata["terminal_outcome"] = terminal
    else:
        metadata.update(
            retrieved_at=result["retrieved_at"], missing=deepcopy(result["missing"])
        )
    return metadata
