"""Source-stated molecule joins into explicitly supplied protein captures."""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field

from .card_access import _Entry, _handle
from .card_bioactivity_access import (
    DEFAULT_OPTIONS as BIO_OPTIONS,
)
from .card_bioactivity_access import (
    _native,
    _wire,
    options_for_bioactivities,
)
from .card_bioactivity_access import (
    materialize as bioactivity,
)
from .card_molecule_activity_selection_v1 import (
    COLUMNS,
    COUNTS,
    DEFAULT_FIELDS,
    FORMAT,
    QUANTITY_FIELD,
    item_ref,
)
from .errors import ArgumentError
from .relationship_store import make_derivation
from .snapshot import canonical_json

TOPIC = "activity_context"
ADAPTER = "molecule_activity_context_exploration@1"
SUPPORT_FORMAT = "molecule_activity_context_support@1"
RULE = "molecule_activity_context@1"
SCOPE = (
    "Exact source-stated molecule identity within explicitly supplied target pins; "
    "retained measurements and source/query scope, not target discovery, inactivity, "
    "efficacy, selectivity or independent experiments."
)
DEFAULT_OPTIONS = {**BIO_OPTIONS, "target_card_ref": None}


def descriptor():
    return {
        "key": TOPIC,
        "label": "Targets, measurements and assay context",
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
        "selection_policy": FORMAT,
        "quantity_expectations": {
            "measurement": {"field": QUANTITY_FIELD, "units": ["nanomolar", "percent"]}
        },
        "mandatory_interpretation": [
            "rule",
            "scope",
            "row_grain",
            "effective_options",
            "identity_basis",
            "target_card_ref",
            "native_outcomes",
            "counting_scope",
            "independence_status",
        ],
        "source_support": {"format": SUPPORT_FORMAT},
        "save": False,
        "save_reason": "A clean LIVE producer and genuine original must precede independent saved reading for this new molecule-target interpretation.",
    }


def options_for_activity_context(options):
    from sabueso._private.argdigest.argument.target_card_ref import (
        digest_target_card_ref,
    )

    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - DEFAULT_OPTIONS.keys():
        raise ArgumentError(
            "activity_context options require only declared policy and focus keys."
        )
    target = digest_target_card_ref(options.get("target_card_ref"))
    result = options_for_bioactivities(
        {key: value for key, value in options.items() if key != "target_card_ref"}
    )
    result["target_card_ref"] = target
    if result["measurement_ref"] is not None and target is None:
        raise ArgumentError(
            "measurement_ref requires an exact captured target_card_ref."
        )
    return result


def _anchor(capture):
    meta = capture.data.get("meta", {})
    identifier = meta.get("card_id")
    prefix = "sabueso:small_molecule:inchikey:"
    if (
        meta.get("entity_type") != "small_molecule"
        or not isinstance(identifier, str)
        or not identifier.startswith(prefix)
    ):
        return None
    anchor = identifier.split(":", 2)[2]
    value = capture.data.get("sections", {}).get("identifiers", {}).get("inchikey")
    value = value.get("value") if isinstance(value, dict) else value
    if value is not None and value != anchor.split(":", 1)[1]:
        return None
    return anchor


def _identity(access):
    edges, focal_edges, by_record = [], [], {}
    for capture_key, capture in sorted(access._captures.items()):
        if capture.data.get("meta", {}).get("entity_type") != "small_molecule":
            continue
        anchor = _anchor(capture)
        local = access._for_capture(capture_key)
        assertions = {
            row["id"] for row in capture.data.get("source_assertion_store", [])
        }
        for rel in sorted(
            capture.data.get("relationship_store", []), key=lambda row: row["id"]
        ):
            if rel.get("predicate") != "same_as":
                continue
            ids = list(rel.get("source_assertion_ids") or [])
            edge = {
                "molecule_card_ref": capture.pin,
                "anchor": anchor,
                "record_ref": rel["subject_ref"],
                "object_ref": rel["object_ref"],
                "targets_own_anchor": anchor is not None
                and rel["object_ref"] == anchor,
                "relationship_id": rel["id"],
                "relationship_location": local._card_location(
                    segments=[
                        {"type": "Key", "value": "relationship_store"},
                        {"type": "Record", "value": rel["id"]},
                    ]
                ),
                "source_assertions": [
                    {
                        "id": identifier,
                        "state": "present"
                        if identifier in assertions
                        else "not_retained",
                        "location": local._card_location(
                            segments=[
                                {"type": "Key", "value": "source_assertion_store"},
                                {"type": "Record", "value": identifier},
                            ]
                        )
                        if identifier in assertions
                        else None,
                    }
                    for identifier in ids
                ],
            }
            edges.append(edge)
            by_record.setdefault(rel["subject_ref"], set()).add(rel["object_ref"])
            if capture_key == access._focal_key:
                focal_edges.append(edge)
    aliases = sorted(
        {edge["record_ref"] for edge in focal_edges if edge["targets_own_anchor"]}
    )
    conflicts = {
        ref: [deepcopy(edge) for edge in edges if edge["record_ref"] == ref]
        for ref in aliases
        if len(by_record[ref]) > 1
    }
    return {
        "basis": "Explicit same_as relationships whose object is the focal molecule anchor; no similarity or name join.",
        "anchor": _anchor(access._focal),
        "focal_edges": focal_edges,
        "all_supplied_identity_edges": edges,
        "admitted_molecule_refs": aliases,
        "conflicting_record_anchors": conflicts,
        "input_occurrences": list(access._inputs),
        "input_multiplicity": dict(Counter(access._inputs)),
    }


