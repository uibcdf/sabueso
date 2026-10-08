"""PDB-REDO refinement stages, independent of deposited structure quality."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import date

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

R_FACTORS = {
    "deposited": ("RFACT", "RFREE"),
    "baseline_refmac": ("RCAL", "RFCAL"),
    "restrained_refinement": ("RTLS", "RFTLS"),
    "final_pdb_redo": ("RFIN", "RFFIN"),
}


def pdb_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError("PDB-REDO requires one four-character public PDB ID.")
    return identifier.lower()


def validate_record(payload, identifier, component="entry"):
    identifier = pdb_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("PDB-REDO response is not finite JSON.") from error
    if not isinstance(payload, dict):
        raise ConnectorError("PDB-REDO record is not an object.")
    if component == "versions":
        data, software = payload.get("data"), payload.get("software")
        if (
            not isinstance(data, dict)
            or data.get("PDBID") != identifier
            or not isinstance(software, dict)
        ):
            raise ConnectorError(
                "PDB-REDO version record identity/software is malformed."
            )
        for item in software.values():
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("used"), bool)
                or "version" not in item
                or item["version"] is not None
                and not isinstance(item["version"], str)
            ):
                raise ConnectorError(
                    "PDB-REDO native software version/use is malformed."
                )
        return payload
    if (
        component != "entry"
        or payload.get("pdbid") != identifier
        or not isinstance(payload.get("properties"), dict)
    ):
        raise ConnectorError(
            "PDB-REDO native entry identity/properties differ or are missing."
        )
    properties = payload["properties"]
    for keys in R_FACTORS.values():
        for key in keys:
            value = properties.get(key)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise ConnectorError(
                    "PDB-REDO R-factor must be a native fraction or null."
                )
    if (
        "VERSION" in properties
        and properties["VERSION"] is not None
        and (
            isinstance(properties["VERSION"], bool)
            or not isinstance(properties["VERSION"], (int, float))
            or properties["VERSION"] <= 0
        )
    ):
        raise ConnectorError("PDB-REDO pipeline version is malformed.")
    if "TIME" in properties:
        try:
            if (
                not isinstance(properties["TIME"], str)
                or date.fromisoformat(properties["TIME"]).isoformat()
                != properties["TIME"]
            ):
                raise ValueError("Not an ISO date")
        except ValueError as error:
            raise ConnectorError(
                "PDB-REDO entry creation date is malformed."
            ) from error
    return payload


def _validated(envelope, component):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "PDB-REDO"
        or envelope.get("kind") != component
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("PDB-REDO mapping requires its native scoped envelope.")
    identifier = pdb_id(envelope["query"].get("pdb_id"))
    return identifier, validate_record(envelope.get("record"), identifier, component)


def _assertion(envelope, identifier, record, field, value):
    assertion = make_source_assertion(
        field,
        value,
        "PDB-REDO",
        identifier,
        envelope.get("retrieved_at"),
        subject_ref="pdb:" + identifier.upper(),
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_record": deepcopy(record),
        "native_response_hash": digest(canonical_json(record)),
        "scope": "source_re_refinement_context; no_new_experiment_or_automatic_model_replacement",
        "databank_revision": "not_stated; pipeline_version_and_creation_date_are_separate",
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return assertion


def map_refinement(envelope):
    """Keep deposited, baseline, restrained and final R-factors as distinct native stages.

    Other properties, coordinates and angle/residue arrays remain native metadata.
    No improvement, physical-unit normalization or parent revision is inferred.
    """
    identifier, record = _validated(envelope, "entry")
    properties = record["properties"]
    stages = {}
    for stage, keys in R_FACTORS.items():
        values = {key: deepcopy(properties[key]) for key in keys if key in properties}
        if values:
            stages[stage] = values
    if not stages:
        return []
    value = {
        "pdb_id": identifier.upper(),
        "r_factor_stages": stages,
        "pipeline_context": {
            key: deepcopy(properties[key])
            for key in ("VERSION", "TIME", "EXPTYP")
            if key in properties
        },
    }
    return [
        _assertion(
            envelope, identifier, record, "structures.refinements.pdb_redo", value
        )
    ]


def map_versions(envelope):
    """Keep source-declared input revisions and used/software flags without merging models."""
    identifier, record = _validated(envelope, "versions")
    return [
        _assertion(
            envelope,
            identifier,
            record,
            "structures.refinement_provenance.pdb_redo",
            deepcopy(record),
        )
    ]
