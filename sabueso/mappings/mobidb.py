"""MobiDB v1 export assertions, scoped to its original protein sequence."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniparc import ACCESSION


def accession(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        ACCESSION, identifier.upper()
    ):
        raise ConnectorError(
            "MobiDB direct access requires a canonical UniProt accession."
        )
    return identifier.upper()


def validate_export(payload, identifier):
    """Validate native identity, sequences and intervals; preserve reported issues."""
    identifier = accession(identifier)
    if not isinstance(payload, list) or len(payload) > 1:
        raise ConnectorError(
            "MobiDB single-protein export must contain at most one record."
        )
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("MobiDB export is not finite JSON.") from error
    for record in payload:
        if not isinstance(record, dict) or record.get("accession") != identifier:
            raise ConnectorError("MobiDB native accession differs from the query.")
        sequence, length = record.get("sequence"), record.get("length")
        if (
            not isinstance(sequence, str)
            or not re.fullmatch(r"[A-Z]+", sequence)
            or isinstance(length, bool)
            or not isinstance(length, int)
            or length != len(sequence)
            or record.get("coordinate_system") != "1-based-inclusive"
        ):
            raise ConnectorError(
                "MobiDB source sequence/length/coordinates are unsupported."
            )
        release = record.get("release")
        if (
            not isinstance(release, dict)
            or release.get("api_version") != "v1"
            or not isinstance(release.get("mobidb_version"), str)
            or not release["mobidb_version"]
            or not isinstance(release.get("release_date"), str)
            or not re.fullmatch(r"[0-9]{4}_(?:0[1-9]|1[0-2])", release["release_date"])
        ):
            raise ConnectorError(
                "MobiDB native release/API contract is missing or malformed."
            )
        annotations, issues = record.get("annotation_sets"), record.get("issues")
        if not isinstance(annotations, list) or not isinstance(issues, list):
            raise ConnectorError("MobiDB annotation sets/issues are missing.")
        if any(
            not isinstance(issue, dict)
            or any(
                not isinstance(issue.get(k), str) or not issue[k]
                for k in ("annotation_id", "field", "code")
            )
            for issue in issues
        ):
            raise ConnectorError("MobiDB representation issue is malformed.")
        seen = set()
        for annotation in annotations:
            if not isinstance(annotation, dict):
                raise ConnectorError("MobiDB annotation set is not an object.")
            native_id = annotation.get("annotation_id")
            if not isinstance(native_id, str) or not native_id or native_id in seen:
                raise ConnectorError(
                    "MobiDB annotation identity is missing or repeated."
                )
            seen.add(native_id)
            if not isinstance(annotation.get("kind"), str) or annotation[
                "kind"
            ] not in {"annotation", "positional"}:
                raise ConnectorError("MobiDB annotation kind is unsupported.")
            if "evidence" in annotation and (
                not isinstance(annotation["evidence"], str)
                or annotation["evidence"]
                not in {
                    "curated",
                    "derived",
                    "homology",
                    "prediction",
                }
            ):
                raise ConnectorError("MobiDB native annotation basis is unsupported.")
            if any(i["annotation_id"] == native_id for i in issues):
                # Reported normalization losses stay raw and are excluded by mappings.
                continue
            regions = annotation.get("regions", [])
            if not isinstance(regions, list):
                raise ConnectorError("MobiDB intervals must be an explicit list.")
            for region in regions:
                if not isinstance(region, dict):
                    raise ConnectorError("MobiDB interval is not an object.")
                start, end = region.get("start"), region.get("end")
                if (
                    any(
                        isinstance(n, bool) or not isinstance(n, int)
                        for n in (start, end)
                    )
                    or not 1 <= start <= end <= length
                ):
                    raise ConnectorError(
                        "MobiDB interval is outside its source sequence."
                    )
            series = annotation.get("residue_series", [])
            if not isinstance(series, list):
                raise ConnectorError("MobiDB residue series must be a list.")
            for track in series:
                if (
                    not isinstance(track, dict)
                    or not isinstance(track.get("start"), int)
                    or track.get("start") != 1
                    or isinstance(track.get("start"), bool)
                    or track.get("step") != 1
                    or not isinstance(track.get("step"), int)
                    or isinstance(track.get("step"), bool)
                    or not isinstance(track.get("values"), list)
                    or len(track["values"]) != length
                    or "missing_value" not in track
                    or track["missing_value"] is not None
                ):
                    raise ConnectorError(
                        "MobiDB series does not retain its full residue axis."
                    )
    return payload


def _regions(envelope, feature, path):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "MobiDB"
        or envelope.get("kind") != "annotations"
    ):
        raise ConnectorError("MobiDB mapping requires its native annotations envelope.")
    if not isinstance(envelope.get("query"), dict):
        raise ConnectorError("MobiDB mapping query is malformed.")
    identifier = accession(envelope["query"].get("accession"))
    payload = validate_export(envelope.get("record"), identifier)
    expected_version = payload[0]["release"]["mobidb_version"] if payload else None
    if (
        envelope.get("version") != expected_version
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("MobiDB envelope version or export scope differs.")
    assertions = []
    for record in payload:
        sequence = record["sequence"]
        sequence_id = f"MobiDB:{identifier}"
        for annotation in record["annotation_sets"]:
            if annotation.get("feature") != feature:
                continue
            native_id = annotation["annotation_id"]
            # A normalized surviving interval cannot repair a reported conversion loss.
            affected = [i for i in record["issues"] if i["annotation_id"] == native_id]
            if affected:
                continue
            for index, region in enumerate(annotation.get("regions", [])):
                value = {
                    "annotation_id": native_id,
                    "feature": feature,
                    "provider_basis": annotation.get("evidence"),
                    "provider_source": annotation.get("source"),
                    "location": {
                        "kind": "sequence",
                        "sequence": {
                            "sequence_id": sequence_id,
                            "indexing": "1-based",
                            "start": region["start"],
                            "end": region["end"],
                        },
                    },
                }
                if "label" in region:
                    value["description"] = deepcopy(region["label"])
                assertion = make_source_assertion(
                    path,
                    value,
                    "MobiDB",
                    f"{identifier}:{native_id}:{index}",
                    envelope.get("retrieved_at"),
                    subject_ref=f"uniprot:{identifier}",
                )
                assertion["source"]["version"] = expected_version
                assertion["source_metadata"] = {
                    "sequence": {
                        "id": sequence_id,
                        "value": sequence,
                        "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                        "uniprot_ref": f"uniprot:{identifier}",
                    },
                    "native_annotation_set": deepcopy(annotation),
                    "native_region": deepcopy(region),
                    "native_release": deepcopy(record["release"]),
                    "representation_issues": deepcopy(record["issues"]),
                    "mapping_scope": {
                        "rule": "mobidb_valid_region_sets@1",
                        "feature": feature,
                        "sets_with_reported_issues": "excluded; raw_export_retained",
                        "coordinates": "source_sequence_only; no_current_UniProt_equivalence",
                    },
                }
                if "snapshot_receipt" in envelope:
                    assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                        envelope["snapshot_receipt"]
                    )
                assertions.append(assertion)
    return assertions


def map_disorder_regions(envelope):
    """Read declared disorder intervals without conflating annotation bases."""
    return _regions(envelope, "disorder", "disorder.regions")


def map_modified_residues(envelope):
    """Retain native PTM labels/locations; original experimental basis may be absent."""
    return _regions(envelope, "ptm", "features_positional.modified_residue")
