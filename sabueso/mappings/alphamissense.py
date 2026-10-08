"""Source-scoped AlphaMissense substitutions, never clinical observations."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniparc import ACCESSION

AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
VARIANT = re.compile(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])\Z")
CLASSES = frozenset({"LBen", "LPath", "Amb"})


def accession(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        ACCESSION, identifier.upper()
    ):
        raise ConnectorError("AlphaMissense requires a canonical UniProt accession.")
    return identifier.upper()


def select_descriptor(discovery, identifier):
    """Select the exact full canonical host descriptor; retain all other records."""
    identifier = accession(identifier)
    if (
        not isinstance(discovery, dict)
        or discovery.get("source") != "AlphaFold DB"
        or discovery.get("kind") != "prediction"
        or discovery.get("query") != {"accession": identifier}
        or not isinstance(discovery.get("record"), list)
        or any(not isinstance(row, dict) for row in discovery["record"])
    ):
        raise ConnectorError("AlphaMissense discovery source/query/records differ.")
    try:
        canonical_json(discovery["record"])
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("AlphaMissense discovery is not finite JSON.") from error
    if any(
        not isinstance(row.get("uniprotAccession"), str)
        or not re.fullmatch(
            re.escape(identifier) + r"(?:-[1-9][0-9]*)?", row["uniprotAccession"]
        )
        for row in discovery["record"]
    ):
        raise ConnectorError("AlphaMissense discovery contains an unrelated protein.")
    candidates = [
        r for r in discovery["record"] if r.get("uniprotAccession") == identifier
    ]
    if len(candidates) > 1:
        raise ConnectorError(
            "AlphaMissense full canonical discovery is ambiguous or fragmented."
        )
    if not candidates:
        return None
    descriptor = candidates[0]
    url = descriptor.get("amAnnotationsUrl")
    if url is None:
        return None
    expected_id = f"AF-{identifier}-F1"
    if (
        descriptor.get("entryId", descriptor.get("modelEntityId")) != expected_id
        or not isinstance(descriptor.get("taxId"), int)
        or descriptor.get("taxId") != 9606
        or descriptor.get("isUniProt") is not True
        or url
        != f"https://alphafold.ebi.ac.uk/files/{expected_id}-aa-substitutions.csv"
    ):
        raise ConnectorError(
            "AlphaMissense artifact identity/host/taxon is unsupported or mismatched."
        )
    value = descriptor.get("uniprotSequence")
    if (
        not isinstance(value, str)
        or not value
        or set(value) - AMINO_ACIDS
        or descriptor.get("sequence") != value
        or any(
            isinstance(descriptor.get(key), bool)
            or not isinstance(descriptor.get(key), int)
            for key in ("sequenceStart", "sequenceEnd")
        )
        or descriptor.get("sequenceStart") != 1
        or descriptor.get("sequenceEnd") != len(value)
        or descriptor.get("isComplex") is True
    ):
        raise ConnectorError(
            "AlphaMissense discovery must state a full supported source sequence."
        )
    checksum = hashlib.md5(value.encode("ascii")).hexdigest()  # nosec - native sequence check
    if descriptor.get("sequenceChecksum") != checksum:
        raise ConnectorError(
            "AlphaMissense discovery checksum differs from its sequence."
        )
    return deepcopy(descriptor)


def variant_value(row, sequence):
    if not isinstance(row, dict) or any(not isinstance(v, str) for v in row.values()):
        raise ConnectorError("AlphaMissense native CSV row is malformed.")
    variant = row.get("protein_variant")
    match = VARIANT.fullmatch(variant) if isinstance(variant, str) else None
    if not match:
        raise ConnectorError("AlphaMissense substitution is malformed.")
    try:
        reference, position, alternate = match[1], int(match[2]), match[3]
    except ValueError as error:
        raise ConnectorError(
            "AlphaMissense position is not a supported integer."
        ) from error
    if (
        not 1 <= position <= len(sequence)
        or sequence[position - 1] != reference
        or reference == alternate
    ):
        raise ConnectorError(
            "AlphaMissense substitution disagrees with the discovery sequence."
        )
    literal = row.get("am_pathogenicity")
    if literal is None or "am_class" not in row:
        raise ConnectorError("AlphaMissense score/class columns are missing.")
    try:
        score = None if literal in {"", "NA"} else float(literal)
    except ValueError as error:
        raise ConnectorError("AlphaMissense score is not a numeric literal.") from error
    if score is not None and (not math.isfinite(score) or not 0 <= score <= 1):
        raise ConnectorError("AlphaMissense score is not finite or outside [0, 1].")
    classification = row["am_class"] or None
    return {
        "variant": variant,
        "position": position,
        "reference_aa": reference,
        "alternate_aa": alternate,
        "pathogenicity_score": score,
        "provider_class": classification,
        "model": "AlphaMissense",
        "knowledge_class": "predicted",
    }


def decode_csv(text, descriptor):
    """Validate every native row before applying a result cap, retaining literals."""
    if not isinstance(text, str):
        raise ConnectorError("AlphaMissense artifact must be CSV text.")
    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        names = reader.fieldnames
        if (
            not names
            or any(not n for n in names)
            or len(names) != len(set(names))
            or not {"protein_variant", "am_pathogenicity", "am_class"} <= set(names)
        ):
            raise ConnectorError("AlphaMissense CSV headers are missing or repeated.")
        rows = list(reader)
    except csv.Error as error:
        raise ConnectorError("AlphaMissense CSV is malformed.") from error
    seen = set()
    for row in rows:
        value = variant_value(row, descriptor["uniprotSequence"])
        if value["variant"] in seen:
            raise ConnectorError("AlphaMissense repeats a substitution.")
        if "uniprot_id" in row and row["uniprot_id"] != descriptor["uniprotAccession"]:
            raise ConnectorError("AlphaMissense native row accession differs.")
        seen.add(value["variant"])
    possible = len(descriptor["uniprotSequence"]) * 19
    return rows, {
        "rule": "single_aa_substitution_coverage@1",
        "observed": len(rows),
        "possible": possible,
        "complete_grid": len(rows) == possible,
        "missing": possible - len(rows),
        "basis": "validated_unique_rows; not_a_native_total_or_biological_absence",
    }


def validate_artifact(artifact, descriptor, limit):
    if (
        not isinstance(artifact, dict)
        or artifact.get("url") != descriptor["amAnnotationsUrl"]
    ):
        raise ConnectorError("AlphaMissense artifact URL differs from discovery.")
    text = artifact.get("csv")
    rows, coverage = decode_csv(text, descriptor)
    if (
        artifact.get("sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest()
        or artifact.get("rows") != rows[:limit]
        or isinstance(artifact.get("total"), bool)
        or not isinstance(artifact.get("total"), int)
        or artifact.get("total") != len(rows)
        or artifact.get("coverage") != coverage
    ):
        raise ConnectorError("AlphaMissense artifact content/hash/count/scope differ.")
    return artifact


def map_variants(envelope):
    """Map returned native substitutions on an explicit AlphaMissense source axis."""
    if (
        envelope.get("source") != "AlphaMissense"
        or envelope.get("kind") != "annotations"
    ):
        raise ConnectorError("AlphaMissense mapping requires its source envelope.")
    identifier = accession(envelope["query"]["accession"])
    limit = envelope["query"].get("limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ConnectorError("AlphaMissense envelope must state a positive row limit.")
    if envelope.get("version") is not None:
        raise ConnectorError("AlphaMissense artifact does not state a score version.")
    record = envelope["record"]
    descriptor = select_descriptor(record["discovery"], identifier)
    if descriptor is None:
        if record.get("artifact") is not None:
            raise ConnectorError("AlphaMissense artifact has no discovery declaration.")
        return []
    artifact = validate_artifact(
        record["artifact"], descriptor, envelope["query"]["limit"]
    )
    if not isinstance(envelope.get("truncated"), bool) or envelope["truncated"] != (
        artifact["total"] > len(artifact["rows"])
    ):
        raise ConnectorError("AlphaMissense returned-subset scope differs.")
    sequence = descriptor["uniprotSequence"]
    sequence_id = "AlphaMissense:" + (
        descriptor.get("entryId") or descriptor.get("modelEntityId")
    )
    assertions = []
    for row in artifact["rows"]:
        value = variant_value(row, sequence)
        value["location"] = {
            "kind": "sequence",
            "sequence": {
                "sequence_id": sequence_id,
                "start": value["position"],
                "end": value["position"],
                "indexing": "1-based",
            },
        }
        assertion = make_source_assertion(
            "variants.predicted_effects",
            value,
            "AlphaMissense",
            f"{identifier}:{value['variant']}",
            artifact.get("retrieved_at"),
            subject_ref=f"uniprot:{identifier}",
        )
        assertion["source"]["version"] = envelope.get("version")
        assertion["source_metadata"] = {
            "native_variant": deepcopy(row),
            "class_validation": {
                "rule": "native_alphamissense_class_vocabulary@1",
                "recognized": value["provider_class"] in CLASSES,
                "basis": "supported_native_AFDB_codes; provider_class_not_recomputed",
            },
            "discovery_descriptor": deepcopy(descriptor),
            "sequence": {
                "id": sequence_id,
                "value": sequence,
                "uniprot_ref": f"uniprot:{identifier}",
                "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                "basis": "host_discovery_sequence; every_native_reference_checked; not_current_UniProt_coordinate_equivalence",
            },
            "artifact_url": artifact["url"],
            "artifact_sha256": artifact["sha256"],
            "coverage": deepcopy(artifact["coverage"]),
            "returned_subset": envelope["truncated"],
            "score_version_basis": "not_stated; AlphaFold_model_version_is_not_AlphaMissense_version",
        }
        assertions.append(assertion)
    return assertions
