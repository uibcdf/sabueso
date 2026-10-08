"""Native SWISS-MODEL Repository records with source-sequence alignment context."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import datetime

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "SWISS-MODEL Repository"
ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("SWISS-MODEL metadata requires a base UniProt accession.")
    return identifier.upper()


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _text(value):
    return isinstance(value, str) and bool(value)


def _alignment(segment, sequence):
    if not isinstance(segment, dict) or not isinstance(segment.get("uniprot"), dict):
        raise ConnectorError("SWISS-MODEL native target alignment is missing.")
    keys = [k for k in ("pdb", "smtl") if k in segment]
    if len(keys) != 1 or not isinstance(segment[keys[0]], dict):
        raise ConnectorError("SWISS-MODEL native template/PDB alignment is ambiguous.")
    target, template = segment["uniprot"], segment[keys[0]]
    for side in (target, template):
        if (
            not all(_integer(side.get(k)) for k in ("from", "to"))
            or side["from"] > side["to"]
            or not isinstance(side.get("aligned_sequence"), str)
            or not re.fullmatch(r"[A-Z-]+", side["aligned_sequence"])
        ):
            raise ConnectorError(
                "SWISS-MODEL native alignment bounds/text are malformed."
            )
    if (
        not 1 <= target["from"] <= target["to"] <= len(sequence)
        or target["aligned_sequence"].replace("-", "")
        != sequence[target["from"] - 1 : target["to"]]
        or len(target["aligned_sequence"]) != len(template["aligned_sequence"])
    ):
        raise ConnectorError(
            "SWISS-MODEL alignment differs from its target sequence/columns."
        )
    # Template bounds have their own native basis. No offset or author/label map is inferred.
    return target["from"], target["to"]


def validate_metadata(payload, identifier):
    """Validate native v2 identity, sequence/hash and every returned alignment.

    API version/query time and model creation/PDB release dates are separate from
    unknown scientific record revisions. The target MD5 is not a model identifier.
    Extra native context remains raw; numeric scores are not rescored/classified.
    """
    identifier = accession(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("SWISS-MODEL response is not finite JSON.") from error
    if not isinstance(payload, dict) or payload.get("api_version") != "2.0":
        raise ConnectorError(
            "SWISS-MODEL response requires the qualified native v2 format."
        )
    query = payload.get("query")
    if (
        not isinstance(query, dict)
        or query.get("ac") != identifier
        or query.get("identifiers") != identifier
        or any(
            k in query for k in ("provider", "template", "range", "from", "to", "sort")
        )
    ):
        raise ConnectorError(
            "SWISS-MODEL native query identity/scope differs from the request."
        )
    try:
        when = datetime.fromisoformat(payload.get("query_date"))
        if when.tzinfo is None:
            raise ValueError("Unstated query timezone")
    except (TypeError, ValueError) as error:
        raise ConnectorError(
            "SWISS-MODEL native query timestamp is malformed."
        ) from error
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ConnectorError("SWISS-MODEL result is missing.")
    sequence = result.get("sequence")
    if not isinstance(sequence, str) or not re.fullmatch(r"[A-Z]+", sequence):
        raise ConnectorError("SWISS-MODEL target sequence is missing or malformed.")
    md5 = hashlib.md5(sequence.encode("ascii")).hexdigest()  # nosec - native sequence checksum, not a security seal
    if (
        not _integer(result.get("sequence_length"))
        or result["sequence_length"] != len(sequence)
        or not isinstance(result.get("md5"), str)
        or result["md5"].lower() != md5
        or not isinstance(result.get("crc64"), str)
        or not re.fullmatch(r"[0-9A-Fa-f]{16}", result["crc64"])
    ):
        raise ConnectorError(
            "SWISS-MODEL sequence length/checksum context is inconsistent."
        )
    entries = result.get("uniprot_entries")
    if (
        not isinstance(entries, list)
        or not entries
        or any(
            not isinstance(e, dict)
            or not _text(e.get("ac"))
            or not ACCESSION.fullmatch(e["ac"])
            or not _text(e.get("id"))
            or "isoid" in e
            and (not _integer(e["isoid"]) or e["isoid"] < 1)
            for e in entries
        )
        or not any(e["ac"] == identifier for e in entries)
    ):
        raise ConnectorError(
            "SWISS-MODEL target entry references are missing or malformed."
        )
    structures = result.get("structures")
    if not isinstance(structures, list):
        raise ConnectorError("SWISS-MODEL native structure array is missing.")
    for row in structures:
        if (
            not isinstance(row, dict)
            or not all(
                _text(row.get(k))
                for k in (
                    "provider",
                    "template",
                    "method",
                    "coordinates",
                    "created_date",
                    "oligo-state",
                )
            )
            or not isinstance(row.get("md5"), str)
            or row["md5"].lower() != md5
            or not all(_integer(row.get(k)) for k in ("from", "to"))
            or not 1 <= row["from"] <= row["to"] <= len(sequence)
            or not _number(row.get("coverage"))
            or not 0 <= row["coverage"] <= 1
        ):
            raise ConnectorError(
                "SWISS-MODEL native structure context/bounds are malformed."
            )
        for k in ("gmqe", "identity", "similarity", "template_qsqe"):
            if k in row and row[k] is not None and not _number(row[k]):
                raise ConnectorError("SWISS-MODEL native score literal is malformed.")
        if (
            "qmean" in row
            and row["qmean"] is not None
            and (
                not isinstance(row["qmean"], dict)
                or any(v is not None and not _number(v) for v in row["qmean"].values())
            )
        ):
            raise ConnectorError(
                "SWISS-MODEL QMEAN must retain its native score dictionary."
            )
        chains = row.get("chains")
        if not isinstance(chains, list) or not chains:
            raise ConnectorError("SWISS-MODEL native chains are missing.")
        bounds = []
        for chain in chains:
            if (
                not isinstance(chain, dict)
                or not _text(chain.get("id"))
                or not isinstance(chain.get("segments"), list)
                or not chain["segments"]
            ):
                raise ConnectorError("SWISS-MODEL native chain segments are missing.")
            bounds.extend(_alignment(s, sequence) for s in chain["segments"])
        if (
            min(start for start, _ in bounds) != row["from"]
            or max(end for _, end in bounds) != row["to"]
        ):
            raise ConnectorError(
                "SWISS-MODEL outer target bounds differ from native segments."
            )
    return payload


def map_structures(envelope):
    """Keep each native repository occurrence; choose/fetch no structure or model.

    URLs are mutable download pointers, not immutable model IDs or acquired files.
    PDB/template numbering remains source-native; target matches establish only
    alignment to the returned source sequence, not current UniProt equivalence.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != SOURCE
        or envelope.get("kind") != "metadata"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"accession"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("SWISS-MODEL mapping requires a native metadata envelope.")
    identifier = accession(envelope["query"]["accession"])
    payload = validate_metadata(envelope.get("record"), identifier)
    result = payload["result"]
    sequence_hash = hashlib.sha256(result["sequence"].encode()).hexdigest()
    sequence_id = f"SWISS-MODEL:{identifier}:sha256:{sequence_hash}"
    assertions = []
    for index, row in enumerate(result["structures"]):
        row_hash = digest(canonical_json(row))
        assertion = make_source_assertion(
            "structures.repository_entries.swissmodel",
            {"native_structure": deepcopy(row), "target_sequence_id": sequence_id},
            SOURCE,
            f"{identifier}:{sequence_hash}:row:{index}:{row_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"uniprot:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_structure_hash": row_hash,
            "native_structure_index": index,
            "native_result_context": deepcopy(
                {k: v for k, v in result.items() if k != "structures"}
            ),
            "native_response_context": deepcopy(
                {k: v for k, v in payload.items() if k != "result"}
            ),
            "response_hash": digest(canonical_json(payload)),
            "native_query": deepcopy(payload["query"]),
            "native_query_date": payload["query_date"],
            "native_api_version": payload["api_version"],
            "native_uniprot_entries": deepcopy(result["uniprot_entries"]),
            "sequence": {
                "id": sequence_id,
                "value": result["sequence"],
                "sha256": sequence_hash,
                "md5": result["md5"],
                "crc64": result["crc64"],
                "revision": None,
            },
            "mapping_scope": {
                "identity": "native_query_reference_only; no_entry_or_isoform_merge",
                "coordinates": "alignment_to_returned_source_sequence; no_current_UniProt_or_author_label_projection",
                "revision": "API_query_and_creation_release_dates_are_not_record_or_sequence_revisions",
                "scores": "native_literals; no_rescoring_probability_or_quality_class",
                "model_identity": "native_MD5_hashes_target_sequence; URLs_do_not_pin_a_model_version",
                "coverage": "all_returned_occurrences; no_native_total_or_complete_database_claim",
                "unqueried": "coordinates_ModelCIF_templates_sequences_publications_and_jobs",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