def _guard(access, identity):
    if access.profile != "small_molecule":
        return {
            "status": "not_applicable",
            "reason": "activity_context requires a captured small-molecule Card.",
        }
    if identity["anchor"] is None or access._focal.pin is None:
        return {
            "status": "missing_prerequisite",
            "reason": "A coherent captured chemical anchor is required before a molecule-target identity join.",
        }
    if not identity["admitted_molecule_refs"]:
        return {
            "status": "missing_prerequisite",
            "reason": "No explicit same_as identity join to this molecule anchor is retained; names never establish activity correspondence.",
        }
    if identity["conflicting_record_anchors"]:
        return {
            "status": "missing_prerequisite",
            "reason": "Supplied source records explicitly name conflicting chemical anchors; no merged activity interpretation was performed. Inspect the original identity edges.",
        }
    return None


@dataclass(frozen=True)
class MoleculeActivityResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict
    _access: object = field(repr=False)
    _members: dict = field(repr=False)

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

    def native_members(self, key):
        return tuple(self._members[key])

    def native_member(self, key):
        members = self.native_members(key)
        if len(members) != 1:
            raise ArgumentError(
                "This aggregate row has multiple original native members; inspect native_members."
            )
        return members[0]

    def target_access(self, pin):
        return self._access._for_capture(pin)

    def cell_state(self, key, column):
        if self.value(key, column) is not None:
            return "present"
        members = self.native_members(key)
        if (
            column in ("molecule_ref", "measurement_ref", "relationship_id")
            and len(members) != 1
        ):
            return "not_applicable"
        if column in (
            "class",
            "measurement",
            "relation",
            "source",
            "assay_ref",
            "document_ref",
        ):
            if len(members) > 1:
                return "not_applicable"
            if len(members) == 1:
                _, result, entry = members[0]
                return result.cell_state(entry.key, column)
            if self.value(key, "record_count") == 0:
                return "not_applicable"
        return "not_evaluated" if not members else "unknown"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        return (
            None
            if state == "present"
            else (
                "This aggregate has no single original scalar at this grain."
                if state == "not_applicable"
                else "No matching native activity member was evaluated in this supplied context; inspect source/query and identity scope."
                if state == "not_evaluated"
                else "The original source does not state a usable scalar value."
            )
        )

    def frame(self, access, selection, entry):
        from pyunitwizard import QuantityRecord

        from .quantities import to_quantity

        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
        cells = {}
        for column in selection._fields:
            value = self.value(entry.key, column)
            if column == "measurement" and value is not None:
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
                "source_assertions": deepcopy(support["source_assertions"]),
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": cells,
            "value_included": True,
            "inspection_required": False,
        }

    def native_crossing(self, pin):
        """Evaluate an explicitly requested native crossing once on detached inputs."""
        from .card_scientific_access import _CapturedCard
        from .deck import Deck
        from .ligand_explanation import explain_ligand
        from .quantities import to_quantity

        access, policies = self.target_access(pin), _policies(self.options)
        cache_key = (
            ADAPTER,
            "native_crossing",
            pin,
            tuple(self._access._inputs),
            canonical_json(policies),
        )
        cache = self._access._scientific_cache
        if cache_key not in cache:

            class TargetInput:
                def __init__(self):
                    self.card = _CapturedCard(access._focal)

                def __getattr__(self, name):
                    return getattr(self.card, name)

                def bioactivities(self, **kwargs):
                    original = deepcopy(_native(access, "bioactivities", **kwargs))
                    for molecule in original["items"]:
                        for measurement in molecule["measurements"]:
                            if measurement.get("normalized") is not None:
                                measurement["normalized"] = to_quantity(
                                    measurement["normalized"]
                                )
                    return original

            cards = [
                _CapturedCard(self._access._captures[key])._card
                for key in self._access._inputs
                if self._access._captures[key].data["meta"].get("entity_type")
                == "small_molecule"
            ]
            native = _wire(
                explain_ligand(
                    TargetInput(),
                    self._access._focal.data["meta"]["card_id"],
                    Deck(cards),
                    **policies,
                )
            )
            wrapper = {
                "native_payload": native,
                "molecule_card_ref": self._access._focal.pin,
                "target_card_ref": pin,
                "structural_flag_limit": "Grouped False/None investigation flags retain an existing ordering limitation; original structure occurrences remain authoritative source context.",
            }
            _, location = self._access._resolve(self._access._object_location(wrapper))
            cache[cache_key] = (
                native,
                {
                    **location,
                    "segments": [
                        *location["segments"],
                        {"type": "Key", "value": "native_payload"},
                    ],
                },
            )
        return cache[cache_key]


