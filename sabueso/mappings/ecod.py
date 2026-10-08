"""Native ECOD experimental-domain classification, without residue projection."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "http://prodata.swmed.edu/ecod/api/v1/domains/"
LEVELS = ("architecture", "x_group", "h_group", "t_group", "family")


def uid_id(identifier):
    """Accept an explicit numeric UID string; zero padding has no numeric meaning."""
    if not isinstance(identifier, str) or not re.fullmatch(r"[0-9]{1,9}", identifier):
        raise ConnectorError("ECOD requires an explicit numeric domain UID string.")
    return str(int(identifier))


def response_query(identifier):
    return {"uid": int(uid_id(identifier))}


def validate_domain(payload, identifier):
    """Qualify the received experimental JSON shape, including false flags.

    The current native classification has id/name objects, whereas documentation
    examples show strings. Only the observed objects are qualified. Range text is
    opaque: neither author/sequential axes nor sequence revisions are stated here.
    AlphaFold domains and broader query/export shapes need separate qualification.
    """
    query = response_query(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("ECOD domain response is not finite JSON.") from error
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("uid"), int)
        or isinstance(payload["uid"], bool)
        or payload["uid"] != query["uid"]
        or payload.get("type") != "experimental structure"
    ):
        raise ConnectorError(
            "ECOD UID or qualified experimental-domain origin differs."
        )
    domain = payload.get("ecod_domain_id")
    match = (
        re.fullmatch(r"e([0-9][a-z0-9]{3})([A-Za-z0-9])([1-9][0-9]*)", domain)
        if isinstance(domain, str)
        else None
    )
    if (
        match is None
        or payload.get("chain_id") != match[2]
        or payload.get("source_id") != match[1] + "_" + match[2]
    ):
        raise ConnectorError("ECOD native domain/structure/chain identity differs.")
    if not isinstance(payload.get("range"), str) or not payload["range"].strip():
        raise ConnectorError("ECOD native range literal is missing.")
    if "uniprot_acc" not in payload or (
        payload["uniprot_acc"] is not None
        and (
            not isinstance(payload["uniprot_acc"], str)
            or not payload["uniprot_acc"].strip()
        )
    ):
        raise ConnectorError("ECOD native UniProt pointer is missing or malformed.")
    for key in ("is_representative", "is_manual"):
        if not isinstance(payload.get(key), bool):
            raise ConnectorError(
                "ECOD representative/manual flag is missing or malformed."
            )
    groups = payload.get("classification")
    if not isinstance(groups, dict):
        raise ConnectorError("ECOD classification is missing.")
    previous = None
    for index, level in enumerate(LEVELS):
        group = groups.get(level)
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("name"), str)
            or not group["name"].strip()
            or not isinstance(group.get("id"), str)
        ):
            raise ConnectorError(
                "ECOD native classification id/name object is malformed."
            )
        code = group["id"]
        pattern = (
            r"a\.[1-9][0-9]*"
            if index == 0
            else r"[1-9][0-9]*(?:\.[1-9][0-9]*){" + str(index - 1) + r"}"
        )
        # Native F=0 is an unassigned family, not a family inferred from its parent.
        if index == 4:
            pattern = r"[1-9][0-9]*(?:\.[1-9][0-9]*){2}\.(?:0|[1-9][0-9]*)"
        if not re.fullmatch(pattern, code) or (
            index > 1 and not code.startswith(previous + ".")
        ):
            raise ConnectorError(
                "ECOD native classification hierarchy is inconsistent."
            )
        previous = code
    files = payload.get("files")
    if not isinstance(files, dict) or any(
        files.get(key) != f"/ecod/api/v1/domains/{query['uid']}/{key}"
        for key in ("pdb", "fasta")
    ):
        raise ConnectorError("ECOD native file pointers differ from the domain UID.")
    return payload


def map_domain(envelope):
    """Record one domain classification on its ECOD UID, preserving native support."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "ECOD"
        or envelope.get("kind") != "domain"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"uid"}
        or not isinstance(envelope["query"]["uid"], int)
        or isinstance(envelope["query"]["uid"], bool)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError("ECOD mapping requires a complete native domain envelope.")
    identifier = uid_id(str(envelope["query"]["uid"]))
    record = validate_domain(envelope.get("record"), identifier)
    response_hash = digest(canonical_json(record))
    value = {
        k: deepcopy(record[k])
        for k in (
            "uid",
            "ecod_domain_id",
            "type",
            "source_id",
            "chain_id",
            "range",
            "uniprot_acc",
            "classification",
            "is_representative",
            "is_manual",
        )
    }
    assertion = make_source_assertion(
        "annotations.structural_domains.ecod",
        value,
        "ECOD",
        f"{identifier}:{response_hash}",
        envelope.get("retrieved_at"),
        subject_ref=f"ecod:uid:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_response": deepcopy(record),
        "response_hash": response_hash,
        "requested_api_version": "v1",
        "version_basis": "API_route_is_not_domain_classification_or_sequence_revision",
        "mapping_scope": {
            "identity": "explicit_ECOD_UID; native_PDB_chain_and_UniProt_pointer_only; no_protein_merge",
            "coordinates": "opaque_source_range_literal; axis_sequence_model_assembly_and_revisions_unstated; no_projection",
            "classification": "native_evolutionary_hierarchy_and_flags; no_function_prediction_or_MOLI_Evidence",
            "coverage": "one_experimental_domain; AlphaFold_domains_and_other_partitions_unqueried",
            "access": "one_explicit_HTTP_JSON_GET; no_protocol_fallback_search_assets_coordinates_sequence_or_jobs",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return [assertion]
