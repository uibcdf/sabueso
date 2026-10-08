"""Independent native APPRIS annotation occurrences on an explicit human gene."""

from __future__ import annotations

import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

GENE = re.compile(r"ENSG[0-9]{11}\Z")
TRANSCRIPT = re.compile(r"ENST[0-9]{11}\Z")
POSITIONS = re.compile(r"[1-9][0-9]*\Z")
REQUIRED = ("source", "type", "seqname", "start", "end", "strand", "frame")
OPTIONAL = (
    "annotation",
    "biotype",
    "ccds_id",
    "length_aa",
    "length_na",
    "no_codons",
    "note",
    "reliability",
    "score",
    "tag",
    "transcript_name",
    "tsl",
)


def gene_id(identifier):
    if not isinstance(identifier, str) or not GENE.fullmatch(identifier):
        raise ConnectorError(
            "APPRIS requires one exact unversioned human ENSG identifier."
        )
    return identifier


def validate_annotations(payload, identifier):
    """Check all received rows; never merge transcripts or parse genomic notes."""
    identifier = gene_id(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("APPRIS response is not finite JSON.") from error
    if not isinstance(payload, list):
        raise ConnectorError("APPRIS native exporter response must be an array.")
    for row in payload:
        if (
            not isinstance(row, dict)
            or row.get("gene_id") != identifier
            or not isinstance(row.get("transcript_id"), str)
            or not TRANSCRIPT.fullmatch(row["transcript_id"])
            or any(not isinstance(row.get(k), str) or not row[k] for k in REQUIRED)
            or any(k in row and not isinstance(row[k], str) for k in OPTIONAL)
        ):
            raise ConnectorError(
                "APPRIS native row identity/text fields are malformed."
            )
        if (
            not POSITIONS.fullmatch(row["start"])
            or not POSITIONS.fullmatch(row["end"])
            or int(row["start"]) > int(row["end"])
            or row["strand"] not in ("+", "-", ".")
            or row["frame"] not in (".", "0", "1", "2")
        ):
            raise ConnectorError(
                "APPRIS native genomic range/strand/frame is malformed."
            )
        # Genomic positions do not establish an assembly or a protein sequence axis.
        # Length, score, note and reliability fields remain source literals.
    return payload


def map_annotations(envelope):
    """Keep every native occurrence, including repeated/conflicting declarations.

    Source scores, flags, notes and genomic coordinates remain literal context.
    This adds no protein identity, principal-isoform selection, residue projection,
    experimental classification, linked acquisition or persisted card field.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "APPRIS"
        or envelope.get("kind") != "gene_annotations"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"gene_id", "species", "filters"}
        or envelope["query"]["species"] != "homo_sapiens"
        or envelope["query"]["filters"] != "provider_default"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "APPRIS mapping requires a complete qualified gene envelope."
        )
    identifier = gene_id(envelope["query"]["gene_id"])
    rows = validate_annotations(envelope.get("record"), identifier)
    response_hash = digest(canonical_json(rows))
    out = []
    for index, row in enumerate(rows):
        assertion = make_source_assertion(
            "annotations.isoforms.appris",
            deepcopy(row),
            "APPRIS",
            f"{identifier}:row:{index}:{response_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"appris:homo_sapiens:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row_index": index,
            "response_hash": response_hash,
            "received_rows": len(rows),
            "mapping_scope": {
                "identity": "native_gene_transcript_references; no_protein_identity_merge",
                "occurrences": "independent_native_rows; no_grouping_selection_or_overwrite",
                "interpretation": "native_scores_flags_notes; no_probability_or_experimental_class",
                "coordinates": "native_genomic_literals; assembly_and_sequence_axis_not_stated; no_residue_projection",
                "revisions": "dataset_record_transcript_and_sequence_revisions_not_stated",
                "coverage": "provider_default_received_rows; no_database_or_transcript_completeness_claim",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        out.append(assertion)
    return out
