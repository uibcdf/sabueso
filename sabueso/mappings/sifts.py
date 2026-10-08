"""Native SIFTS segment correspondences; never calculate residue remapping."""

from __future__ import annotations

import math
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.uniparc import ACCESSION


def pdb_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError("SIFTS direct access requires a four-character PDB ID.")
    return identifier.lower()


def validate_mappings(payload, identifier):
    """Retain exact references and numbering, rejecting unrelated or invalid segments."""
    identifier = pdb_id(identifier)
    if not isinstance(payload, dict) or set(payload) != {identifier}:
        raise ConnectorError("SIFTS native PDB identity differs from the query.")
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("SIFTS response is not finite JSON.") from error
    record = payload[identifier]
    if not isinstance(record, dict) or not isinstance(record.get("UniProt"), dict):
        raise ConnectorError("SIFTS must state an explicit UniProt mapping collection.")
    for accession, reference in record["UniProt"].items():
        if not isinstance(accession, str) or not re.fullmatch(
            ACCESSION + r"(?:-[1-9][0-9]*)?", accession
        ):
            raise ConnectorError("SIFTS native UniProt reference is unsupported.")
        if not isinstance(reference, dict) or not isinstance(
            reference.get("mappings"), list
        ):
            raise ConnectorError("SIFTS mapping segments are missing.")
        seen = set()
        for mapping in reference["mappings"]:
            if not isinstance(mapping, dict):
                raise ConnectorError("SIFTS segment is not an object.")
            identity = canonical_json(mapping)
            if identity in seen:
                raise ConnectorError("SIFTS repeats an identical segment.")
            seen.add(identity)
            entity, start, end = (
                mapping.get(k) for k in ("entity_id", "unp_start", "unp_end")
            )
            if (
                any(
                    isinstance(n, bool) or not isinstance(n, int)
                    for n in (entity, start, end)
                )
                or entity < 1
                or not 1 <= start <= end
                or any(
                    not isinstance(mapping.get(k), str) or not mapping[k]
                    for k in ("chain_id", "struct_asym_id")
                )
            ):
                raise ConnectorError(
                    "SIFTS entity/chain/UniProt interval is malformed."
                )
            for key in ("start", "end"):
                location = mapping.get(key)
                if not isinstance(location, dict):
                    raise ConnectorError("SIFTS structure endpoint is missing.")
                number = location.get("residue_number")
                author = location.get("author_residue_number")
                if (
                    isinstance(number, bool)
                    or not isinstance(number, int)
                    or number < 1
                    or "author_residue_number" not in location
                    or author is not None
                    and (isinstance(author, bool) or not isinstance(author, int))
                    or "author_insertion_code" not in location
                    or location["author_insertion_code"] is not None
                    and not isinstance(location["author_insertion_code"], str)
                ):
                    raise ConnectorError(
                        "SIFTS author/internal residue numbering is malformed."
                    )
            if mapping["start"]["residue_number"] > mapping["end"]["residue_number"]:
                raise ConnectorError("SIFTS internal residue interval is reversed.")
            for key in ("identity", "coverage"):
                value = mapping.get(key)
                if key in mapping and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or not 0 <= value <= 1
                ):
                    raise ConnectorError(
                        "SIFTS native identity/coverage is outside [0, 1]."
                    )
    return payload


def map_sequence_mappings(envelope):
    """Retain each source-declared segment; do not extrapolate endpoints or merge entities."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "SIFTS"
        or envelope.get("kind") != "mappings"
    ):
        raise ConnectorError("SIFTS mapping requires its native mappings envelope.")
    query = envelope.get("query")
    if not isinstance(query, dict):
        raise ConnectorError("SIFTS mapping query is malformed.")
    identifier = pdb_id(query.get("pdb_id"))
    payload = validate_mappings(envelope.get("record"), identifier)
    if envelope.get("version") is not None or envelope.get("truncated") is not False:
        raise ConnectorError(
            "SIFTS native response does not state a release or partial-export scope."
        )
    assertions = []
    for accession, reference in payload[identifier]["UniProt"].items():
        for mapping in reference["mappings"]:
            value = {
                "pdb_id": identifier.upper(),
                "uniprot_ref": "uniprot:" + accession,
                "entity_id": mapping["entity_id"],
                "author_chain_id": mapping["chain_id"],
                "label_asym_id": mapping["struct_asym_id"],
                "uniprot_range": {
                    "start": mapping["unp_start"],
                    "end": mapping["unp_end"],
                    "indexing": "1-based-inclusive",
                },
                "pdb_start": deepcopy(mapping["start"]),
                "pdb_end": deepcopy(mapping["end"]),
            }
            for key in ("identity", "coverage"):
                if key in mapping:
                    value[key] = mapping[key]
            assertion = make_source_assertion(
                "structures.sequence_mappings.sifts",
                value,
                "SIFTS",
                f"{identifier}:{accession}:{digest(canonical_json(mapping))}",
                envelope.get("retrieved_at"),
                subject_ref="pdb:" + identifier.upper(),
            )
            assertion["source"]["version"] = None
            assertion["source_metadata"] = {
                "native_mapping": deepcopy(mapping),
                "native_reference": {
                    k: deepcopy(v) for k, v in reference.items() if k != "mappings"
                },
                "scope": "source_segment_correspondence; no_per_residue_offset_or_sequence_reconstruction",
                "sequence_revision": "not_stated; not_current_UniProt_or_isoform_sequence_equivalence",
            }
            if "snapshot_receipt" in envelope:
                assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                    envelope["snapshot_receipt"]
                )
            assertions.append(assertion)
    return assertions
