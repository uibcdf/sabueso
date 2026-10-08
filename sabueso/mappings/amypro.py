"""AmyPro entry context and regions on their original investigated sequence."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion

ENTRY_ID = re.compile(r"AP[0-9]{5}\Z")
TEXT_FIELDS = (
    "protein_name",
    "species",
    "sequence",
    "description",
    "class_name",
    "prion_domain",
    "uniprot_id",
    "uniprot_start",
    "uniprot_end",
    "pdb_id",
)


def entry_id(identifier):
    if (
        not isinstance(identifier, str)
        or not ENTRY_ID.fullmatch(identifier.upper())
        or identifier.upper() == "AP00000"
    ):
        raise ConnectorError("AmyPro requires an explicit AP plus five-digit entry ID.")
    return identifier.upper()


def validate_export(payload):
    """Check the whole received export before selecting a native entry.

    Parent UniProt bounds and mutation strings stay literal: they do not prove
    sequence equivalence, a valid offset or mutation interpretation. Region bounds
    refer to the investigated entry sequence and must match its declared peptide.
    Missing regions are distinct from an explicitly empty region dictionary.
    """
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("AmyPro export is not finite JSON.") from error
    if not isinstance(payload, list):
        raise ConnectorError("AmyPro export must be its native entry array.")
    seen = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ConnectorError("AmyPro entry is malformed.")
        identifier = entry_id(row.get("entry_id"))
        if row["entry_id"] != identifier or identifier in seen:
            raise ConnectorError("AmyPro native entry ID is noncanonical or repeated.")
        seen.add(identifier)
        if any(not isinstance(row.get(k), str) for k in TEXT_FIELDS):
            raise ConnectorError("AmyPro entry literals are missing or malformed.")
        sequence = row["sequence"]
        if not re.fullmatch(r"[A-Z]+", sequence):
            raise ConnectorError(
                "AmyPro investigated sequence is missing or malformed."
            )
        for key in ("mutations", "pubmed_ids"):
            if not isinstance(row.get(key), list) or any(
                not isinstance(v, str) or not v for v in row[key]
            ):
                raise ConnectorError(
                    "AmyPro mutation/publication literals are malformed."
                )
        if any(not re.fullmatch(r"[1-9][0-9]*", v) for v in row["pubmed_ids"]):
            raise ConnectorError("AmyPro native PubMed pointer is malformed.")
        regions = row.get("regions")
        if not isinstance(regions, dict):
            raise ConnectorError("AmyPro region dictionary is missing or malformed.")
        for name, region in regions.items():
            if not isinstance(name, str) or not name or not isinstance(region, dict):
                raise ConnectorError("AmyPro region declaration is malformed.")
            bounds, peptide = (
                region.get("region_indices"),
                region.get("region_sequence"),
            )
            if (
                not isinstance(bounds, str)
                or not re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*", bounds)
                or not isinstance(peptide, str)
                or not re.fullmatch(r"[A-Z]+", peptide)
            ):
                raise ConnectorError("AmyPro region bounds/peptide are malformed.")
            start, end = map(int, bounds.split("-"))
            if (
                not 1 <= start <= end <= len(sequence)
                or sequence[start - 1 : end] != peptide
            ):
                raise ConnectorError(
                    "AmyPro region differs from its investigated sequence."
                )
    return payload


def select_entry(payload, identifier):
    identifier = entry_id(identifier)
    validate_export(payload)
    return next((r for r in payload if r["entry_id"] == identifier), None)


def _context(envelope):
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "AmyPro"
        or envelope.get("kind") != "entry"
        or not isinstance(envelope.get("query"), dict)
        or set(envelope["query"]) != {"entry_id"}
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
    ):
        raise ConnectorError(
            "AmyPro mapping requires a native full-export entry envelope."
        )
    identifier = entry_id(envelope["query"]["entry_id"])
    return identifier, select_entry(envelope.get("record"), identifier)


def _assertion(envelope, row, field, value, locator):
    identifier = row["entry_id"]
    assertion = make_source_assertion(
        field,
        deepcopy(value),
        "AmyPro",
        f"{identifier}:{digest(canonical_json(row))}:{locator}",
        envelope.get("retrieved_at"),
        subject_ref=f"amypro:{identifier}",
    )
    assertion["source"]["version"] = None
    assertion["source_metadata"] = {
        "native_entry": deepcopy(row),
        "native_entry_hash": digest(canonical_json(row)),
        "export_hash": digest(canonical_json(envelope["record"])),
        "received_export_count": len(envelope["record"]),
        "sequence": {
            "id": f"AmyPro:{identifier}",
            "value": row["sequence"],
            "sha256": hashlib.sha256(row["sequence"].encode()).hexdigest(),
            "indexing": "1-based",
            "revision": None,
        },
        "mapping_scope": {
            "identity": "AmyPro_entry; parent_UniProt_pointer_does_not_merge_entities",
            "coordinates": "investigated_entry_sequence; no_parent_or_current_UniProt_projection",
            "origin": "native_categories_only; no_experimental_or_curated_class_assigned",
            "support": "entry_level_PubMed_pointers; no_region_specific_support_or_method_returned",
            "revision": "record_sequence_and_export_revisions_not_stated",
            "coverage": "received_export_only; no_native_total_or_current_database_completeness_claim",
        },
    }
    if "snapshot_receipt" in envelope:
        assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
            envelope["snapshot_receipt"]
        )
    return assertion


def map_entry(envelope):
    """Retain native categories, parent bounds, mutations and publication pointers."""
    _, row = _context(envelope)
    if row is None:
        return []
    value = {k: deepcopy(v) for k, v in row.items() if k != "regions"}
    value["sequence_id"] = f"AmyPro:{row['entry_id']}"
    return [
        _assertion(envelope, row, "sequence.aggregation_context.amypro", value, "entry")
    ]


def map_regions(envelope):
    """Retain each declared region independently, on the entry's own sequence axis."""
    _, row = _context(envelope)
    if row is None:
        return []
    assertions = []
    for name, region in row["regions"].items():
        start, end = map(int, region["region_indices"].split("-"))
        value = {
            "entry_id": row["entry_id"],
            "region_id": name,
            "native_region": deepcopy(region),
            "class_name": row["class_name"],
            "prion_domain": row["prion_domain"],
            "location": {
                "kind": "sequence",
                "sequence": {
                    "sequence_id": f"AmyPro:{row['entry_id']}",
                    "indexing": "1-based",
                    "start": start,
                    "end": end,
                },
            },
        }
        assertions.append(
            _assertion(
                envelope,
                row,
                "sequence.aggregation_regions.amypro",
                value,
                f"region:{name}:{digest(canonical_json(region))}",
            )
        )
    return assertions
