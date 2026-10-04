"""Observe declared model versions and resources without running model generation."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_responses = ContextVar("sabueso_alphafold_responses", default=None)
_METADATA = (
    "entryId",
    "modelEntityId",
    "latestVersion",
    "allVersions",
    "toolUsed",
    "providerId",
    "entityType",
    "isComplex",
    "isUniProt",
    "uniprotAccession",
    "uniprotStart",
    "uniprotEnd",
    "sequenceStart",
    "sequenceEnd",
    "sequenceChecksum",
    "modelCreatedDate",
    "sequenceVersionDate",
    "chainId",
)
_LINKS = (
    "bcifUrl",
    "cifUrl",
    "pdbUrl",
    "paeImageUrl",
    "paeDocUrl",
    "plddtDocUrl",
    "msaUrl",
)


def note_response(payload):
    responses = _responses.get()
    if responses is not None:
        responses.append(deepcopy(payload))


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            responses = []
            token = _responses.set(responses)
            try:
                return acquisition(
                    "AlphaFold DB",
                    "prediction",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, responses
                    ),
                )(function)(*args, **kwargs)
            finally:
                _responses.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, responses):
    failed = isinstance(result, Exception)
    payload = responses[-1] if responses else None
    if not failed:
        payload = result.get("record")
    pages = [
        {
            "response_identity": {
                "basis": "decoded_fixture_record"
                if fixture
                else "decoded_api_response",
                "hash": digest(canonical_json(p)),
            }
        }
        for p in responses
    ]
    entries, versions, completed = [], [], []
    models = payload if isinstance(payload, list) else []
    for index, model in enumerate(models):
        entry = {
            "record_index": index,
            "response_identity": {
                "basis": "decoded_model_record",
                "hash": digest(canonical_json(model)),
            },
        }
        if not isinstance(model, dict):
            entry.update(
                outcome="unobserved",
                source_version={"value": None, "basis": "not_stated"},
            )
            entries.append(entry)
            continue
        version = model.get("latestVersion")
        entry.update(
            outcome="received",
            model_id=deepcopy(model.get("entryId") or model.get("modelEntityId")),
            identifier_basis="entryId"
            if model.get("entryId")
            else "modelEntityId"
            if model.get("modelEntityId")
            else "not_stated",
            source_version={
                "value": deepcopy(version),
                "basis": "model_version" if version is not None else "not_stated",
            },
            model_metadata={k: deepcopy(model[k]) for k in _METADATA if k in model},
            artifact_links={k: deepcopy(model[k]) for k in _LINKS if k in model},
        )
        if version is not None:
            versions.append(
                {
                    "record_index": index,
                    "model_id": entry["model_id"],
                    "value": deepcopy(version),
                }
            )
        if entry["model_id"] is not None:
            completed.append(deepcopy(entry["model_id"]))
        entries.append(entry)
    outcome = _terminal(result, fixture, requests) if failed else "received"
    if isinstance(payload, list):
        if not payload:
            if not failed or isinstance(result, RecordNotFoundError):
                outcome = "empty"
        elif any(e["outcome"] == "unobserved" for e in entries):
            outcome = (
                "partial"
                if any(e["outcome"] == "received" for e in entries)
                else "unobserved"
            )
    elif responses or not failed:
        # The original client may return or reject a non-list envelope; neither
        # establishes a completed, evaluated-empty model list.
        outcome = "unobserved"
    metadata = {
        "outcome": outcome,
        "count": len(models) if isinstance(payload, list) else None,
        "count_basis": "source_returned_model_records_not_mapped_relationships",
        "entries": entries,
        "completed_ids": completed,
        "pages": pages,
        "completed_pages": pages
        if any(e["outcome"] == "received" for e in entries)
        else [],
        "source_version": {
            "value": versions or None,
            "basis": "per_model_version" if versions else "not_stated",
        },
        "response_identity": {
            "basis": "decoded_received_response" if responses else "not_received",
            "hash": digest(canonical_json(payload)) if responses else None,
        },
        "structural_context": {
            "kind": "predicted_models",
            "model_list_basis": "source_returned_model_list"
            if isinstance(payload, list)
            else "unexpected_response_shape"
            if responses
            else "not_observed",
            "accession": query["accession"],
            "record_locator_basis": "zero_based_index_in_original_model_list",
            "version_basis": "native_latestVersion_per_record_not_global_database_release",
            "generation_basis": "source_declared_tool_and_provider_not_executed_by_this_access",
            "artifact_access": "declared_links_not_downloaded",
            "reference_basis": "AlphaFold DB statements; linked providers and UniProt were not consulted by this operation",
        },
    }
    if not failed:
        metadata["retrieved_at"] = result.get("retrieved_at")
    if outcome == "partial":
        metadata["incomplete"] = True
    return metadata
