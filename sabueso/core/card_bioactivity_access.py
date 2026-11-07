"""Captured live activity, group and original-record access without acquisition."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry, _handle
from .card_bioactivity_selection_v1 import (
    COLUMNS,
    COUNTS,
    DEFAULT_FIELDS,
    QUANTITY_FIELD,
    item_ref,
)
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json

TOPIC = "bioactivities"
ADAPTER = "bioactivity_exploration@1"
SUPPORT_FORMAT = "bioactivity_support_membership@1"
SCOPE = "Retained target measurements under explicit classification and grouping policies; not efficacy, selectivity or independent experiments."
DEFAULT_OPTIONS = {
    "include_indirect": False,
    "thresholds": None,
    "classification_rule": "bioactivity_class@4",
    "measurement_rule": "measurement_identity@1",
    "target_scope_rule": "bioactivity_target_scope@1",
    "molecule_ref": None,
    "measurement_ref": None,
}


def descriptor():
    return {
        "key": TOPIC,
        "label": "Measured molecules, assays and original records",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {
                "type": "quantity|null"
                if key == "measurement"
                else "integer|null"
                if key in COUNTS
                else "string|null"
            }
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": deepcopy(DEFAULT_OPTIONS),
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "bioactivity_access_selection@1",
        "quantity_expectations": {
            "measurement": {"field": QUANTITY_FIELD, "units": ["nanomolar", "percent"]}
        },
        "mandatory_interpretation": [
            "scope",
            "row_grain",
            "rule_names",
            "effective_options",
            "target_assignment",
            "counting_scope",
            "independence_status",
            "citation_support_grain",
            "qualifier_conflicts",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
    }


def options_for_bioactivities(options):
    """Validate existing native policies and exact local focus before any reader."""
    from sabueso._private.argdigest.argument.include_indirect import (
        digest_include_indirect,
    )
    from sabueso._private.argdigest.argument.measurement_ref import (
        digest_measurement_ref,
    )
    from sabueso._private.argdigest.argument.molecule_ref import digest_molecule_ref
    from sabueso._private.argdigest.argument.thresholds import digest_thresholds

    from .bioactivities import resolve_thresholds
    from .bioactivity_class_v4 import classification_rule, thresholds_in_force
    from .bioactivity_target_scope import validate_target_scope_rule
    from .measurement_correspondence import validate_measurement_rule

    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - DEFAULT_OPTIONS.keys():
        raise ArgumentError(
            "bioactivities options require only declared policy and focus keys."
        )
    result = {**DEFAULT_OPTIONS, **options}
    result["include_indirect"] = digest_include_indirect(result["include_indirect"])
    result["classification_rule"] = classification_rule(result["classification_rule"])
    result["measurement_rule"] = validate_measurement_rule(result["measurement_rule"])
    result["target_scope_rule"] = validate_target_scope_rule(
        result["target_scope_rule"]
    )
    thresholds = digest_thresholds(result["thresholds"])
    if result["classification_rule"] == "bioactivity_class@4":
        thresholds_in_force(thresholds)
    result["thresholds"] = (
        None if thresholds is None else resolve_thresholds(thresholds)
    )
    for key, validate in (
        ("molecule_ref", digest_molecule_ref),
        ("measurement_ref", digest_measurement_ref),
    ):
        if result[key] is not None:
            result[key] = validate(result[key])
    try:
        canonical_json(result).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, StorageError) as exc:
        raise ArgumentError(
            "Bioactivity options require finite serializable values."
        ) from exc
    return deepcopy(result)


def _wire(value):
    """Keep every original field; native live quantities become explicit nodes."""
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_wire(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    import pyunitwizard as puw

    if puw.is_quantity(value):
        unit = puw.convert(str(puw.get_unit(value)), to_form="record", to_type="unit")
        number = puw.get_value(value, to_unit=unit)
        return {
            "value": number.tolist() if hasattr(number, "tolist") else number,
            "unit": unit,
        }
    raise TypeError(f"Unsupported native bioactivity value: {type(value).__name__}")


def _native(access, method, *args, **kwargs):
    key = (ADAPTER, "native", access._focal_key, method, canonical_json([args, kwargs]))
    if key not in access._scientific_cache:
        from .card_scientific_access import _CapturedCard

        card_key = (ADAPTER, "captured_card", access._focal_key)
        if card_key not in access._scientific_cache:
            access._scientific_cache[card_key] = _CapturedCard(access._focal)
        card = access._scientific_cache[card_key]
        access._scientific_cache[key] = _wire(getattr(card, method)(*args, **kwargs))
    return access._scientific_cache[key]


def _guard(access):
    if access.profile != "protein":
        return {
            "status": "not_applicable",
            "reason": "The bioactivities adapter requires a protein Card.",
        }
    data = access._focal.data
    identifier = data.get("sections", {}).get("identifiers", {}).get("uniprot", {})
    accession = identifier.get("value") if isinstance(identifier, dict) else None
    expected = (
        "sabueso:protein:uniprot:" + accession if isinstance(accession, str) else None
    )
    if not access._focal.pin or expected != data["meta"].get("card_id"):
        return {
            "status": "missing_prerequisite",
            "reason": "A coherent captured protein identity and canonical UniProt identifier are required; use literal inspection.",
        }
    if any(
        rel.get("predicate") == "has_bioactivity"
        and rel.get("subject_ref") != "uniprot:" + accession
        for rel in data.get("relationship_store", [])
    ):
        return {
            "status": "missing_prerequisite",
            "reason": "Retained activity subjects do not share the captured canonical identity; use original relationship inspection.",
        }
    return None


@dataclass(frozen=True)
class BioactivityResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        """Separate an absent scalar from a column without one value at this grain."""
        row = self.wire["rows"][key]
        if row[column] is not None:
            return "present"
        grain = self.wire["context"]["grain"]
        if grain == "molecule" and column in ("measurement_ref", "relationship_id"):
            return "not_applicable"
        members = (
            row["item"].get("measurements", [])
            if grain == "molecule"
            else row["item"].get("records", [])
            if grain == "group"
            else [row["item"]]
        )
        if (
            column in ("measurement", "relation", "relationship_id")
            and len(members) > 1
        ):
            return "not_applicable"
        context = self.wire["explanations"][key]
        values = []
        if column == "source":
            values = (
                row["item"].get("sources", [])
                if grain == "molecule"
                else (row["item"].get("identity") or {}).get("sources", [])
                if grain == "group"
                else []
            )
        elif column == "assay_ref":
            values = [
                (record.get("assay") or {}).get("id")
                for record in context["assay_context"]
            ]
        elif column == "document_ref":
            for record in context["citation_context"]:
                document = record.get("document") or {}
                values.append(
                    document.get("id")
                    or (
                        "pubmed:" + str(document["pubmed"])
                        if document.get("pubmed")
                        else "doi:" + document["doi"]
                        if document.get("doi")
                        else None
                    )
                )
        if len({value for value in values if value is not None}) > 1:
            return "not_applicable"
        return "unknown"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        if state == "present":
            return None
        if state == "not_applicable":
            if self.wire["context"]["grain"] == "molecule" and column in (
                "measurement_ref",
                "relationship_id",
            ):
                return "Measurement and source-record identifiers belong to more detailed rows."
            return "This row contains multiple original values and has no single value for this column."
        if column == "measurement":
            return "A usable normalized quantity is not stated for the original measurement."
        return "The retained source context does not state a usable scalar value."

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
        cells = {}
        for column in selection._fields:
            value = self.value(entry.key, column)
            if column == "measurement" and value is not None:
                from pyunitwizard import QuantityRecord

                from .quantities import to_quantity

                value = QuantityRecord.from_quantity(
                    to_quantity(value), field=QUANTITY_FIELD, unit=value["unit"]
                ).to_dict()
            cells[column] = {
                "state": self.cell_state(entry.key, column),
                "reason": self.cell_reason(entry.key, column),
                "value": deepcopy(value),
                "field": {"adapter": ADAPTER, "column": column},
                "support_basis": support["basis"],
                "support_ref": entry.key,
                "value_included": True,
                "value_location": access._location(
                    self.location("rows", entry.key, column)
                ),
                "interpretation_location": interpretation,
            }
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": access._focal.pin,
            "location": access._location(entry.location),
            "payload_location": access._location(
                self.location("rows", entry.key, "item")
            ),
            "state": row["interpretation"]["state"],
            "support_location": access._location(self.location("support", entry.key)),
            "support": {
                "ref": entry.key,
                "format": SUPPORT_FORMAT,
                "basis": support["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": record["id"], "state": record["state"]}
                    for record in support["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": cells,
            "value_included": True,
            "inspection_required": False,
        }


def _single(values):
    values = list(values)
    if not values or any(value is None for value in values):
        return None
    values = list(dict.fromkeys(values))
    return values[0] if len(values) == 1 else None


def _location(access, store, identifier):
    return access._card_location(
        segments=[
            {"type": "Key", "value": store},
            {"type": "Record", "value": identifier},
        ]
    )


def _support(access, result, key, relationships, literature):
    ids = sorted(
        {
            identifier
            for rel in relationships
            for identifier in rel.get("source_assertion_ids", [])
        }
    )
    available = {
        row["id"] for row in access._focal.data.get("source_assertion_store", [])
    }
    citations = []
    for rel in relationships:
        document = (rel.get("qualifiers") or {}).get("document") or {}
        ref = (
            "pubmed:" + str(document["pubmed"])
            if document.get("pubmed")
            else "doi:" + document["doi"]
            if document.get("doi")
            else None
        )
        if ref is not None:
            citations.append(ref)
    publications = []
    for index, publication in enumerate(literature.get("publications", [])):
        if publication["publication_ref"] in citations:
            publications.append(
                {
                    **result.location("literature", "publications"),
                    "segments": [
                        *result.location("literature", "publications")["segments"],
                        {"type": "Index", "value": index},
                    ],
                }
            )
    return {
        "format": SUPPORT_FORMAT,
        "basis": "original_activity_and_assay_relationship_support",
        "source_assertion_ids": ids,
        "source_assertions": [
            {
                "id": identifier,
                "state": "present" if identifier in available else "not_retained",
                "location": _location(access, "source_assertion_store", identifier)
                if identifier in available
                else None,
            }
            for identifier in ids
        ],
        "relationship_ids": [rel["id"] for rel in relationships],
        "relationship_locations": [
            _location(access, "relationship_store", rel["id"]) for rel in relationships
        ],
        "source_record_location": result.location("rows", key, "item"),
        "whole_card_context_location": access._card_location(),
        "explanation_location": result.location("explanations", key),
        "context_location": result.location("native_payload", "context")
        if "context" in result.wire.get("native_payload", {})
        else result.location("native_payload", "measurement_identity"),
        "assay_context_location": result.location("explanations", key, "assay_context"),
        "citation_context_location": result.location(
            "explanations", key, "citation_context"
        ),
        "publication_context_locations": publications,
        "citation_support_grain": "Retained citation fields on activity relationships; original activity and assay assertions, not an independently asserted document object.",
    }


def _row(kind, item, measures, molecule=None, group=None, relationship=None):
    measure = measures[0] if len(measures) == 1 else {}
    return {
        "label": (item.get("label") or molecule)
        if kind == "molecule"
        else "Measurement group " + group
        if kind == "group"
        else "Activity "
        + str(
            (relationship.get("qualifiers") or {}).get("activity_id")
            or relationship["id"]
        ),
        "kind": "bioactivity_" + kind,
        "molecule_ref": molecule,
        "measurement_ref": group,
        "relationship_id": relationship["id"]
        if relationship
        else measure.get("relationship_id")
        if kind == "group"
        else None,
        "class": item.get("class") if kind != "record" else measure.get("class"),
        "measurement": deepcopy(measure.get("normalized")),
        "relation": measure.get("relation"),
        "measurement_count": item.get("measurement_count") if kind == "molecule" else 1,
        "record_count": item.get("record_count")
        if kind == "molecule"
        else len(item.get("records", []))
        if kind == "group"
        else 1,
        "source": _single(measurement.get("source") for measurement in measures),
        "assay_ref": _single(measurement.get("assay") for measurement in measures),
        "document_ref": _single(
            measurement.get("document") for measurement in measures
        ),
        "item": deepcopy(item),
    }


def _outcome(rows, coverage, native):
    states = {row["state"] for row in coverage.get("rows", [])}
    if rows:
        return {
            "status": "partial"
            if states & {"partial", "unavailable"} or native.get("gaps")
            else "ok",
            "reason": "Some original support or source/request coverage remains incomplete."
            if states & {"partial", "unavailable"} or native.get("gaps")
            else None,
        }
    status = (
        "partial"
        if "partial" in states
        else "unavailable"
        if "unavailable" in states
        else "empty"
        if states & {"known", "not_stated", "conflicting"}
        else "not_queried"
    )
    return {
        "status": status,
        "reason": "No retained included rows under these options; inspect original source coverage and exclusions. This is not global absence or inactivity.",
    }


def materialize(access, options=None):
    """Share one detached evaluation of each exact native request across surfaces."""
    if access.mode != "live":
        raise ArgumentError("Bioactivity original saved reading is not implemented.")
    options = options_for_bioactivities(options)
    cache_key = (ADAPTER, access._focal_key, canonical_json(options))
    if cache_key in access._scientific_cache:
        return access._scientific_cache[cache_key]
    grain = (
        "record"
        if options["measurement_ref"]
        else "group"
        if options["molecule_ref"]
        else "molecule"
    )
    unavailable = _guard(access)
    native, root, originals, rows, literature = {}, {}, {}, {}, {}
    focus_membership = None
    coverage = {
        "basis": "not_evaluated",
        "rows": [],
        "quality_location": access._card_location(
            segments=[{"type": "Key", "value": "quality"}]
        ),
    }
    if unavailable is None:
        policies = {
            key: value
            for key, value in options.items()
            if key not in ("molecule_ref", "measurement_ref")
        }
        if grain == "molecule":
            native = _native(access, "bioactivities", **policies)
            root = native
        else:
            parent = materialize(
                access, {**policies, "molecule_ref": None, "measurement_ref": None}
            )
            root = parent.wire["native_payload"]
            matching = [
                item
                for item in root["items"]
                if options["molecule_ref"] is None
                or item["molecule_ref"] == options["molecule_ref"]
            ]
            if not matching:
                raise ArgumentError(
                    "molecule_ref is outside this captured bioactivity result."
                )
            if grain == "group":
                native = _native(
                    access, "explain_bioactivity", options["molecule_ref"], **policies
                )
            else:
                if not any(
                    measurement["group"] == options["measurement_ref"]
                    or measurement["relationship_id"] == options["measurement_ref"]
                    for item in matching
                    for measurement in item["measurements"]
                ):
                    raise ArgumentError(
                        "measurement_ref is outside the selected molecule/result; foreign focus is refused."
                    )
                native = _native(
                    access,
                    "explain_measurement",
                    options["measurement_ref"],
                    measurement_rule=options["measurement_rule"],
                )
        knowledge = _native(access, "knowledge_state")
        coverage = {
            **coverage,
            "basis": "original_scoped_knowledge_state",
            "rule": knowledge["rule"],
            "rows": [
                row
                for row in knowledge["rows"]
                if row["area"].startswith("relationships.has_bioactivity")
            ],
            "scope_note": "Retained source/request outcomes, including unqueried, failed, partial and excluded contexts; never global source absence.",
        }
        literature = _native(access, "literature")
        originals = {
            rel["id"]: rel for rel in access._focal.data.get("relationship_store", [])
        }
        projected = {
            measurement["relationship_id"]: measurement
            for item in root["items"]
            for measurement in item["measurements"]
        }
        if grain == "molecule":
            for item in native["items"]:
                key = item["molecule_ref"]
                rows[key] = _row(grain, item, item["measurements"], molecule=key)
        elif grain == "group":
            for index, group in enumerate(native["groups"]):
                base = group["group"]
                key = base if base not in rows else f"{base}:occurrence:{index}"
                members = [
                    projected[ref] for ref in group["records"] if ref in projected
                ]
                rows[key] = _row(
                    grain, group, members, molecule=options["molecule_ref"], group=base
                )
        else:
            original_members = [
                record["relationship"]["id"] for record in native["records"]
            ]
            admitted = {
                measurement["relationship_id"]
                for item in matching
                for measurement in item["measurements"]
                if measurement["relationship_id"] in original_members
            }
            focus_membership = {
                "included_relationship_ids": [
                    ref for ref in original_members if ref in admitted
                ],
                "context_only_relationship_ids": [
                    ref for ref in original_members if ref not in admitted
                ],
                "basis": "Exact original group membership intersected with the selected molecule and retained inclusion policy; broader native group records remain context, not included rows.",
            }
            for record in native["records"]:
                rel = record["relationship"]
                if rel["id"] not in admitted:
                    continue
                measurement = projected[rel["id"]]
                rows[rel["id"]] = _row(
                    grain,
                    record,
                    [measurement],
                    molecule=rel["object_ref"],
                    group=native["group"]["id"],
                    relationship=rel,
                )
    ref = _handle(
        "XR_",
        {
            "format": "bioactivity_exploration_result@1",
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "options": options,
            "native": native,
            "coverage": coverage,
            "unavailable": unavailable,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "grain": grain,
            "options": deepcopy(options),
            "used_captures": [access._focal_key],
            "original_card_location": access._card_location(),
            "quality_location": coverage["quality_location"],
        },
        "native_payload": native,
        "rows": rows,
        "support": {},
        "explanations": {},
        "coverage": coverage,
        "exclusions": deepcopy(root.get("excluded", [])),
        "literature": literature,
        "scope": SCOPE,
        "schema": {
            key: value
            for key, value in descriptor().items()
            if key not in ("save", "save_reason")
        },
        "outcome": unavailable or _outcome(rows, coverage, native),
    }
    if focus_membership is not None:
        wire["context"]["focus_membership"] = focus_membership
    shell = BioactivityResult(ref, wire, (), deepcopy(options))
    for key, row in rows.items():
        ids = (
            [
                measurement["relationship_id"]
                for measurement in row["item"]["measurements"]
            ]
            if grain == "molecule"
            else row["item"]["records"]
            if grain == "group"
            else [row["relationship_id"]]
        )
        relationships = [
            originals[identifier] for identifier in ids if identifier in originals
        ]
        support = _support(access, shell, key, relationships, literature)
        wire["support"][key] = support
        row["interpretation"] = {
            "scope": SCOPE,
            "row_grain": grain,
            "rule_names": [
                options[name]
                for name in (
                    "classification_rule",
                    "measurement_rule",
                    "target_scope_rule",
                )
            ],
            "effective_options": deepcopy(options),
            "state": "support_unknown"
            if any(
                record["state"] != "present" for record in support["source_assertions"]
            )
            or not support["source_assertions"]
            else "present",
            "target_assignment": deepcopy(root.get("scope")),
            "classification": deepcopy(root.get("classification")),
            "counting_scope": "Native molecule/group/source-record counts under the selected policy; not independent experiments.",
            "independence_status": "not_established",
            "citation_support_grain": support["citation_support_grain"],
            "qualifier_conflicts": [
                {
                    "relationship_id": rel["id"],
                    "conflicts": deepcopy(rel["qualifier_conflicts"]),
                }
                for rel in relationships
                if rel.get("qualifier_conflicts")
            ],
            "context_location": support["context_location"],
            "exclusions_location": shell.location("exclusions"),
        }
        wire["explanations"][key] = {
            "original_item": deepcopy(row["item"]),
            "support_location": shell.location("support", key),
            "context_location": support["context_location"],
            "assay_context": [
                {
                    "relationship_id": rel["id"],
                    "assay": deepcopy((rel.get("qualifiers") or {}).get("assay")),
                    "qualifier_conflicts": deepcopy(rel.get("qualifier_conflicts")),
                }
                for rel in relationships
            ],
            "citation_context": [
                {
                    "relationship_id": rel["id"],
                    "document": deepcopy((rel.get("qualifiers") or {}).get("document")),
                    "support_grain": support["citation_support_grain"],
                }
                for rel in relationships
            ],
            "quality_location": coverage["quality_location"],
        }
    if rows and any(
        row["interpretation"]["state"] == "support_unknown" for row in rows.values()
    ):
        wire["outcome"] = {
            "status": "partial",
            "reason": "Some original source support is not retained; original values and classes remain unchanged.",
        }
    result = BioactivityResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
        deepcopy(options),
    )
    access._objects[ref] = wire
    access._scientific_cache[cache_key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Defer value, interpretation and support together, preserving read paths."""
    deferred = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    deferred.update(
        cells={
            key: {
                name: deepcopy(value) for name, value in cell.items() if name != "value"
            }
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return deferred
