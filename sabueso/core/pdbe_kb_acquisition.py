"""Observe PDBe-KB aggregates without claiming direct underlying source access."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_responses = ContextVar("sabueso_pdbe_kb_responses", default=None)


def note_response(payload):
    responses = _responses.get()
    if responses is not None:
        responses.append(deepcopy(payload))


def observe(operation, *, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            responses = []
            token = _responses.set(responses)

            def summary(result, query, is_fixture, requests):
                return summarize(
                    result, query, is_fixture, requests, responses, args[0]
                )

            try:
                return acquisition(
                    "PDBe-KB", operation, fixture=fixture, summarize=summary
                )(function)(*args, **kwargs)
            finally:
                _responses.reset(token)

        return observed

    return decorate


def _groups(record):
    groups = record.get("data") or []
    if not isinstance(groups, list):
        raise ValueError("PDBe-KB aggregate data is not a list")
    entries = []
    for index, group in enumerate(groups):
        entry = {"record_index": index}
        if not isinstance(group, dict):
            entry["outcome"] = "unobserved"
            entries.append(entry)
            continue
        residues = group.get("residues") or []
        extra = group.get("additionalData") or {}
        interactions = {
            canonical_json(item): item
            for residue in residues
            for item in residue.get("interactingPDBEntries") or []
        }
        entry.update(
            outcome="received",
            accession=deepcopy(group.get("accession")),
            name=deepcopy(group.get("name")),
            identifier_type=deepcopy(extra.get("type")),
            residue_record_count=len(residues),
            index_types=sorted(
                {r["indexType"] for r in residues if r.get("indexType")}
            ),
            listed_pdb_ids=deepcopy(extra.get("pdbEntries") or []),
            all_pdb_ids=sorted(
                {p for r in residues for p in r.get("allPDBEntries") or []}
            ),
            interacting_entries=[
                deepcopy(interactions[k]) for k in sorted(interactions)
            ],
            response_identity={
                "basis": "decoded_aggregate_group",
                "hash": digest(canonical_json(group)),
            },
        )
        entries.append(entry)
    return entries


def summarize(result, query, fixture, requests, responses, client):
    failed = isinstance(result, Exception)
    payload = responses[-1] if responses else None
    record = (
        payload
        if fixture
        else payload.get(query["accession"])
        if isinstance(payload, dict)
        else None
    )
    if not failed:
        record = result["record"]
    metadata = {
        "source_version": {"value": None, "basis": "not_stated"},
        "pages": [
            {
                "response_identity": {
                    "basis": "decoded_fixture_record"
                    if fixture
                    else "decoded_api_response",
                    "hash": digest(canonical_json(p)),
                }
            }
            for p in responses
        ],
    }
    outcome = _terminal(result, fixture, requests) if failed else "received"
    if not failed and not isinstance(record, dict):
        raise ValueError("PDBe-KB aggregate record is not an object")
    entries = _groups(record) if isinstance(record, dict) else []
    declared_groups = isinstance(record, dict) and isinstance(record.get("data"), list)
    count = len(entries) if declared_groups or not record else None
    data_basis = (
        "source_returned_data_list"
        if declared_groups
        else "empty_record"
        if not record
        else "not_stated"
    )
    if not failed:
        outcome = "empty" if count == 0 else "received"
        metadata["retrieved_at"] = result.get("retrieved_at")
    elif isinstance(result, RecordNotFoundError) and responses and not record:
        outcome = "empty"
        if fixture:
            metadata["retrieved_at"] = client.retrieved_at
    metadata.update(
        outcome=outcome,
        count=count,
        count_basis="source_returned_aggregate_groups_not_mapped_relationships",
        entries=entries,
        structural_context={
            "accession": query["accession"],
            "data_type": deepcopy(record.get("dataType"))
            if isinstance(record, dict)
            else None,
            "reference_basis": "PDBe-KB statements; listed PDB entries and linked providers were not consulted by this operation",
            "record_locator_basis": "zero_based_data_index_in_original_response",
            "aggregate_data_basis": data_basis,
            "returned_group_count": count,
        },
        response_identity={
            "basis": "decoded_completed_pages" if failed else "decoded_client_record",
            "hash": digest(canonical_json(metadata["pages"] if failed else record)),
        },
    )
    return metadata
