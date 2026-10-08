"""Explicit UniProt isoform declarations and native FASTA sequence assertions."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

BASE = r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})"
ISOFORM = re.compile(BASE + r"-[1-9][0-9]*\Z")


def isoform_id(identifier):
    if not isinstance(identifier, str) or not ISOFORM.fullmatch(identifier.upper()):
        raise ConnectorError(
            "Supply an explicit base UniProt accession with a positive isoform suffix."
        )
    return identifier.upper()


def _positive(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def select_isoform(parent, identifier):
    """Validate all native declarations; names do not determine isoform IDs.

    Missing declaration scope and explicit not-listed selection stay distinct.
    External/unknown/not-described sequences are retained without following links.
    """
    identifier = isoform_id(identifier)
    accession = identifier.rsplit("-", 1)[0]
    try:
        canonical_json(parent)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("UniProt isoform parent is not finite JSON.") from error
    if (
        not isinstance(parent, dict)
        or parent.get("primaryAccession") != accession
        or parent.get("entryType") == "Inactive"
    ):
        raise ConnectorError("UniProt isoform parent identity/active entry differs.")
    sequence = parent.get("sequence")
    if (
        not isinstance(sequence, dict)
        or not isinstance(sequence.get("value"), str)
        or not re.fullmatch(r"[A-Z]+", sequence["value"])
        or not _positive(sequence.get("length"))
        or sequence["length"] != len(sequence["value"])
    ):
        raise ConnectorError("UniProt parent sequence/length is malformed.")
    if (
        "md5" in sequence
        and sequence["md5"]
        != hashlib.md5(sequence["value"].encode()).hexdigest().upper()
    ):
        raise ConnectorError("UniProt parent sequence checksum differs.")
    audit = parent.get("entryAudit", {})
    if not isinstance(audit, dict) or any(
        k in audit and not _positive(audit[k])
        for k in ("entryVersion", "sequenceVersion")
    ):
        raise ConnectorError("UniProt parent revision context is malformed.")
    comments = parent.get("comments", [])
    if not isinstance(comments, list) or any(not isinstance(c, dict) for c in comments):
        raise ConnectorError("UniProt parent comments are malformed.")
    declared, known, unknown, ids = [], False, False, set()
    for comment in comments:
        if comment.get("commentType") != "ALTERNATIVE PRODUCTS":
            continue
        if "isoforms" not in comment:
            unknown = True
            continue
        known = True
        if not isinstance(comment["isoforms"], list):
            raise ConnectorError("UniProt native isoform array is malformed.")
        for row in comment["isoforms"]:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("name"), dict)
                or not isinstance(row["name"].get("value"), str)
                or not row["name"]["value"]
                or not isinstance(row.get("isoformIds"), list)
                or not row["isoformIds"]
                or not isinstance(row.get("isoformSequenceStatus"), str)
                or not row["isoformSequenceStatus"]
            ):
                raise ConnectorError("UniProt native isoform declaration is malformed.")
            for value in row["isoformIds"]:
                if (
                    not isinstance(value, str)
                    or not ISOFORM.fullmatch(value)
                    or value in ids
                ):
                    raise ConnectorError(
                        "UniProt isoform references are malformed or ambiguous."
                    )
                ids.add(value)
            if "sequenceIds" in row and (
                not isinstance(row["sequenceIds"], list)
                or any(
                    not isinstance(value, str) or not re.fullmatch(r"VSP_[0-9]+", value)
                    for value in row["sequenceIds"]
                )
                or len(set(row["sequenceIds"])) != len(row["sequenceIds"])
            ):
                raise ConnectorError(
                    "UniProt native alternative sequence pointers are malformed."
                )
            if row["isoformSequenceStatus"] == "Described" and not row.get(
                "sequenceIds"
            ):
                raise ConnectorError(
                    "UniProt described isoform has no alternative sequence pointers."
                )
            if identifier in row["isoformIds"]:
                declared.append(row)
    if not declared:
        return None, "not_declared" if known and not unknown else "not_stated"
    row = declared[0]
    status = row["isoformSequenceStatus"]
    outcome = {
        "Displayed": "declared",
        "Described": "declared",
        "Not described": "sequence_not_stated",
        "External": "external_sequence_not_followed",
    }.get(status, "sequence_status_unqualified")
    return row, outcome


def parse_fasta(document, identifier):
    """Require one native, explicitly identified isoform FASTA, without repair."""
    identifier = isoform_id(identifier)
    if not isinstance(document, str) or not document or not document.isascii():
        raise ConnectorError("UniProt isoform FASTA is missing or non-ASCII.")
    lines = document.splitlines()
    match = re.fullmatch(r">(sp)\|([^|\s]+)\|([^\s|]+) Isoform ([^\r\n]+)", lines[0])
    if (
        not match
        or match.group(2) != identifier
        or len(lines) < 2
        or any(not re.fullmatch(r"[A-Z]+", line) for line in lines[1:])
    ):
        raise ConnectorError(
            "UniProt isoform FASTA identity or single-record sequence differs."
        )
    return "".join(lines[1:]), lines[0]


def validate_components(parent, sequence, identifier):
    """Validate separate component observations without reconstructing variants."""
    declaration, status = select_isoform(parent.get("record"), identifier)
    if status != "declared":
        if sequence is not None:
            raise ConnectorError(
                "UniProt sequence was fetched outside declared isoform scope."
            )
        return declaration, status, None
    if not isinstance(sequence, dict) or sequence.get("version") is not None:
        raise ConnectorError(
            "UniProt isoform sequence/revision component is unsupported."
        )
    value, _ = parse_fasta(sequence.get("record"), identifier)
    if (
        declaration["isoformSequenceStatus"] == "Displayed"
        and value != parent["record"]["sequence"]["value"]
    ):
        raise ConnectorError(
            "UniProt displayed isoform disagrees with the parent sequence."
        )
    return declaration, "received", value


def map_isoform_sequence(envelope):
    """Keep the acquired sequence and source-declared parent association.

    Parent revisions and VAR_SEQ pointers are separate from unknown isoform
    sequence revision. No variant reconstruction or canonical residue map is made.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "UniProt"
        or envelope.get("kind") != "isoform_sequence"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"isoform_id"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "UniProt isoform mapping requires an explicit sequence envelope."
        )
    identifier = isoform_id(envelope["query"]["isoform_id"])
    record = envelope.get("record")
    if not isinstance(record, dict) or set(record) != {
        "parent_entry",
        "isoform_sequence",
        "selection_status",
    }:
        raise ConnectorError("UniProt isoform component record is malformed.")
    parent, sequence = record["parent_entry"], record["isoform_sequence"]
    if (
        not isinstance(parent, dict)
        or parent.get("source") != "UniProt"
        or parent.get("kind") != "isoform_parent"
        or parent.get("query") != {"accession": identifier.rsplit("-", 1)[0]}
    ):
        raise ConnectorError("UniProt parent envelope identity/scope differs.")
    select_isoform(parent.get("record"), identifier)
    if parent.get("truncated") is not False:
        raise ConnectorError("UniProt parent component scope is truncated or unstated.")
    expected_version = (
        (parent.get("record", {}).get("entryAudit") or {}).get("entryVersion")
        if isinstance(parent.get("record"), dict)
        else None
    )
    if parent.get("version") != (
        str(expected_version) if expected_version is not None else None
    ):
        raise ConnectorError("UniProt parent revision declaration differs.")
    if sequence is not None and (
        not isinstance(sequence, dict)
        or sequence.get("source") != "UniProt"
        or sequence.get("kind") != "isoform_fasta"
        or sequence.get("query") != {"isoform_id": identifier}
        or sequence.get("truncated") is not False
    ):
        raise ConnectorError("UniProt FASTA component identity/scope differs.")
    declaration, status, value = validate_components(parent, sequence, identifier)
    if record["selection_status"] != status:
        raise ConnectorError("UniProt isoform selection declaration differs.")
    if value is None:
        return []
    parent_hash = digest(canonical_json(parent["record"]))
    fasta_hash = hashlib.sha256(sequence["record"].encode()).hexdigest()
    sha256 = hashlib.sha256(value.encode()).hexdigest()
    accession = identifier.rsplit("-", 1)[0]
    assertion = make_source_assertion(
        "sequence.isoform_sequences",
        {
            "sequence_id": f"UniProt:{identifier}",
            "isoform_id": identifier,
            "value": value,
            "length": len(value),
            "native_header": sequence["record"].splitlines()[0],
        },
        "UniProt",
        f"{identifier}:parent:{parent_hash}:fasta:sha256:{fasta_hash}",
        sequence.get("retrieved_at"),
        subject_ref=f"uniprot:{accession}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "sequence": {
            "id": f"UniProt:{identifier}",
            "value": value,
            "sha256": sha256,
            "uniprot_ref": f"uniprot:{accession}",
            "revision": None,
        },
        "native_isoform_declaration": deepcopy(declaration),
        "parent_entry": deepcopy(parent),
        "isoform_sequence": deepcopy(sequence),
        "parent_response_hash": parent_hash,
        "native_fasta_sha256": fasta_hash,
        "mapping_scope": {
            "identity": "exact_FASTA_isoform_ID_and_native_parent_declaration; names_do_not_define_IDs",
            "revision": "parent_entry_and_canonical_sequence_versions_are_not_isoform_sequence_revisions",
            "coordinates": "native_isoform_sequence_only; no_canonical_offset_or_structural_mapping",
            "variants": "native_VSP_pointers_retained; no_sequence_reconstruction",
            "access": "explicit_parent_and_selected_FASTA_only; other_isoforms_and_links_unqueried",
        },
    }
    return [assertion]
