"""Native BRENDA EC-class descriptions, without protein activity transfer."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

URL = "https://sparql.dsmz.de/api/brenda"
EC_ROOT = "https://purl.dsmz.de/brenda/ec/"
FIELDS = ("ec", "label", "name", "description")
PREFIXES = (
    "PREFIX d3o: <https://purl.dsmz.de/schema/> "
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
    "PREFIX dcterms: <http://purl.org/dc/terms/> "
)
STRING = "http://www.w3.org/2001/XMLSchema#string"
LANG_STRING = "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString"


def response_query(identifier):
    """Bind one exact numeric EC literal; no wildcard or protein accession."""
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][0-9]*(?:\.(?:0|[1-9][0-9]*)){3}", identifier
    ):
        raise ConnectorError(
            "BRENDA requires an exact four-component numeric EC number."
        )
    sparql = (
        PREFIXES
        + "SELECT ?ec ?label ?name ?description WHERE { VALUES ?ec { <"
        + EC_ROOT
        + identifier
        + "> } ?ec a d3o:ECNumber ; rdfs:label ?label . "
        + "OPTIONAL { ?ec d3o:hasSystematicName ?name . } "
        + "OPTIONAL { ?ec dcterms:description ?description . } }"
    )
    return {"ec": identifier, "fields": list(FIELDS), "sparql": sparql}


def _literal(node):
    if (
        not isinstance(node, dict)
        or not {"type", "value"}
        <= set(node)
        <= {"type", "value", "datatype", "xml:lang"}
        or node["type"] not in ("literal", "typed-literal")
        or not isinstance(node["value"], str)
        or ("datatype" in node and node["datatype"] not in (STRING, LANG_STRING))
        or (node["type"] == "typed-literal" and "datatype" not in node)
        or (
            "xml:lang" in node
            and (
                not isinstance(node["xml:lang"], str)
                or not node["xml:lang"]
                or node.get("datatype", LANG_STRING) != LANG_STRING
            )
        )
        or (node.get("datatype") == LANG_STRING and "xml:lang" not in node)
    ):
        raise ConnectorError(
            "BRENDA selected descriptions require native RDF string terms."
        )


def validate_enzyme_class(payload, identifier):
    """Validate every solution; preserve missing OPTIONALs and empty literals."""
    response_query(identifier)
    try:
        canonical_json(payload)
    except (StorageError, ValueError, TypeError) as error:
        raise ConnectorError("BRENDA requires finite native JSON.") from error
    if (
        not isinstance(payload, dict)
        or set(payload) != {"head", "results"}
        or not isinstance(payload["head"], dict)
        or not {"vars"} <= set(payload["head"]) <= {"vars", "link"}
        or payload["head"]["vars"] != list(FIELDS)
        or (
            "link" in payload["head"]
            and (
                not isinstance(payload["head"]["link"], list)
                or any(not isinstance(v, str) for v in payload["head"]["link"])
            )
        )
        or not isinstance(payload["results"], dict)
        or set(payload["results"]) != {"bindings"}
        or not isinstance(payload["results"]["bindings"], list)
    ):
        raise ConnectorError(
            "Unsupported BRENDA SPARQL results, fields or cut metadata."
        )
    rows = payload["results"]["bindings"]
    for row in rows:
        if (
            not isinstance(row, dict)
            or not {"ec", "label"} <= set(row) <= set(FIELDS)
            or row["ec"] != {"type": "uri", "value": EC_ROOT + identifier}
        ):
            raise ConnectorError(
                "BRENDA native EC identity or binding scope differs from query."
            )
        for field in set(row) - {"ec"}:
            _literal(row[field])
    return rows


def map_enzyme_class(envelope):
    """Record source class descriptions on their own EC subject, retaining RDF terms."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "BRENDA"
        or envelope.get("kind") != "enzyme_class"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("BRENDA requires the qualified EC-class envelope.")
    query = envelope["query"]
    if query != response_query(query.get("ec")):
        raise ConnectorError("Unsupported BRENDA query or selected fields.")
    rows = validate_enzyme_class(envelope.get("record"), query["ec"])
    response_hash = digest(canonical_json(envelope["record"]))
    assertions = []
    for index, row in enumerate(rows):
        assertion = make_source_assertion(
            "annotations.enzyme_class_context",
            deepcopy(row),
            "BRENDA",
            f"{query['ec']}:{response_hash}:{index}",
            envelope.get("retrieved_at"),
            subject_ref=f"brenda:ec:{query['ec']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_response": deepcopy(envelope["record"]),
            "binding_index": index,
            "response_hash": response_hash,
            "query": deepcopy(query),
            "mapping_scope": {
                "identity": "native_EC_URI; no_protein_organism_or_similarity_identity_transfer",
                "classification": "source_EC_class_record; no_Sabueso_derived_assignment",
                "revision": "prototype_dataset_and_individual_class_revisions_not_stated",
                "coverage": "all_received_solutions_for_fixed_four_fields; no_database_completeness_claim",
                "kinetics": "unqueried; no_kinetic_constants_inhibitors_cofactors_or_activity_claim",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