def _policies(options):
    return {
        key: value
        for key, value in options.items()
        if key not in ("target_card_ref", "molecule_ref", "measurement_ref")
    }


def _counts(members):
    groups, records = set(), set()
    for _, result, entry in members:
        row = entry.value
        if result.wire["context"]["grain"] == "molecule":
            for measurement in row["item"]["measurements"]:
                groups.add(measurement["group"])
                records.add(measurement["relationship_id"])
        elif result.wire["context"]["grain"] == "group":
            groups.add(row["measurement_ref"])
            records.update(row["item"]["records"])
        else:
            groups.add(row["measurement_ref"])
            records.add(row["relationship_id"])
    return len(groups), len(records)


def _unique_locations(locations):
    return list({canonical_json(location): location for location in locations}.values())


def materialize(access, options=None):
    """Share the complete retained native context without changing scientific rules."""
    if access.mode != "live":
        raise ArgumentError(
            "This new molecule activity-context interpretation is not available in saved mode."
        )
    options = options_for_activity_context(options)
    cache_key = (
        ADAPTER,
        access._focal_key,
        tuple(access._inputs),
        canonical_json(options),
    )
    if cache_key in access._scientific_cache:
        return access._scientific_cache[cache_key]
    identity = _identity(access)
    unavailable = _guard(access, identity)
    pin = options["target_card_ref"]
    if pin is not None and pin not in access._captures:
        raise ArgumentError(
            "target_card_ref is outside the explicitly supplied captures; supply that exact Card state first."
        )
    aliases = identity["admitted_molecule_refs"]
    if options["molecule_ref"] is not None:
        if options["molecule_ref"] not in aliases:
            raise ArgumentError(
                "molecule_ref is not an explicit identity member of the focal molecule."
            )
        aliases = [options["molecule_ref"]]
    grain = (
        "record"
        if options["measurement_ref"] is not None
        else "group"
        if pin is not None
        else "target"
    )
    target_keys = (
        [pin]
        if pin is not None
        else sorted(
            key
            for key, capture in access._captures.items()
            if key != access._focal_key
            and capture.data["meta"].get("entity_type") == "protein"
            and capture.pin is not None
        )
    )
    if (
        unavailable is None
        and pin is not None
        and access._captures[pin].data["meta"].get("entity_type") != "protein"
    ):
        unavailable = {
            "status": "not_applicable",
            "reason": "The explicitly selected capture has no protein target capability; no activity interpretation was evaluated.",
        }
    if unavailable is None and not target_keys:
        unsupported = any(
            key != access._focal_key for key in access._captures
        ) and not any(
            capture.data["meta"].get("entity_type") == "protein"
            for key, capture in access._captures.items()
            if key != access._focal_key
        )
        unavailable = {
            "status": "unsupported" if unsupported else "missing_prerequisite",
            "reason": "No supplied captured protein context is available; this is not a statement about biological targets or activity.",
        }
    targets, rows, members, coverage_rows, exclusions = {}, {}, {}, [], []
    outcomes = []
    if unavailable is None:
        for target_key in target_keys:
            target_access = access._for_capture(target_key)
            root = bioactivity(target_access, _policies(options))
            targets[target_key] = {
                "overview": {"result_ref": root.result_ref, "wire": root.wire},
                "focused_results": {},
            }
            outcomes.append(deepcopy(root.wire["outcome"]))
            coverage_rows.extend(
                {**deepcopy(row), "target_card_ref": target_key}
                for row in root.wire["coverage"].get("rows", [])
            )
            exclusions.extend(
                {"target_card_ref": target_key, "original": deepcopy(row)}
                for row in root.wire["exclusions"]
            )
            matching = [
                entry
                for entry in root.entries
                if entry.value["molecule_ref"] in aliases
            ]
            if grain == "target":
                key = _handle("MC_", [target_key])
                members[key] = [(target_access, root, entry) for entry in matching]
                rows[key] = {"target_card_ref": target_key}
            else:
                for molecule in matching:
                    alias = molecule.value["molecule_ref"]
                    reference = options["measurement_ref"]
                    if reference is not None and not any(
                        reference in (item["group"], item["relationship_id"])
                        for item in molecule.value["item"]["measurements"]
                    ):
                        continue
                    focused = bioactivity(
                        target_access,
                        {
                            **_policies(options),
                            "molecule_ref": alias,
                            "measurement_ref": reference,
                        },
                    )
                    targets[target_key]["focused_results"][focused.result_ref] = (
                        focused.wire
                    )
                    for entry in focused.entries:
                        original_key = (
                            entry.value["relationship_id"]
                            if grain == "record"
                            else entry.value["measurement_ref"]
                        )
                        key = _handle("MC_", [target_key, grain, original_key])
                        rows.setdefault(key, {"target_card_ref": target_key})
                        members.setdefault(key, []).append(
                            (target_access, focused, entry)
                        )
        if options["measurement_ref"] is not None and not rows:
            raise ArgumentError(
                "measurement_ref is outside the exact joined molecule/target membership."
            )
    rule = make_derivation(RULE, inputs=list(access._inputs), parameters=options)
    native = {
        "rule": rule,
        "identity": identity,
        "targets": targets,
        "unsupported_inputs": [
            {"capture": key, "profile": capture.data["meta"].get("entity_type")}
            for key, capture in access._captures.items()
            if key != access._focal_key
            and capture.data["meta"].get("entity_type") != "protein"
        ],
    }
    ref = _handle(
        "XR_",
        {
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "options": options,
            "native": native,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "grain": grain,
            "options": deepcopy(options),
            "molecule_card_ref": access._focal.pin,
            "target_card_ref": pin,
            "used_captures": list(dict.fromkeys(access._inputs)),
            "quality_location": access._card_location(
                segments=[{"type": "Key", "value": "quality"}]
            ),
        },
        "native_payload": native,
        "rows": rows,
        "support": {},
        "explanations": {},
        "coverage": {
            "basis": "original_supplied_target_query_scope",
            "rows": coverage_rows,
            "scope_note": SCOPE,
            "target_outcomes": outcomes,
        },
        "exclusions": exclusions,
        "scope": SCOPE,
        "schema": {
            key: value
            for key, value in descriptor().items()
            if key not in ("save", "save_reason")
        },
        "outcome": unavailable,
    }
    shell = MoleculeActivityResult(ref, wire, (), deepcopy(options), access, members)
    for key, row in rows.items():
        originals = members[key]
        source_rows = [entry.value for _, _, entry in originals]
        molecule_refs = sorted({value["molecule_ref"] for value in source_rows})
        row.update({column: None for column in COLUMNS if column not in row})
        row.update(
            kind="activity_context_" + grain,
            molecule_card_ref=access._focal.pin,
            molecule_refs=molecule_refs,
            target_ref=access._captures[row["target_card_ref"]]
            .data["meta"]
            .get("card_id", "")
            .split(":", 2)[-1],
            label="Supplied target · " + row["target_card_ref"]
            if grain == "target"
            else source_rows[0]["label"],
            item=deepcopy(source_rows[0]["item"])
            if len(source_rows) == 1
            else {"native_members": [deepcopy(value["item"]) for value in source_rows]},
        )
        if len(source_rows) == 1:
            for column in COLUMNS:
                if column not in (
                    "kind",
                    "label",
                    "target_card_ref",
                    "target_ref",
                    "molecule_card_ref",
                ):
                    row[column] = deepcopy(source_rows[0][column])
        if grain == "group":
            row["measurement_ref"] = source_rows[0]["measurement_ref"]
        if originals:
            row["measurement_count"], row["record_count"] = _counts(originals)
        elif targets[row["target_card_ref"]]["overview"]["wire"]["outcome"][
            "status"
        ] in ("ok", "empty", "partial"):
            row["measurement_count"], row["record_count"] = 0, 0
        edges = [
            edge
            for edge in identity["focal_edges"]
            if edge["targets_own_anchor"]
            and (not molecule_refs or edge["record_ref"] in molecule_refs)
        ]
        assertions = [
            deepcopy(statement)
            for edge in edges
            for statement in edge["source_assertions"]
        ]
        relationships = [edge["relationship_location"] for edge in edges]
        native_supports = []
        for _, original, entry in originals:
            support = original.wire["support"][entry.key]
            assertions.extend(deepcopy(support["source_assertions"]))
            relationships.extend(deepcopy(support["relationship_locations"]))
            native_supports.append(
                {
                    "molecule_ref": entry.value["molecule_ref"],
                    "result_ref": original.result_ref,
                    "row_key": entry.key,
                    "support": deepcopy(support),
                }
            )
        assertions = list(
            {canonical_json(statement): statement for statement in assertions}.values()
        )
        support_unknown = (
            not edges
            or any(not edge["source_assertions"] for edge in edges)
            or any(statement["state"] != "present" for statement in assertions)
        )
        wire["support"][key] = {
            "format": SUPPORT_FORMAT,
            "basis": "Explicit original identity edges and exact target-native activity membership",
            "identity_edges": deepcopy(edges),
            "native_supports": native_supports,
            "source_assertions": assertions,
            "relationship_locations": _unique_locations(relationships),
            "whole_card_context_location": access._card_location(),
            "target_card_location": access._for_capture(
                row["target_card_ref"]
            )._card_location(),
        }
        row["interpretation"] = {
            "rule": deepcopy(rule),
            "scope": SCOPE,
            "row_grain": grain,
            "effective_options": deepcopy(options),
            "identity_basis": identity["basis"],
            "target_card_ref": row["target_card_ref"],
            "state": "support_unknown"
            if support_unknown
            else "present"
            if originals
            else "empty"
            if row["record_count"] == 0
            else "not_evaluated",
            "native_outcomes": [
                deepcopy(targets[row["target_card_ref"]]["overview"]["wire"]["outcome"])
            ],
            "counting_scope": "Distinct native group IDs and source relationship IDs within each exact supplied target pin; alias/input occurrences remain explicit, not independent experiments.",
            "independence_status": "not_established",
            "native_interpretations": [
                deepcopy(value["interpretation"]) for value in source_rows
            ],
        }
        wire["explanations"][key] = {
            "original_items": [deepcopy(value["item"]) for value in source_rows],
            "identity_edges": deepcopy(edges),
            "native_explanations": [
                deepcopy(original.wire["explanations"][entry.key])
                for _, original, entry in originals
            ],
            "support_location": shell.location("support", key),
            "interpretation": deepcopy(row["interpretation"]),
        }
    if unavailable is None:
        statuses = {outcome["status"] for outcome in outcomes}
        matched = any(members.values())
        partial = any(
            row["interpretation"]["state"] == "support_unknown" for row in rows.values()
        )
        status = (
            "partial"
            if partial
            or "partial" in statuses
            or (matched and "unavailable" in statuses)
            else "ok"
            if matched
            else "unavailable"
            if "unavailable" in statuses
            else "not_queried"
            if statuses == {"not_queried"}
            else "missing_prerequisite"
            if "missing_prerequisite" in statuses or "not_applicable" in statuses
            else "empty"
        )
        wire["outcome"] = {
            "status": status,
            "reason": None
            if status == "ok"
            else "The supplied context, explicit identity joins or original source/query scope are incomplete or have no matching included records. This is not global inactivity or absence of targets.",
        }
    result = MoleculeActivityResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
        deepcopy(options),
        access,
        members,
    )
    access._objects[ref] = wire
    access._scientific_cache[cache_key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Keep bounded machine pages explicit about deferred values and interpretation."""
    from .card_bioactivity_access import defer_frame as defer_original

    return defer_original(frame)
