"""Native SIGNOR causal declarations without first-row loss or inferred binding."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)
RELATION = re.compile(r"SIGNOR-[1-9][0-9]*\Z")
NO_RESULTS = "No result found."
COLUMNS = (
    "ENTITYA",
    "TYPEA",
    "IDA",
    "DATABASEA",
    "ENTITYB",
    "TYPEB",
    "IDB",
    "DATABASEB",
    "EFFECT",
    "MECHANISM",
    "RESIDUE",
    "SEQUENCE",
    "TAX_ID",
    "CELL_DATA",
    "TISSUE_DATA",
    "MODULATOR_COMPLEX",
    "TARGET_COMPLEX",
    "MODIFICATIONA",
    "MODASEQ",
    "MODIFICATIONB",
    "MODBSEQ",
    "PMID",
    "DIRECT",
    "NOTES",
    "ANNOTATOR",
    "SENTENCE",
    "SIGNOR_ID",
    "SCORE",
)


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("SIGNOR requires one exact base UniProt accession.")
    return identifier.upper()


def organism(taxon_id):
    if (
        not isinstance(taxon_id, int)
        or isinstance(taxon_id, bool)
        or taxon_id not in (9606, 10090, 10116)
    ):
        raise ConnectorError(
            "SIGNOR organism requests support only 9606, 10090 and 10116."
        )
    return taxon_id


def response_query(identifier, taxon_id):
    return {
        "accession": accession(identifier),
        "requested_organism": organism(taxon_id),
    }


def parse_relations(text, identifier):
    """Validate every headerless native row; preserve quotes, unknowns and trailers.

    The documented field order has 28 columns. Current responses append one empty
    trailing field. Only those two exact shapes are qualified, without a header,
    row skipping, query expansion, score interpretation or taxonomy reassignment.
    """
    identifier = accession(identifier)
    if not isinstance(text, str):
        raise ConnectorError("SIGNOR requires original native TSV text.")
    if text == NO_RESULTS:
        return []
    rows = []
    try:
        reader = csv.reader(
            io.StringIO(text, newline=""),
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
            strict=True,
        )
        for values in reader:
            if len(values) not in (28, 29) or len(values) == 29 and values[-1] != "":
                raise ConnectorError(
                    "SIGNOR native headerless column count/trailer is unsupported."
                )
            row = dict(zip(COLUMNS, values[:28]))
            if (
                any(not row[k] for k in COLUMNS[:9])
                or not RELATION.fullmatch(row["SIGNOR_ID"])
                or row["DIRECT"] not in ("t", "f", "")
                or row["TAX_ID"]
                and not re.fullmatch(r"(?:-1|[1-9][0-9]*)", row["TAX_ID"])
            ):
                raise ConnectorError(
                    "SIGNOR native entity/relation/direct/taxonomy context is malformed."
                )
            matches = [
                side
                for side in ("A", "B")
                if row["ID" + side] == identifier
                and row["DATABASE" + side] == "UNIPROT"
                and row["TYPE" + side] == "protein"
            ]
            if not matches:
                raise ConnectorError(
                    "SIGNOR native row does not state the requested UniProt participant."
                )
            rows.append(
                {
                    "fields": row,
                    "native_columns": values,
                    "query_participant_sides": matches,
                }
            )
    except csv.Error as error:
        raise ConnectorError(f"Unreadable SIGNOR native TSV: {error}") from error
    return rows


def map_relations(envelope):
    """Retain independent native causal rows, roles, support and original source scope."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "SIGNOR"
        or envelope.get("kind") != "causal_relations"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"accession", "requested_organism"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "SIGNOR mapping requires a complete qualified native envelope."
        )
    query = response_query(
        envelope["query"]["accession"], envelope["query"]["requested_organism"]
    )
    rows = parse_relations(envelope.get("record"), query["accession"])
    response_hash = (
        "sha256:" + hashlib.sha256(envelope["record"].encode("utf-8")).hexdigest()
    )
    out = []
    for index, row in enumerate(rows):
        assertion = make_source_assertion(
            "signaling.causal_relations.signor",
            deepcopy(row["fields"]),
            "SIGNOR",
            f"{query['accession']}:{query['requested_organism']}:{index}:{row['fields']['SIGNOR_ID']}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"signor:uniprot:{query['accession']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "native_columns": deepcopy(row["native_columns"]),
            "query_participant_sides": deepcopy(row["query_participant_sides"]),
            "response_hash": response_hash,
            "query": query.copy(),
            "native_publication_pointer": row["fields"]["PMID"],
            "mapping_scope": {
                "identity": "exact_UNIPROT_protein_query_match; no_entity_merge_or_complex_expansion",
                "causality": "native_regulator_A_to_regulated_B_effect_mechanism; no_binding_or_experimental_class_inference",
                "taxonomy": "requested_organism_separate_from_native_TAX_ID; no_species_reassignment",
                "scores": "literal_provider_score; model_or_probability_revision_not_stated",
                "coordinates": "native_residue_sequence_modification_context; no_current_sequence_axis_or_projection",
                "revisions": "relation_export_sequence_and_score_revisions_not_stated; website_release_is_separate",
                "coverage": "all_received_occurrences; no_native_total_or_database_completeness_claim",
                "support": "native_PMID_and_sentence_context; underlying_publication_not_fetched",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        out.append(assertion)
    return out
