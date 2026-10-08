"""DisProt native region assertions, scoped to DisProt's own sequence."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError(
            "DisProt direct access requires a canonical UniProt accession."
        )
    return identifier.upper()


def validate_records(payload, identifier):
    """Reject cut, unrelated, duplicate or malformed native search results."""
    identifier = accession(identifier)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ConnectorError("DisProt response must state data and size.")
    total = payload.get("size")
    if (
        isinstance(total, bool)
        or not isinstance(total, int)
        or total != len(payload["data"])
    ):
        raise ConnectorError("DisProt search count is missing, inconsistent or capped.")
    try:
        json.dumps(payload, allow_nan=False)
    except (ValueError, TypeError) as error:
        raise ConnectorError("DisProt response is not finite JSON.") from error
    seen = set()
    for record in payload["data"]:
        if not isinstance(record, dict) or record.get("acc") != identifier:
            raise ConnectorError(
                "DisProt native accession does not match the requested protein."
            )
        native_id, sequence = record.get("disprot_id"), record.get("sequence")
        if (
            not isinstance(native_id, str)
            or not re.fullmatch(r"DP[0-9]{5,}", native_id)
            or native_id in seen
        ):
            raise ConnectorError(
                "DisProt native record identity is missing or repeated."
            )
        seen.add(native_id)
        if not isinstance(sequence, str) or not re.fullmatch(r"[A-Z]+", sequence):
            raise ConnectorError("DisProt native sequence is missing or malformed.")
        length = record.get("length")
        if (
            isinstance(length, bool)
            or not isinstance(length, int)
            or length != len(sequence)
        ):
            raise ConnectorError("DisProt length does not match its native sequence.")
        regions = record.get("regions")
        count = record.get("regions_counter")
        if (
            not isinstance(regions, list)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < len(regions)
        ):
            raise ConnectorError("DisProt regions/count are missing or inconsistent.")
        region_ids = set()
        for region in regions:
            if not isinstance(region, dict):
                raise ConnectorError("DisProt region is not an object.")
            region_id = region.get("region_id")
            if (
                not isinstance(region_id, str)
                or not re.fullmatch(re.escape(native_id) + r"r[0-9]+", region_id)
                or region_id in region_ids
            ):
                raise ConnectorError(
                    "DisProt region identity is unrelated or repeated."
                )
            region_ids.add(region_id)
            revision = region.get("version")
            if revision is not None and (
                isinstance(revision, bool)
                or not isinstance(revision, int)
                or revision < 0
            ):
                raise ConnectorError(
                    "DisProt region revision must be a non-negative integer."
                )
            for flag in ("term_is_obsolete", "term_not_annotate"):
                if flag in region and not isinstance(region[flag], bool):
                    raise ConnectorError(
                        "DisProt ontology flags must be explicit booleans."
                    )
            begin, end = region.get("start"), region.get("end")
            if (
                any(isinstance(n, bool) or not isinstance(n, int) for n in (begin, end))
                or not 1 <= begin <= end <= length
            ):
                raise ConnectorError("DisProt region is outside its stated sequence.")
            if not all(
                isinstance(region.get(key), str) and region[key]
                for key in ("term_id", "term_namespace")
            ):
                raise ConnectorError(
                    "DisProt region has no explicit native term/scope."
                )
    return payload


def map_disorder_regions(envelope):
    """Retain exact native disorder terms; do not place them on another sequence.

    Only structural-state IDPO:0000002 is selected. Other states, transitions and
    functions remain in the raw record. This is source access, not card enrichment.
    """
    if envelope.get("source") != "DisProt" or envelope.get("kind") != "records":
        raise ConnectorError(
            "DisProt mapping requires a native DisProt records envelope."
        )
    identifier = envelope["query"]["accession"]
    payload = validate_records(envelope["record"], identifier)
    assertions = []
    for record in payload["data"]:
        sequence_id = f"DisProt:{record['disprot_id']}"
        for region in record["regions"]:
            if (
                region["term_namespace"] != "Structural state"
                or region["term_id"] != "IDPO:0000002"
            ):
                continue
            if region.get("term_is_obsolete") or region.get("term_not_annotate"):
                continue
            assertion = make_source_assertion(
                "disorder.regions",
                {
                    "region_id": region["region_id"],
                    "term_id": region["term_id"],
                    "term_name": region.get("term_name"),
                    "location": {
                        "kind": "sequence",
                        "sequence": {
                            "sequence_id": sequence_id,
                            "indexing": "1-based",
                            "start": region["start"],
                            "end": region["end"],
                        },
                    },
                },
                "DisProt",
                region["region_id"],
                envelope.get("retrieved_at"),
                subject_ref=f"uniprot:{identifier}",
            )
            assertion["source"]["version"] = (
                str(region["version"]) if region.get("version") is not None else None
            )
            assertion["source_metadata"] = {
                "disprot_id": record["disprot_id"],
                "sequence": {
                    "id": sequence_id,
                    "value": record["sequence"],
                    "sha256": hashlib.sha256(record["sequence"].encode()).hexdigest(),
                    "uniprot_ref": f"uniprot:{identifier}",
                },
                "native_region": {
                    key: deepcopy(region[key])
                    for key in (
                        "ec_id",
                        "ec_name",
                        "reference_source",
                        "reference_id",
                        "released",
                        "date",
                        "curator_id",
                        "validated",
                        "sample",
                        "cross_refs",
                    )
                    if key in region
                },
                "regions_returned": len(record["regions"]),
                "regions_stated": record["regions_counter"],
                "scope": "returned_default_region_subset; source_sequence_only",
            }
            if "snapshot_receipt" in envelope:
                assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                    envelope["snapshot_receipt"]
                )
            assertions.append(assertion)
    return assertions
