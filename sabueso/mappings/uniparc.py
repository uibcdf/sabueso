"""Native UniParc sequence and returned UniProtKB reference declarations."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion

AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWYBXZJUO")
ACCESSION = (
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})"
)
REFERENCE = re.compile(
    rf"(?P<accession>{ACCESSION})(?P<isoform>-[1-9][0-9]*)?(?P<revision>\.[1-9][0-9]*)?\Z"
)


def checksum_key(checksum):
    if not isinstance(checksum, str) or not re.fullmatch(r"[0-9A-Fa-f]{32}", checksum):
        raise ConnectorError("UniParc requires a native MD5 sequence search key.")
    return checksum.upper()


def validate_results(results, checksum):
    checksum = checksum_key(checksum)
    if not isinstance(results, list):
        raise ConnectorError("UniParc results must be a native list.")
    seen = set()
    try:
        canonical_json(results)
    except (TypeError, ValueError, StorageError) as error:
        raise ConnectorError("UniParc results are not finite JSON.") from error
    for row in results:
        if not isinstance(row, dict):
            raise ConnectorError("UniParc entry is not an object.")
        native_id = row.get("uniParcId")
        if (
            not isinstance(native_id, str)
            or not re.fullmatch(r"UPI[0-9A-F]{10}", native_id)
            or native_id in seen
        ):
            raise ConnectorError("UniParc identity is missing, malformed or repeated.")
        seen.add(native_id)
        sequence = row.get("sequence")
        if not isinstance(sequence, dict):
            raise ConnectorError("UniParc sequence is not stated.")
        value, length, md5 = (
            sequence.get("value"),
            sequence.get("length"),
            sequence.get("md5"),
        )
        if not isinstance(value, str) or not value or set(value) - AMINO_ACIDS:
            raise ConnectorError("UniParc sequence alphabet is malformed.")
        actual_md5 = hashlib.md5(value.encode("ascii")).hexdigest().upper()  # nosec - native search key, not a security seal
        if (
            isinstance(length, bool)
            or not isinstance(length, int)
            or length != len(value)
            or not isinstance(md5, str)
            or md5.upper() != actual_md5
            or actual_md5 != checksum
        ):
            raise ConnectorError(
                "UniParc sequence length/checksum differs from the query."
            )
        references = row.get("uniProtKBAccessions")
        if not isinstance(references, list) or any(
            not isinstance(ref, str) or not REFERENCE.fullmatch(ref)
            for ref in references
        ):
            raise ConnectorError(
                "UniParc native UniProtKB references are malformed or missing."
            )
        if len(references) != len(set(references)):
            raise ConnectorError("UniParc native reference list repeats an accession.")
    return results


def map_sequence_records(envelope):
    """Keep sequence archive associations, never protein entity equivalence."""
    if envelope.get("source") != "UniParc" or envelope.get("kind") != "checksum_search":
        raise ConnectorError(
            "UniParc mapping requires a native checksum-search envelope."
        )
    rows = validate_results(
        envelope["record"]["results"], envelope["query"]["checksum"]
    )
    assertions = []
    for row in rows:
        native_id = row["uniParcId"]
        assertion = make_source_assertion(
            "sequence.archive_entry",
            {
                "uniparc_id": native_id,
                "sequence": {
                    key: row["sequence"][key] for key in ("value", "length", "md5")
                },
                "uniprotkb_accessions": deepcopy(row["uniProtKBAccessions"]),
            },
            "UniParc",
            native_id,
            envelope.get("retrieved_at"),
            subject_ref=f"uniparc:{native_id}",
        )
        assertion["source"]["version"] = envelope.get("version")
        assertion["source_metadata"] = {
            "native_record": deepcopy(row),
            "scope": "returned_search_UniProtKB_references; not_identity_equivalence",
            "search_total": envelope["record"]["total"],
            "search_truncated": envelope["truncated"],
        }
        assertions.append(assertion)
    return assertions
