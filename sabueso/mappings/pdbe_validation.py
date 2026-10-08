"""Entry-wide native PDBe validation metrics, without inferred quality classes."""

from __future__ import annotations

import math
import re
from copy import deepcopy

from sabueso.core.errors import ConnectorError, StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion


def pdb_id(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][A-Za-z0-9]{3}", identifier
    ):
        raise ConnectorError("PDBe validation requires a four-character PDB ID.")
    return identifier.lower()


def validate_percentiles(payload, identifier):
    """Check exact entry identity and native numeric domains before mapping."""
    identifier = pdb_id(identifier)
    if not isinstance(payload, dict) or set(payload) != {identifier}:
        raise ConnectorError("PDBe validation entry identity differs from the query.")
    try:
        canonical_json(payload)
    except (StorageError, TypeError, ValueError) as error:
        raise ConnectorError("PDBe validation response is not finite JSON.") from error
    metrics = payload[identifier]
    if not isinstance(metrics, dict):
        raise ConnectorError("PDBe validation must state a metric collection.")
    for name, values in metrics.items():
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(values, dict)
        ):
            raise ConnectorError(
                "PDBe validation metric identity/values are malformed."
            )
        for key in ("rawvalue", "absolute", "relative"):
            if key == "relative" and key not in values:
                continue  # Optional in the native API schema; never substitute zero.
            value = values.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or isinstance(value, float)
                and not math.isfinite(value)
                or key != "rawvalue"
                and not 0 <= value <= 100
            ):
                raise ConnectorError(
                    f"PDBe validation {name!r} has an invalid {key!r} value."
                )
    return payload


def map_global_percentiles(envelope):
    """Keep one structure-bound assertion per metric with all native numeric values.

    No quality threshold, aggregate score, experimental method or missing metric
    is inferred. Percentiles retain their native 0–100 scale; raw values keep
    their native definitions and are not converted into guessed physical units.
    """
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "PDBe Validation"
        or envelope.get("kind") != "global_percentiles"
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "PDBe validation requires its global-percentiles envelope."
        )
    identifier = pdb_id(envelope["query"].get("pdb_id"))
    payload = validate_percentiles(envelope.get("record"), identifier)
    if envelope.get("version") is not None or envelope.get("truncated") is not False:
        raise ConnectorError("PDBe validation revision/completeness is unsupported.")
    assertions = []
    for name, values in payload[identifier].items():
        assertion = make_source_assertion(
            "structures.validation.pdbe_global_percentiles",
            {
                "pdb_id": identifier.upper(),
                "metric": name,
                "native_values": deepcopy(values),
            },
            "PDBe Validation",
            f"{identifier}:{name}",
            envelope.get("retrieved_at"),
            subject_ref="pdb:" + identifier.upper(),
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "scope": "entry_wide_validation_metric; not_per_residue_or_protein_quality",
            "native_response_hash": digest(canonical_json(payload)),
            "metric_definitions": "https://www.ebi.ac.uk/pdbe/api/",
            "percentile_comparison": {
                "absolute": "all_possible_entries_in_the_PDB_archive",
                "relative": "comparable_entries; e.g._similar_resolution_for_X_ray",
                "scale": "0_to_100_native_percentile_rank",
            },
            "comparison_population": "counts_and_revision_not_stated",
            "validation_software_version": "not_stated",
            "raw_value_units": "not_stated_in_native_response; no_conversion",
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
