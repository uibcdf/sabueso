"""Native CATH domain summaries on their own structural sequence/numbering axes."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

DOMAIN = re.compile(r"[0-9][A-Za-z0-9]{3}[A-Za-z0-9][0-9]{2}\Z")
RELEASE = re.compile(r"v[1-9][0-9]*_(?:0|[1-9][0-9]*)_(?:0|[1-9][0-9]*)\Z")
PDB_NUMBER = re.compile(r"-?[0-9]+[A-Za-z]?\Z")


def domain_id(identifier):
    if not isinstance(identifier, str) or not DOMAIN.fullmatch(identifier):
        raise ConnectorError("CATH requires an explicit seven-character domain ID.")
    # PDB codes are case insensitive; native chain codes are not.
    return identifier[:4].lower() + identifier[4:]


def release_id(release):
    if not isinstance(release, str) or not RELEASE.fullmatch(release):
        raise ConnectorError("CATH requires an explicit fixed release such as v4_4_0.")
    return release


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _groups(value, count):
    return isinstance(value, str) and bool(
        re.fullmatch(r"[1-9][0-9]*(?:\.[1-9][0-9]*){" + str(count - 1) + r"}", value)
    )


def _bound(value):
    if _integer(value) and value > 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
        return int(value)
    raise ConnectorError("CATH COMBS segment boundary is malformed.")


def validate_summary(payload, identifier):
    """Check the complete qualified summary before mapping any of its fields.

    COMBS and ATOM are independent native sequences. The residue table explicitly
    pairs their letters with SEQRES/PDB literals; it does not supply UniProt positions.
    Segment order, mixed native boundary types, null PDB locations and insertions
    survive. Extra fields, GO/EC context and their native support remain unmodified.
    """
    identifier = domain_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("CATH summary is not finite JSON.") from error
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ConnectorError("CATH did not return a successful native domain summary.")
    data = payload.get("data")
    if (
        not isinstance(data, dict)
        or data.get("domain_id") != identifier
        or data.get("pdb_code") != identifier[:4]
    ):
        raise ConnectorError(
            "CATH native domain/PDB identity differs from the request."
        )
    if (
        not _groups(data.get("cath_id"), 9)
        or not _groups(data.get("superfamily_id"), 4)
        or not _groups(data.get("s35_id"), 5)
        or not data["cath_id"].startswith(data["s35_id"] + ".")
        or not data["s35_id"].startswith(data["superfamily_id"] + ".")
    ):
        raise ConnectorError("CATH native classification hierarchy is inconsistent.")
    for key in ("funfam_number", "ssg5_number", "ssg9_number"):
        if key not in data or (
            data[key] is not None and (not _integer(data[key]) or data[key] < 1)
        ):
            raise ConnectorError("CATH native family/group number is malformed.")
    for key in ("atom_sequence", "combs_sequence"):
        if not isinstance(data.get(key), str) or not re.fullmatch(r"[A-Z]+", data[key]):
            raise ConnectorError("CATH native sequence is missing or malformed.")
    if not _integer(data.get("atom_length")) or data["atom_length"] != len(
        data["atom_sequence"]
    ):
        raise ConnectorError("CATH native ATOM sequence length differs.")
    positions = []
    for key in ("combs_segments", "pdb_segments"):
        segments = data.get(key)
        if not isinstance(segments, list) or not segments:
            raise ConnectorError("CATH native segment array is missing or empty.")
        for segment in segments:
            if (
                not isinstance(segment, dict)
                or segment.get("pdb_code") != identifier[:4]
                or segment.get("chain_code") != identifier[4]
            ):
                raise ConnectorError("CATH native segment parent/chain differs.")
            if key == "combs_segments":
                begin, end = _bound(segment.get("start")), _bound(segment.get("stop"))
                # Bound allocation by the actual sequence, including discontinuous domains.
                if end < begin or end - begin + 1 > len(data["combs_sequence"]):
                    raise ConnectorError("CATH COMBS segment size is inconsistent.")
                positions.extend(range(begin, end + 1))
            elif any(
                not isinstance(segment.get(k), str)
                or not PDB_NUMBER.fullmatch(segment[k])
                for k in ("start", "stop")
            ):
                raise ConnectorError("CATH native PDB segment boundary is malformed.")
    residues = data.get("residues")
    if (
        not isinstance(residues, list)
        or len(residues) != len(data["combs_sequence"])
        or len(positions) != len(residues)
        or len(set(positions)) != len(positions)
    ):
        raise ConnectorError(
            "CATH residue table differs from its COMBS sequence/segments."
        )
    observed = []
    for index, row in enumerate(residues):
        if (
            not isinstance(row, dict)
            or not _integer(row.get("seqres"))
            or row["seqres"] != positions[index]
            or row.get("aa") != data["combs_sequence"][index]
            or "pdbres" not in row
        ):
            raise ConnectorError(
                "CATH residue correspondence differs from COMBS support."
            )
        location = row["pdbres"]
        if location is not None:
            if not isinstance(location, str) or not PDB_NUMBER.fullmatch(location):
                raise ConnectorError("CATH native PDB residue literal is malformed.")
            observed.append(row["aa"])
    if "".join(observed) != data["atom_sequence"]:
        raise ConnectorError("CATH observed residues differ from its ATOM sequence.")
    for key in ("go_terms", "ec_terms"):
        if not isinstance(data.get(key), list) or any(
            not isinstance(r, dict) for r in data[key]
        ):
            raise ConnectorError("CATH native term context is missing or malformed.")
    return data


def map_domain(envelope):
    """Keep one full domain observation, without protein identity or location inference."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "CATH"
        or envelope.get("kind") != "domain_summary"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"domain_id", "release"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "CATH mapping requires a complete native domain-summary envelope."
        )
    identifier = domain_id(envelope["query"]["domain_id"])
    release = release_id(envelope["query"]["release"])
    data = validate_summary(envelope.get("record"), identifier)
    response_hash = digest(canonical_json(envelope["record"]))
    assertion = make_source_assertion(
        "annotations.structural_domains.cath",
        deepcopy(data),
        "CATH",
        f"{release}:{identifier}:{response_hash}",
        envelope.get("retrieved_at"),
        subject_ref=f"cath:{release}:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "requested_release": release,
        "release_basis": "requested_route; response_does_not_state_release_or_record_revision",
        "response_hash": response_hash,
        "native_response": deepcopy(envelope["record"]),
        "mapping_scope": {
            "identity": "explicit_CATH_domain; no_UniProt_identity_merge",
            "coordinates": "native_COMBS_SEQRES_and_PDB_literals; no_canonical_projection_or_offset",
            "sequences": "independent_native_ATOM_and_COMBS; revisions_not_stated",
            "terms": "native_GO_and_EC_context_only; no_independent_function_or_experimental_assertion",
            "access": "one_selected_domain; no_search_coordinates_alignments_links_or_jobs",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return [assertion]
