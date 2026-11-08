"""Captured native clinical knowledge, with separate citation and registry roles."""

from copy import deepcopy
from dataclasses import dataclass

from ..card_access import _Entry, _handle
from ..errors import ArgumentError
from ..snapshot import canonical_json
from .selection import COLUMNS, DEFAULT_FIELDS, SORT_COLUMNS, item_ref

TOPIC = "clinical"
ADAPTER = "clinical_exploration@1"
SUPPORT_FORMAT = "clinical_support_membership@1"
SCOPE = (
    "ChEMBL molecule/indication phases, individual source-cited trial occurrences "
    "and retained ClinicalTrials.gov records. Source phases and registry status "
    "retain distinct meanings; citations, study completion and reported results "
    "do not establish efficacy or a treatment recommendation. No source acquisition."
)
AREAS = (
    "clinical.max_phase",
    "relationships.investigated_for",
    "relationships.tested_in",
)


def descriptor():
    return {
        "key": TOPIC,
        "label": "Indications and clinical studies",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {
                "type": "number|null"
                if key == "chembl_max_phase"
                else "integer|null"
                if key == "citation_count"
                else "array[string]|null"
                if key == "registry_phases"
                else "string|null"
            }
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "sortable_columns": list(SORT_COLUMNS),
        "selection_policy": "clinical_access_selection@1",
        "mandatory_interpretation": [
            "scope",
            "row_grain",
            "rule_names",
            "phase_scope",
            "registry_scope",
            "query_coverage_scope",
            "support_state",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Exact retained original records; each support role keeps its own subject and field.",
        },
        "save": False,
        "save_reason": "Independent original clinical saved reading is not implemented.",
    }


