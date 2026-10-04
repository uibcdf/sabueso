"""Observe InterPro's declared family-site residues, without running alignments."""

from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

from .errors import RecordNotFoundError
from .snapshot import canonical_json, digest
from .source_acquisition import _terminal, acquisition

_response = ContextVar("sabueso_interpro_response", default=None)


def note_version(version):
    response = _response.get()
    if response is not None:
        response["version"] = deepcopy(version)


def note_response(payload):
    response = _response.get()
    if response is not None:
        response["received"] = True
        response["payload"] = deepcopy(payload)


def observe(*, fixture=False):
    def decorate(function):
        @wraps(function)
        def observed(*args, **kwargs):
            response = {"received": False, "version": None}
            token = _response.set(response)
            try:
                return acquisition(
                    "InterPro",
                    "site_residues",
                    fixture=fixture,
                    summarize=lambda result, query, local, requests: summarize(
                        result, query, local, requests, response
                    ),
                )(function)(*args, **kwargs)
            finally:
                _response.reset(token)

        return observed

    return decorate


def summarize(result, query, fixture, requests, response):
    failed = isinstance(result, Exception)
    payload = response.get("payload")
    declared = (
        (isinstance(payload, dict) and "residues" in payload)
        if fixture
        else response["received"]
    )
    residues = (
        payload.get("residues")
        if fixture and isinstance(payload, dict)
        else payload
        if not fixture
        else None
    )
    version = (
        payload.get("version")
        if fixture and isinstance(payload, dict)
        else response["version"]
    )
    if not failed:
        residues = result.get("residues")
        version = result.get("version")
    entries = []
    for key, signature in residues.items() if isinstance(residues, dict) else ():
        entry = {
            "signature_key": key,
            "response_identity": {
                "basis": "decoded_signature_record",
                "hash": digest(canonical_json(signature)),
            },
        }
        if not isinstance(signature, dict):
            entry["outcome"] = "unobserved"
        else:
            locations = signature.get("locations")
            entry.update(
                outcome="received",
                signature_metadata={
                    k: deepcopy(signature[k])
                    for k in ("accession", "name", "source_database")
                    if k in signature
                },
                location_record_count=len(locations)
                if isinstance(locations, list)
                else None,
                locations=deepcopy(locations),
            )
        entries.append(entry)
    outcome = _terminal(result, fixture, requests) if failed else "received"
    if declared:
        if isinstance(residues, dict):
            if not residues:
                if not failed or isinstance(result, RecordNotFoundError):
                    outcome = "empty"
            elif any(e["outcome"] == "unobserved" for e in entries):
                outcome = (
                    "partial"
                    if any(e["outcome"] == "received" for e in entries)
                    else "unobserved"
                )
        else:
            outcome = "unobserved"
    elif response["received"]:
        outcome = "unobserved"
    pages = (
        [
            {
                "response_identity": {
                    "basis": "decoded_fixture_envelope"
                    if fixture
                    else "decoded_api_response",
                    "hash": digest(canonical_json(payload)),
                }
            }
        ]
        if response["received"]
        else []
    )
    metadata = {
        "outcome": outcome,
        "source_version": {
            "value": deepcopy(version),
            "basis": "fixture_declared_release"
            if fixture and version is not None
            else "response_header_release"
            if version is not None
            else "not_stated",
        },
        "count": len(residues) if isinstance(residues, dict) and declared else None,
        "count_basis": "source_returned_signature_records_not_mapped_sites",
        "entries": entries,
        "pages": pages,
        "completed_pages": pages
        if any(e["outcome"] == "received" for e in entries)
        else [],
        "response_identity": {
            "basis": "decoded_residue_response" if declared else "not_received",
            "hash": digest(canonical_json(residues)) if declared else None,
        },
        "annotation_context": {
            "kind": "family_site_residues",
            "accession": query["accession"],
            "record_basis": "source_returned_signature_map"
            if isinstance(residues, dict) and declared
            else "unexpected_response_shape"
            if response["received"]
            else "not_observed",
            "numbering_basis": "source_declared_protein_sequence_positions_not_locally_aligned",
            "validation_basis": "received_source_records_not_validated_mapped_sites",
            "reference_basis": "InterPro statements; member databases and UniProt were not consulted by this operation",
            "absence_basis": "no_site_residues_or_unknown_accession_cannot_be_distinguished",
            "execution_basis": "source_access_not_InterProScan_or_member_database_analysis",
        },
    }
    if not failed:
        metadata["retrieved_at"] = result.get("retrieved_at")
    if outcome == "partial":
        metadata["incomplete"] = True
    return metadata
