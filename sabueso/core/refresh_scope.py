"""Reconstruct requested enrichment scope, without inferring it from selected facts."""

from __future__ import annotations

import copy
import importlib
import json

from .errors import ArgumentError, StorageError

RESTORATION_RULE = "enrichment_request_restoration@1"


def _portable(value):
    """Treat serialized lists and the original argument's tuples identically."""
    return json.loads(json.dumps(value))


def _at(record, path):
    value = record
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _historical(enricher, records):
    if enricher.option_kind == "flag":
        return True, []
    if enricher.option == "europepmc":
        kinds = {record.get("data") for record in records}
        if len(kinds) != 1:
            raise ValueError(
                "Bibliography and located annotations require separate requests"
            )
        if "located_accession_annotations" in kinds:
            if any(not record.get("article_ids") for record in records):
                raise ValueError("Located annotations have no recorded article_ids")
            articles = []
            for record in records:
                ids = record["article_ids"]
                articles.extend([ids] if isinstance(ids, str) else ids)
            return {"article_ids": list(dict.fromkeys(articles))}, []
    options, unrecorded = {}, []
    for argument, path in enricher.historical_parameters.items():
        values = [
            _portable(value) for r in records if (value := _at(r, path)) is not None
        ]
        if not values:
            unrecorded.append(argument)
        elif any(value != values[0] for value in values[1:]):
            raise ValueError(f"Conflicting recorded values for {argument}")
        else:
            options[argument] = values[0]
    return options, sorted(unrecorded)


def _restore(enricher, records):
    values = [
        _portable(r["request_options"]) for r in records if "request_options" in r
    ]
    if values:
        if any(value != values[0] for value in values[1:]):
            raise ValueError("Conflicting recorded request_options")
        value = values[0]
        if len(values) != len(records):
            # Missing records cannot establish that their requests were identical.
            historical, missing = _historical(
                enricher, [r for r in records if "request_options" not in r]
            )
            if isinstance(value, dict) and isinstance(historical, dict):
                if any(value.get(k) != v for k, v in historical.items()):
                    raise ValueError(
                        "Historical parameters contradict recorded request_options"
                    )
            elif value != historical:
                raise ValueError("Historical flags contradict recorded request_options")
            basis = "partially_recorded_request"
        else:
            missing, basis = [], "recorded_request_options"
    else:
        value, missing = _historical(enricher, records)
        basis = (
            "historical_flag"
            if enricher.option_kind == "flag"
            else "historical_parameters"
        )
    module = importlib.import_module(
        f"sabueso._private.argdigest.argument.{enricher.option}"
    )
    value = getattr(module, f"digest_{enricher.option}")(value)
    if value is False or not enricher.requested(value):
        raise ValueError("The recorded value does not request this enrichment")
    if enricher.option == "europepmc":
        expected = "located_accession_annotations" if "article_ids" in value else None
        if any(r.get("data") != expected for r in records):
            raise ValueError("Recorded options contradict the Europe PMC request route")
    return value, basis, missing


def restoration_plan(card):
    """Return options and inspectable restoration rows; perform no source access."""
    from sabueso.enrichers import ENRICHERS, Enricher

    selectors = {(e.source, kind): e for e in ENRICHERS for kind in e.record_kinds}
    # Bespoke protein routes keep their distinct acquisition and aggregation code.
    for source, option, parameters in (
        ("ChEMBL", "chembl", {"limit": "limit"}),
        ("BindingDB", "bindingdb", {"cutoff": "cutoff", "limit": "limit"}),
        ("PubChem BioAssay", "pubchem_bioassay", {"limit": "limit"}),
    ):
        route = Enricher()
        route.source, route.option = source, option
        route.option_kind, route.historical_parameters = "options", parameters
        selectors[(source, None)] = route
    groups = {}
    for index, record in enumerate(card.quality.get("enrichments") or []):
        selector = record.get("source"), record.get("data")
        enricher = selectors.get(selector)
        key = enricher.option if enricher else selector
        groups.setdefault(key, []).append((index, record))
    options, report = {}, []
    for group in groups.values():
        indices, records = zip(*group)
        first = records[0]
        source, kind = first.get("source"), first.get("data")
        enricher = selectors.get((source, kind))
        row = {
            "source": source,
            "data": kind,
            "option": enricher.option if enricher else None,
            "record_indices": list(indices),
            "original_statuses": [r.get("status") for r in records],
            "status": "restored",
            "basis": "",
            "unrecorded_parameters": [],
            "detail": "Refresh is a new acquisition; saved options do not freeze client defaults or source identifiers",
        }
        if source == "RCSB PDB" and kind is None:
            structures = [r.get("structure") for r in records]
            row["option"], row["basis"] = "structures", "recorded_structure_ids"
            values = [
                _portable(r["request_options"])
                for r in records
                if "request_options" in r
            ]
            if values:
                from sabueso._private.argdigest.argument.structures import (
                    digest_structures,
                )

                try:
                    if any(value != values[0] for value in values[1:]):
                        raise ValueError("Conflicting recorded structure requests")
                    value = digest_structures(values[0])
                    if value != "all" and any(
                        r.get("structure") and r["structure"] not in value
                        for r in records
                    ):
                        raise ValueError(
                            "Structure ids contradict recorded request_options"
                        )
                    options["structures"] = value
                except (ValueError, TypeError, ArgumentError) as exc:
                    row.update(status="requires_override", detail=str(exc))
                else:
                    row["basis"] = (
                        "recorded_request_options"
                        if len(values) == len(records)
                        else "partially_recorded_request"
                    )
                    if len(values) != len(records):
                        row["unrecorded_parameters"] = ["structures"]
            elif all(structures):
                options["structures"] = sorted(set(structures))
            else:
                row["status"], row["detail"] = (
                    "requires_override",
                    "No structure ids were recorded",
                )
        elif source == "ChEMBL" and kind == "assays named by PubChem copies":
            row.update(
                status="dependent_request",
                option="pubchem_bioassay",
                basis="source_stated_copy_pointer",
                detail="Reacquired only through the newly requested PubChem copies",
            )
        elif enricher is None:
            row.update(
                status="unsupported",
                basis="no_declared_route",
                detail="No refresh route is declared for this source/data selector; the original pin retains its record",
            )
        else:
            try:
                value, basis, missing = _restore(enricher, records)
            except (ValueError, TypeError, ArgumentError) as exc:
                row.update(
                    status="requires_override",
                    basis="unrestorable_request",
                    detail=str(exc),
                )
            else:
                options[enricher.option] = value
                row.update(basis=basis, unrecorded_parameters=missing)
        report.append(row)
    profile = (card.quality.get("terms_profile") or {}).get("profile")
    if profile is not None:
        options["terms"] = profile
    decision = (card.quality.get("entity_resolution") or {}).get("decision") or {}
    if any(s.get("name") == "NCBI Gene" for s in decision.get("sources") or []):
        options["ncbi_gene"] = True
    return copy.deepcopy(options), report


def apply_overrides(report, options):
    """Require an explicit choice for conflicting or missing request parameters."""
    for row in report:
        if row["option"] in options:
            row["status"] = "overridden"
        elif row["status"] == "requires_override":
            raise StorageError(
                f"Cannot restore {row['source']} ({row['option']}): {row['detail']}. "
                f"Pass {row['option']} explicitly to refresh_card."
            )