def options_for_clinical(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(
            "clinical has no scientific options; use typed display selection."
        )
    return {}


@dataclass(frozen=True)
class ClinicalResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    @property
    def explanations(self):
        return self.wire["explanations"]

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
        if self.value(key, column) is not None:
            return "present"
        kind = self.value(key, "kind")
        applicable = (
            column in ("chembl_max_phase", "disease_ref", "disease_term")
            and kind in ("clinical_indication", "clinical_trial_citation")
            or column == "citation_count"
            and kind == "clinical_indication"
            or column == "chembl_max_phase"
            and kind == "clinical_molecule_phase"
            or column in ("trial_ref", "registry_state")
            and kind in ("clinical_trial_citation", "clinical_registry_record")
            or column in ("registry_status", "registry_phases")
            and kind == "clinical_registry_record"
            and self.value(key, "registry_state") != "not_found"
        )
        return "unknown" if applicable else "not_applicable"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        return (
            None
            if state == "present"
            else "The native clinical item does not retain a value for this field."
            if state == "unknown"
            else "This field belongs to a different clinical row grain."
        )

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
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
            "state": row["state"],
            "support_location": access._location(self.location("support", entry.key)),
            "support": {
                "ref": entry.key,
                "format": SUPPORT_FORMAT,
                "basis": support["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": r["id"], "state": r["state"], "role": r["role"]}
                    for r in support["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "value": deepcopy(self.value(entry.key, column)),
                    "state": self.cell_state(entry.key, column),
                    "reason": self.cell_reason(entry.key, column),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": support["basis"],
                    "support_ref": entry.key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, column)
                    ),
                    "interpretation_location": interpretation,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def _record_location(access, store, identifier):
    return access._card_location(
        segments=[
            {"type": "Key", "value": store},
            {"type": "Record", "value": identifier},
        ]
    )


def _membership(access, identifier, roles):
    source = next(
        (
            r
            for r in access._focal.data["source_assertion_store"]
            if r["id"] == identifier
        ),
        None,
    )
    matches = [
        role
        for role, subject, field, name in roles
        if source is not None
        and source.get("subject_ref") == subject
        and source.get("field_path") == field
        and (source.get("source") or {}).get("name") == name
    ]
    return {
        "id": identifier,
        "state": "present"
        if matches
        else "not_retained"
        if source is None
        else "role_mismatch",
        "role": matches[0] if len(matches) == 1 else "unverified",
        "expected_roles": [
            {"role": role, "subject_ref": subject, "field_path": field, "source": name}
            for role, subject, field, name in roles
        ],
        "location": _record_location(access, "source_assertion_store", identifier)
        if source
        else None,
    }


def _support(access, relationships, *, phase=None):
    memberships = []
    for rel in relationships:
        roles = [
            (
                "indication_citation",
                rel["subject_ref"],
                "relationships.investigated_for",
                "ChEMBL",
            )
        ]
        if rel["predicate"] == "tested_in":
            roles.append(
                (
                    "registry_record",
                    rel["object_ref"],
                    "relationships.tested_in",
                    "ClinicalTrials.gov",
                )
            )
        memberships.extend(
            _membership(access, ref, roles)
            for ref in rel.get("source_assertion_ids", [])
        )
    if phase is not None:
        aliases = {
            rel["subject_ref"]
            for rel in access._focal.data["relationship_store"]
            if rel["predicate"] == "same_as"
        }
        roles = [
            ("molecule_phase", subject, "clinical.max_phase", "ChEMBL")
            for subject in sorted(aliases)
        ]
        memberships.extend(
            _membership(access, ref, roles)
            for ref in phase.get("source_assertion_ids", [])
        )
    seen, unique = set(), []
    for record in memberships:
        identity = canonical_json(record)
        if identity not in seen:
            seen.add(identity)
            unique.append(record)
    valid = bool(unique) and all(r["state"] == "present" for r in unique)
    return {
        "format": SUPPORT_FORMAT,
        "basis": "retained_role_bound_source_membership"
        if valid
        else "support_membership_unverified",
        "state": "retained" if valid else "partial",
        "source_assertions": unique,
        "relationships": [
            {
                "id": r["id"],
                "state": "present",
                "location": _record_location(access, "relationship_store", r["id"]),
            }
            for r in relationships
        ],
        "qualifier_conflicts": [
            {
                "relationship_id": r["id"],
                "conflicts": deepcopy(r["qualifier_conflicts"]),
            }
            for r in relationships
            if r.get("qualifier_conflicts")
        ],
        "quality_location": access._card_location(
            segments=[{"type": "Key", "value": "quality"}]
        ),
        "whole_card_context_location": access._card_location(),
    }


def _row(kind, label, item, **cells):
    return {
        **dict.fromkeys(COLUMNS),
        "label": label,
        "kind": kind,
        "state": "retained",
        **cells,
        "item": deepcopy(item),
    }


def materialize(access, options=None):
    """Read the captured native view once; opening this panel never fetches trials."""
    options_for_clinical(options)
    if access.mode != "live":
        raise ArgumentError(
            "Independent original clinical saved reading is not implemented."
        )
    if access.profile != "small_molecule":
        raise ArgumentError("clinical requires a small-molecule Card.")
    key = (ADAPTER, access._focal_key)
    if key in access._scientific_cache:
        return access._scientific_cache[key]
    from .inputs import _CapturedCard

    card = _CapturedCard(access._focal)
    native, knowledge = deepcopy(card.clinical()), card.knowledge_state()
    coverage = {
        "rule": deepcopy(knowledge["rule"]),
        "rows": [deepcopy(r) for r in knowledge["rows"] if r["area"] in AREAS],
        "scope_note": "Original knowledge-state and request records; not_fetched does not distinguish an unrequested, bounded or failed request on its own. No global absence is inferred.",
    }
    coverage["native_rows"] = deepcopy(coverage["rows"])
    coverage["request_scope_rule"] = "clinical_query_scope@1"
    quality = access._focal.data.get("quality", {})
    reports = quality.get("enrichments") if isinstance(quality, dict) else None
    stated = {row["area"] for row in coverage["rows"]}
    for area, source in (
        ("relationships.investigated_for", "ChEMBL"),
        ("relationships.tested_in", "ClinicalTrials.gov"),
    ):
        if area not in stated:
            coverage["rows"].append(
                {
                    "area": area,
                    "source": source,
                    "state": "not_queried"
                    if isinstance(reports, list)
                    else "not_recorded",
                    "count": None,
                    "release": None,
                    "basis": {
                        "rule": "clinical_query_scope@1",
                        "detail": "No matching request report in the retained enrichment ledger."
                        if isinstance(reports, list)
                        else "The original enrichment ledger is not retained; request history is unknown.",
                    },
                }
            )
    relationships = access._focal.data["relationship_store"]
    rows, supports = {}, {}
    phase = card.get("clinical.max_phase")
    if isinstance(phase, dict):
        rows["molecule_phase"] = _row(
            "clinical_molecule_phase",
            "ChEMBL molecule maximum phase",
            phase,
            chembl_max_phase=native["max_phase"],
        )
        supports["molecule_phase"] = _support(access, [], phase=phase)
    trial_rows = {}
    for index, trial in enumerate(native["trials"]):
        row_key = f"registry:{index}"
        rels = [
            r
            for r in relationships
            if r["predicate"] == "tested_in"
            and r["subject_ref"] == trial["molecule"]
            and r["object_ref"] == trial["trial"]
        ]
        trial_rows.setdefault((trial["molecule"], trial["trial"]), []).append(row_key)
        membership = _support(access, rels)
        registry_retained = any(
            r["state"] == "present" and r["role"] == "registry_record"
            for r in membership["source_assertions"]
        )
        state = (
            "not_found"
            if trial.get("registry") == "not_found"
            else "received"
            if registry_retained
            else "unverified"
        )
        rows[row_key] = _row(
            "clinical_registry_record",
            trial.get("title") or trial["trial"],
            trial,
            molecule_ref=trial["molecule"],
            trial_ref=trial["trial"],
            registry_state=state,
            registry_status=trial.get("status"),
            registry_phases=trial.get("phases"),
        )
        supports[row_key] = membership
    # Native indication order and per-indication citation occurrences remain intact.
    indication_rows = {}
    for index, indication in enumerate(native["indications"]):
        row_key = f"indication:{index}"
        rels = [
            r
            for r in relationships
            if r["predicate"] == "investigated_for"
            and r["subject_ref"] == indication["molecule"]
            and r["object_ref"] == indication["disease"]
        ]
        cells = {
            "molecule_ref": indication["molecule"],
            "disease_ref": indication["disease"],
            "disease_term": indication["disease_term"],
            "chembl_max_phase": indication["max_phase"],
        }
        indication_rows[row_key] = _row(
            "clinical_indication",
            indication["disease_term"] or indication["disease"],
            indication,
            **cells,
            citation_count=len(indication["trials"]),
        )
        supports[row_key] = _support(access, rels)
        for position, nct in enumerate(indication["trials"]):
            citation_key = f"citation:{index}:{position}"
            destinations = trial_rows.get((indication["molecule"], "nct:" + nct), [])
            states = {rows[k]["registry_state"] for k in destinations}
            indication_rows[citation_key] = _row(
                "clinical_trial_citation",
                f"{nct} · cited for {indication['disease_term'] or indication['disease']}",
                {
                    "nct_id": nct,
                    "molecule": indication["molecule"],
                    "disease": indication["disease"],
                    "indication_row_key": row_key,
                    "citation_position": position,
                },
                **cells,
                trial_ref="nct:" + nct,
                registry_state=next(iter(states))
                if len(states) == 1
                else "not_fetched"
                if not states
                else "conflicting",
            )
            supports[citation_key] = deepcopy(supports[row_key])
            supports[citation_key]["indication_row_key"] = row_key
            supports[citation_key]["registry_row_keys"] = list(destinations)
    rows = {
        **(
            {"molecule_phase": rows.pop("molecule_phase")}
            if "molecule_phase" in rows
            else {}
        ),
        **indication_rows,
        **rows,
    }
    incomplete = any(
        r["state"]
        in ("not_queried", "not_recorded", "unavailable", "partial", "conflicting")
        for r in coverage["rows"]
    )
    partial_support = any(
        s["state"] != "retained" or s["qualifier_conflicts"] for s in supports.values()
    )
    outcome = {
        "status": "missing_prerequisite"
        if not access._focal.pin
        else "partial"
        if incomplete or partial_support
        else "ok"
        if rows
        else "empty",
        "reason": "Original source/query gaps or support limitations remain; consult clinical coverage and original quality records."
        if incomplete or partial_support
        else None,
    }
    ref = _handle(
        "XR_",
        {
            "format": "clinical_exploration_result@1",
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "native": native,
            "coverage": coverage,
            "rows": rows,
            "support": supports,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "grain": "separate molecule phase, indication, cited-trial occurrence and registry record",
            "options": {},
            "used_captures": [access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "support": supports,
        "coverage": coverage,
        "scope": SCOPE,
        "schema": descriptor(),
        "outcome": outcome,
        "explanations": {},
        "exclusions": [],
    }
    shell = ClinicalResult(ref, wire, (), {})
    for row_key, row in rows.items():
        original = supports[row_key]
        row["state"] = (
            "partial"
            if original["state"] != "retained" or original["qualifier_conflicts"]
            else "retained"
        )
        row["interpretation"] = {
            "scope": SCOPE,
            "row_grain": row["kind"],
            "rule_names": [ADAPTER, SUPPORT_FORMAT],
            "phase_scope": "ChEMBL maximum phase is separate from registry study phases; native values and ordering are unchanged.",
            "registry_scope": "A cited ID is not a fetched registry record. Intervention names do not establish molecule identity; has_results does not establish efficacy.",
            "query_coverage_scope": coverage["scope_note"],
            "support_state": original["state"],
            "qualifier_conflicts": deepcopy(original["qualifier_conflicts"]),
            "context_location": shell.location("context"),
        }
        wire["explanations"][row_key] = {
            "item": deepcopy(row["item"]),
            "support": deepcopy(original),
            "interpretation": deepcopy(row["interpretation"]),
        }
    result = ClinicalResult(
        ref,
        wire,
        tuple(_Entry(shell.location("rows", k), k, row) for k, row in rows.items()),
        {},
    )
    access._objects[ref] = wire
    access._scientific_cache[key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Defer scientific values and their mandatory interpretation together."""
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
