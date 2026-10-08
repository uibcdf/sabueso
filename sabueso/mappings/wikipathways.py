"""Literal WikiPathways bulk cross-references on independent pathway subjects."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import date

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "WikiPathways"
XREF_FIELDS = (
    "ncbigene",
    "ensembl",
    "hgnc",
    "uniprot",
    "wikidata",
    "chebi",
    "inchikey",
)
FIELDS = (
    "id",
    "url",
    "name",
    "species",
    "revision",
    "authors",
    "description",
) + XREF_FIELDS
IDENTIFIERS = {
    "uniprot": r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-[1-9][0-9]*)?",
    "ensembl": r"ENS[A-Z]*[GTP][0-9]+(?:\.[0-9]+)?",
    "ncbigene": r"[1-9][0-9]*",
    "wikidata": r"Q[1-9][0-9]*",
    "chebi": r"[1-9][0-9]*",
    "inchikey": r"[A-Z]{14}-[A-Z]{10}-[A-Z]",
}


def xref_id(identifier):
    """Require one literal supported namespaced ID; names and symbols are not joins."""
    if isinstance(identifier, str):
        namespace, _, value = identifier.partition(":")
        pattern = IDENTIFIERS.get(namespace)
        if pattern and re.fullmatch(pattern, value):
            return identifier
    raise ConnectorError(
        "WikiPathways requires one exact supported namespaced cross-reference."
    )


def response_query(identifier):
    return {
        "xref": xref_id(identifier),
        "dataset": "findPathwaysByXref",
        "scope": "all_received_pathways_and_native_xref_fields",
    }


def validate_export(payload):
    """Validate the full native response without repairing heterogeneous xref cells."""
    try:
        canonical_json(payload)
    except (StorageError, TypeError, OverflowError) as error:
        raise ConnectorError(
            "WikiPathways export must contain finite JSON values."
        ) from error
    if not isinstance(payload, dict) or not isinstance(
        payload.get("pathwayInfo"), list
    ):
        raise ConnectorError(
            "WikiPathways requires the native pathwayInfo bulk export."
        )
    for row in payload["pathwayInfo"]:
        if (
            not isinstance(row, dict)
            or any(not isinstance(row.get(key), str) for key in FIELDS)
            or not re.fullmatch(r"WP[1-9][0-9]*", row["id"])
            or row["url"] != "https://www.wikipathways.org/instance/" + row["id"]
            or not row["name"]
            or not row["species"]
            or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", row["revision"])
        ):
            raise ConnectorError(
                "WikiPathways native pathway shape or identity is malformed."
            )
        try:
            date.fromisoformat(row["revision"])
        except ValueError as error:
            raise ConnectorError(
                "WikiPathways native pathway revision label is malformed."
            ) from error
    return payload


def xref_matches(row, identifier):
    """Keep original field/group/alias positions for exact literal token matches.

    Native fields can contain other prefixes, blank aliases or free text. Do not
    repair columns, assume prefix from the field name or infer group equivalence.
    """
    out = []
    for field in XREF_FIELDS:
        for group_index, group in enumerate(row[field].split(",")):
            for alias_index, alias in enumerate(group.split(";")):
                if alias.strip() == identifier:
                    out.append(
                        {
                            "field": field,
                            "group_index": group_index,
                            "alias_index": alias_index,
                            "native_token": alias,
                        }
                    )
    return out


def map_pathway_cross_references(envelope):
    """Retain pathway declarations; xrefs do not establish mechanism or participation."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != SOURCE
        or envelope.get("kind") != "pathway_cross_references"
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "WikiPathways mapping requires a qualified native bulk export."
        )
    identifier = xref_id(envelope["query"].get("xref"))
    if envelope["query"] != response_query(identifier):
        raise ConnectorError(
            "WikiPathways mapping requires the exact cross-reference scope."
        )
    payload = validate_export(envelope.get("record"))
    response_hash = digest(canonical_json(payload))
    out = []
    for index, row in enumerate(payload["pathwayInfo"]):
        matches = xref_matches(row, identifier)
        if not matches:
            continue
        assertion = make_source_assertion(
            "pathways.cross_references.wikipathways",
            deepcopy(row),
            SOURCE,
            f"{row['url']}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref="wikipathways:" + row["id"],
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "received_export_rows": len(payload["pathwayInfo"]),
            "query_xref": identifier,
            "matched_xref_occurrences": matches,
            "native_pathway_revision": row["revision"],
            "mapping_scope": {
                "identity": "exact_literal_namespaced_tokens; no_alias_gene_protein_or_species_identity_merge",
                "meaning": "source_served_pathway_xrefs; no_GPML_node_role_mechanism_or_experimental_participation_claim",
                "coverage": "all_received_rows_validated; no_independent_database_total_or_species_filter",
                "representation": "provider_template_unique_compact_xref_groups_and_200_character_description; no_GPML_occurrence_coverage",
                "revisions": "native_pathway_date_label_retained; dataset_GPML_entity_and_sequence_revisions_unknown",
                "absence": "not_listed_in_received_export_is_not_no_pathway_or_biological_negative",
            },
        }
        for key in ("snapshot_receipt", "download_sha256"):
            if key in envelope:
                assertion["source_metadata"][key] = deepcopy(envelope[key])
        out.append(assertion)
    return out
