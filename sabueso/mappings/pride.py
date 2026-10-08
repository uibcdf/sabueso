"""Native PRIDE Archive project metadata on the depositor's dataset subject."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

PROJECT = re.compile(r"PXD[0-9]{6}\Z")
OBJECT_ARRAYS = (
    "instruments",
    "softwares",
    "experimentTypes",
    "quantificationMethods",
    "sampleAttributes",
    "organisms",
    "organismParts",
    "diseases",
    "references",
    "identifiedPTMStrings",
    "submitters",
    "labPIs",
    "additionalAttributes",
)


def project_id(identifier):
    if (
        not isinstance(identifier, str)
        or not PROJECT.fullmatch(identifier.upper())
        or identifier.upper() == "PXD000000"
    ):
        raise ConnectorError(
            "PRIDE requires one exact PXD plus six-digit project accession."
        )
    return identifier.upper()


def validate_project(payload, identifier):
    identifier = project_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("PRIDE project is not finite JSON.") from error
    if not isinstance(payload, dict) or payload.get("accession") != identifier:
        raise ConnectorError(
            "PRIDE response does not identify the exact requested project."
        )
    if not isinstance(payload.get("title"), str) or not payload["title"]:
        raise ConnectorError("PRIDE native project title is missing or malformed.")
    for k in (
        "license",
        "projectDescription",
        "sampleProcessingProtocol",
        "dataProcessingProtocol",
        "submissionType",
        "submissionDate",
        "publicationDate",
        "updatedDate",
        "doi",
    ):
        if k in payload and payload[k] is not None and not isinstance(payload[k], str):
            raise ConnectorError("PRIDE native project literal is malformed.")
    for k in OBJECT_ARRAYS:
        if (
            k in payload
            and payload[k] is not None
            and (
                not isinstance(payload[k], list)
                or any(not isinstance(v, dict) for v in payload[k])
            )
        ):
            raise ConnectorError("PRIDE native metadata object array is malformed.")
    for k in ("keywords", "projectTags", "countries", "otherOmicsLinks"):
        if (
            k in payload
            and payload[k] is not None
            and (
                not isinstance(payload[k], list)
                or any(not isinstance(v, str) for v in payload[k])
            )
        ):
            raise ConnectorError("PRIDE native metadata string array is malformed.")
    for k in ("totalFileDownloads", "botCount", "hubCount", "organicCount"):
        if (
            k in payload
            and payload[k] is not None
            and (type(payload[k]) is not int or payload[k] < 0)
        ):
            raise ConnectorError("PRIDE native administrative count is malformed.")
    return payload


def map_project(envelope):
    """Retain original dataset metadata, without importing results onto proteins.

    Protocols/descriptions stay depositor text; named modifications, organisms and
    instruments do not establish individual peptide/protein identifications or
    abundance, canonical positions, methods of a particular result or MOLI Evidence.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "PRIDE"
        or envelope.get("kind") != "project"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"project_accession"}
    ):
        raise ConnectorError("PRIDE mapping requires an exact native project envelope.")
    identifier = project_id(envelope["query"]["project_accession"])
    if envelope["query"]["project_accession"] != identifier:
        raise ConnectorError("PRIDE mapping query accession must be canonical.")
    record = validate_project(envelope.get("record"), identifier)
    record_hash = digest(canonical_json(record))
    assertion = make_source_assertion(
        "datasets.pride_project",
        deepcopy(record),
        "PRIDE",
        f"{identifier}:{record_hash}",
        envelope.get("retrieved_at"),
        subject_ref=f"pride:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_project": deepcopy(record),
        "response_hash": record_hash,
        "native_license": record.get("license"),
        "mapping_scope": {
            "identity": "native_PRIDE_dataset; no_title_search_protein_mapping_or_identity_merge",
            "support": "project_level_depositor_metadata_and_publication_pointers; not_per_peptide_or_protein_support",
            "origin": "PRIDE_Archive; no_PeptideAtlas_ProteomicsDB_or_generic_Proteins_API_relabeling",
            "interpretation": "original_depositor_protocol_and_description_text; no_project_results_imported_as_protein_knowledge_or_MOLI_Evidence",
            "revision": "submission_publication_and_API_dates_do_not_state_project_or_sequence_revision",
            "coverage": "one_native_metadata_response; not_file_peptide_protein_or_archive_coverage",
            "terms": "native_per_project_license; no_blanket_depositor_grant_or_linked_publication_rights",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return [assertion]
