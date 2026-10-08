"""GlyGen modification assertions on the sequence stated in its protein record."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

ACCESSION = re.compile(
    r"(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\Z"
)
TABLES = ("glycosylation", "phosphorylation")


def accession(identifier):
    if not isinstance(identifier, str) or not ACCESSION.fullmatch(identifier.upper()):
        raise ConnectorError("GlyGen access requires a base UniProt accession.")
    return identifier.upper()


def validate_protein(payload, identifier):
    """Validate identity, source sequence and complete requested modification tables.

    Missing coordinates remain unstated. Native ranges remain ranges rather than
    assertions that every residue in a range is modified. Publication/database
    pointers remain source declarations, not independently acquired support.
    """
    identifier = accession(identifier)
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("GlyGen response is not finite JSON.") from error
    if not isinstance(payload, dict) or "error_list" in payload:
        raise ConnectorError("GlyGen protein record is missing or reports an error.")
    uniprot, sequence = payload.get("uniprot"), payload.get("sequence")
    if not isinstance(uniprot, dict) or not re.fullmatch(
        re.escape(identifier) + r"-[1-9][0-9]*",
        str(uniprot.get("uniprot_canonical_ac", "")),
    ):
        raise ConnectorError("GlyGen canonical record does not match the query.")
    if (
        not isinstance(sequence, dict)
        or not isinstance(sequence.get("sequence"), str)
        or not re.fullmatch(r"[A-Z]+", sequence["sequence"])
    ):
        raise ConnectorError("GlyGen source sequence is missing or malformed.")
    length = len(sequence["sequence"])
    for declared in (sequence.get("length"), uniprot.get("length")):
        if (
            isinstance(declared, bool)
            or not isinstance(declared, int)
            or declared != length
        ):
            raise ConnectorError(
                "GlyGen sequence length differs from its declarations."
            )
    stats = payload.get("section_stats")
    if not isinstance(stats, list) or any(not isinstance(s, dict) for s in stats):
        raise ConnectorError("GlyGen section counts are missing or malformed.")
    for table in TABLES:
        rows = payload.get(table)
        sections = [s for s in stats if s.get("table_id") == table]
        if not isinstance(rows, list) or len(sections) != 1:
            raise ConnectorError(
                "GlyGen modification table/count is missing or repeated."
            )
        entries = sections[0].get("table_stats")
        if not isinstance(entries, list) or any(
            not isinstance(s, dict) for s in entries
        ):
            raise ConnectorError("GlyGen table statistics are malformed.")
        totals = [s.get("count") for s in entries if s.get("field") == "total"]
        if (
            len(totals) != 1
            or isinstance(totals[0], bool)
            or not isinstance(totals[0], int)
            or totals[0] != len(rows)
        ):
            raise ConnectorError(
                "GlyGen modification rows differ from the native total."
            )
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("evidence"), list):
                raise ConnectorError("GlyGen modification row/support is malformed.")
            for pointer in row["evidence"]:
                if not isinstance(pointer, dict) or any(
                    not isinstance(pointer.get(k), str) or not pointer[k]
                    for k in ("database", "id", "url")
                ):
                    raise ConnectorError("GlyGen native support pointer is malformed.")
            for key in ("start_pos", "end_pos"):
                number = row.get(key)
                if number is not None and (
                    isinstance(number, bool) or not isinstance(number, int)
                ):
                    raise ConnectorError(
                        "GlyGen site numbering is not an integer or unstated."
                    )
            for key in (
                "residue",
                "start_aa",
                "end_aa",
                "site_seq",
                "site_lbl",
                "comment",
                "glytoucan_ac",
                "type",
                "subtype",
                "site_category",
                "relation",
            ):
                if key in row and not isinstance(row[key], str):
                    raise ConnectorError(
                        "GlyGen native annotation literal is malformed."
                    )
            if table == "glycosylation" and any(
                not isinstance(row.get(k), str) or not row[k]
                for k in ("type", "site_category", "relation")
            ):
                raise ConnectorError(
                    "GlyGen glycosylation category/type/relation is unstated."
                )
    return payload


def _map(envelope, table, field):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "GlyGen"
        or envelope.get("kind") != "protein"
        or not isinstance(envelope.get("query"), dict)
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "GlyGen mapping requires a complete native protein envelope."
        )
    identifier = accession(envelope["query"].get("accession"))
    payload = validate_protein(envelope.get("record"), identifier)
    canonical_ac = payload["uniprot"]["uniprot_canonical_ac"]
    sequence = payload["sequence"]["sequence"]
    sequence_id = f"GlyGen:{canonical_ac}"
    record_hash = digest(canonical_json(payload))
    assertions = []
    for index, row in enumerate(payload[table]):
        value = {"glygen_canonical_ac": canonical_ac, "annotation_table": table}
        for key in (
            "type",
            "subtype",
            "site_category",
            "residue",
            "start_aa",
            "end_aa",
            "site_seq",
            "site_lbl",
            "comment",
            "glytoucan_ac",
            "relation",
            "evidence",
            "kinase_uniprot_canonical_ac",
            "kinase_gene_name",
        ):
            if key in row:
                value[key] = deepcopy(row[key])
        begin, end = row.get("start_pos"), row.get("end_pos")
        # A range describes uncertain localization, not modification of all its residues.
        if isinstance(begin, int) and begin == end and 1 <= begin <= len(sequence):
            value["location"] = {
                "kind": "sequence",
                "sequence": {
                    "sequence_id": sequence_id,
                    "indexing": "1-based",
                    "start": begin,
                    "end": end,
                },
            }
            placement = "source_stated_single_site; no_current_UniProt_equivalence"
        else:
            placement = "native_range_or_unlocated; no_single_residue_placement"
        row_hash = digest(canonical_json(row))
        assertion = make_source_assertion(
            field,
            value,
            "GlyGen",
            f"{canonical_ac}:{table}:{index}:{row_hash}",
            envelope.get("retrieved_at"),
            subject_ref=f"uniprot:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "sequence": {
                "id": sequence_id,
                "value": sequence,
                "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                "uniprot_ref": f"uniprot:{identifier}",
            },
            "native_uniprot": deepcopy(payload["uniprot"]),
            "native_annotation": deepcopy(row),
            "native_history": deepcopy(payload.get("history")),
            "native_section_stats": deepcopy(
                next(s for s in payload["section_stats"] if s.get("table_id") == table)
            ),
            "response_hash": record_hash,
            "native_annotation_hash": row_hash,
            "mapping_scope": {
                "coordinates": placement,
                "origin": "native_category_and_support_only; no_curated_or_experimental_class",
                "support": "native_pointers; linked_sources_and_articles_not_acquired",
                "revision": "not_stated; introduction_history_is_not_current_revision",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions


def map_glycosylation(envelope):
    """Retain independent reported, predicted and text-mined glycan/site annotations."""
    return _map(envelope, "glycosylation", "features_positional.glycosylation")


def map_phosphorylation(envelope):
    """Retain literal phosphorylation and kinase/support context on the source axis."""
    return _map(envelope, "phosphorylation", "features_positional.modified_residue")
