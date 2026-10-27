# Frozen original quaternary history from0830de5/SDK109 (#148).
"""Readable quaternary findings over one captured, source-bound native result.

The native readers own interpretation. This adapter presents interface findings
and every family comparison separately; it never creates source knowledge.
"""

from copy import deepcopy
from dataclasses import dataclass, replace
from types import SimpleNamespace

from .card_access import _Entry, _handle
from .card_exploration_verification import _historical_resolution
from .card_quaternary_selection_v1 import COLUMNS as AGENT_COLUMNS
from .card_quaternary_selection_v1 import DEFAULT_FIELDS, item_ref
from .errors import ArgumentError

SUPPORT_FORMAT = "quaternary_support_membership@1"

TOPIC = "quaternary_interpretation"

ADAPTER = "quaternary_exploration@1"

LINK_RULE = "quaternary_interpretation_links@1"

COLUMNS = ("partner_ref", "status", "coordinate_status", "finding", "reason")

HEADERS = (
    "Index",
    "Finding",
    "Kind",
    "Partner",
    "Interpretation",
    "Coordinates",
    "Result",
    "Context",
)

SCOPE = (
    "Source-bound interface classifications and individual interface/family-site "
    "comparisons. A source-declared self-interface is not a validated biological "
    "assembly. Aggregate interfaces are not physical assembly occurrences; no "
    "geometry, affinity or biological relevance is inferred. Uncomputed positions "
    "are unknown, not zero or source absence. Original subunit and assembly "
    "declarations: explorer.view('quaternary_structure'). Source/request coverage: "
    "explorer.view('coverage')."
)

REASONS = {
    "declaration_subject_not_focal": "This declaration refers to another protein.",
    "source_support_missing_or_foreign": "The original source support is missing or refers to another subject.",
    "source_references_unavailable_or_invalid": "Usable original source references are unavailable.",
    "source_identity_unavailable": "The source identity was not retained in a usable form.",
    "source_qualifier_binding_differs": "The retained qualifiers differ from their original source record.",
    "source_object_reference_differs": "The retained partner or structure differs from the original record.",
    "interface_native_partner_binding_unavailable": "The partner reference cannot be confirmed against the original interface record.",
    "interface_native_structure_references_differ": "The listed structures differ from those in the original interface record.",
    "interface_native_structure_scope_unavailable": "The original interface does not provide usable structure references.",
    "canonical_identity_sequence_or_length_unavailable": "A consistent canonical protein identity, sequence and length are unavailable.",
    "conflicting_canonical_inputs": "The retained canonical reference inputs conflict.",
    "canonical_source_support_unavailable": "Original support for the canonical reference is unavailable.",
    "interface_numbering_not_comparable": "Interface numbering is not on the admitted canonical sequence axis.",
    "interface_axis_not_canonical": "The interface refers to another sequence axis.",
    "interface_positions_unstated_or_invalid": "Interface positions are unstated, uncertain or invalid.",
    "conflicting_interface_coordinates": "The retained interface coordinates conflict.",
    "interface_sequence_version_differs": "The stated interface and reference sequence revisions differ.",
    "interface_sequence_version_invalid": "The interface sequence revision is not usable.",
    "annotation_axis_not_canonical": "The family annotation is not on the focal canonical sequence.",
    "annotation_positions_uncertain_or_invalid": "Family annotation bounds are uncertain or invalid.",
    "annotation_sequence_revision_differs": "Family annotation and reference revisions are invalid or inconsistent.",
    "annotation_source_support_unavailable": "Original source support for the family annotation is unavailable.",
    "conflicting_annotation_inputs": "The retained family annotation inputs conflict.",
    "native_annotation_scope_not_retained": "The original family coordinate context was not retained.",
    "structure_context_unavailable_or_conflicting": "Some retained structures lack a usable, consistent entity mapping or coverage; inspect each declaration.",
    "conflicting_or_unrecognized_interface_structures": "The interface structure references conflict or have an unsupported shape.",
    "partner_protein_reference_unavailable": "A source-declared protein reference for this partner is unavailable.",
}

FINDINGS = {
    "homomeric": "Source-declared self-interface",
    "heteromeric": "Qualified non-fragment complex context with this partner",
    "chimera": "Source entity mapping includes both proteins",
    "fragment_complex": "Retained qualified contexts contain protein fragments",
    "chimera_or_fragment": "Retained contexts are chimeric or fragmentary",
    "undetermined": "Interface classification not computed",
}


def reason_text(codes):
    return " ".join(
        REASONS.get(
            code,
            "The retained input could not be admitted; inspect its original scope and reason code.",
        )
        for code in dict.fromkeys(code for code in codes if code)
    )


def _rows(native):
    """Stable grains are relationship IDs and original family field ordinals."""
    rows = {}
    for index, item in enumerate(native["interfaces"]):
        reason = reason_text(
            [
                item["classification"].get("reason"),
                item["coordinate_scope"].get("reason"),
            ]
        )
        if not reason:
            reason = "Based on retained source references and structure context; this does not establish biological assembly relevance."
        rows["interface:" + item["relationship_id"]] = {
            "label": item["partner_name"]
            if isinstance(item.get("partner_name"), str) and item["partner_name"]
            else item["partner_ref"],
            "kind": "interface_classification",
            "partner_ref": item["partner_ref"],
            "status": item["classification"]["status"],
            "coordinate_status": item["coordinate_scope"]["status"],
            "finding": FINDINGS[item["class"]],
            "reason": reason,
            "item": deepcopy(item),
            "explanation_index": index,
        }
    for index, item in enumerate(native["agreement"]):
        compared = item["comparison"]["status"] == "comparable"
        finding = (
            f"{len(item['both'])} shared positions; {len(item['family_only'])} family-only; {len(item['observed_only'])} interface-only"
            if compared
            else "Position comparison not computed"
        )
        codes = item["comparison"]["reasons"]
        reason = reason_text(codes)
        if not compared and not reason:
            reason = "Coordinate inputs could not be admitted; inspect their original scopes."
        if compared:
            revisions = [
                item["comparison"][key].get("sequence_revision_agreement")
                for key in ("interface_scope", "family_scope")
            ]
            reason = (
                "Compared on source-declared canonical numbering with matching stated sequence revisions."
                if revisions == ["matching_stated_versions"] * 2
                else "Compared on source-declared canonical numbering; agreement of sequence revisions is not established."
            )
        rows[
            f"comparison:{item['interface_relationship_id']}:{item['family_site_index']}"
        ] = {
            "label": item["family_site"],
            "kind": "interface_family_comparison",
            "partner_ref": native["canonical_reference"]["sequence_ref"],
            "status": "computed" if compared else "not_computed",
            "coordinate_status": item["comparison"]["status"],
            "finding": finding,
            "reason": reason,
            "item": deepcopy(item),
            "explanation_index": index,
        }
    return rows


def _materialize(access):
    from ._card_quaternary_explanation_v1 import _explain_oligomer
    from ._card_quaternary_native_v1 import oligomer_view
    from .card_exploration_history import _HistoricalInput as _CapturedCard
    from .card_ligand_site_history_v1 import _location, _rule_identity, _statement

    native, rows, explanations, supports, explanation = {}, {}, {}, {}, {}
    outcome = {
        "status": "not_applicable",
        "reason": "Quaternary interpretation requires a protein Card.",
    }
    if access.profile == "protein" and not access._focal.pin:
        outcome = {
            "status": "missing_prerequisite",
            "reason": "A captured protein identity is required; inspect the original content.",
        }
    elif access.profile == "protein":
        card = _CapturedCard(access._focal)
        native = oligomer_view(card)
        explanation = _explain_oligomer(card, native)
        rows = _rows(native)
        outcome = {
            "status": "ok" if rows else "empty",
            "reason": None
            if rows
            else "No interface classifications or interface/family pairs are retained. Inspect subunit/assembly declarations and source/request coverage; this is not evidence of no interface.",
        }
    identity = deepcopy(native)
    if "rules" in identity:
        identity["rules"] = [_rule_identity(rule) for rule in identity["rules"]]
    ref = _handle(
        "XR_", {"adapter": ADAPTER, "focal": access._focal_key, "native": identity}
    )

    def location(*keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    for key, row in rows.items():
        item = row["item"]
        classification = row["kind"] == "interface_classification"
        index = row.pop("explanation_index")
        original = explanation["interfaces" if classification else "agreement"][index]
        ids = set(native["canonical_reference"]["inputs"]) | set(
            item["source_assertion_ids"]
        )
        relationship_id = item["relationship_id"]
        relationship_locations = [
            _location(access, "relationship_store", relationship_id)
        ]
        if classification:
            for bases in item["basis"].values():
                for basis in bases:
                    rid = basis["relationship_id"]
                    if rid is not None:
                        declaration = card.relationship_store.get(rid)
                        ids.update(declaration.get("source_assertion_ids", []))
                        relationship_locations.append(
                            _location(access, "relationship_store", rid)
                        )
        supports[key] = {
            "basis": "derived_quaternary_interpretation",
            "rules": deepcopy(native["rules"]),
            "canonical_scope_rule": native["canonical_reference"]["rule"],
            "source_assertions": [
                _statement(access, source_id) for source_id in sorted(ids)
            ],
            "relationship_locations": relationship_locations,
            "scope": SCOPE,
        }
        explanations[key] = {
            "original_interpretation": deepcopy(original),
            "reference_inputs_location": location("explanation", "fields"),
            "source_request_context_location": location("explanation", "context"),
            "full_explanation_location": location("explanation"),
            "scope": SCOPE,
        }
        row["support_location"] = location("support", key)
        row["explanation_location"] = location("explanations", key)
        reason_codes = (
            [
                item["classification"].get("reason"),
                item["coordinate_scope"].get("reason"),
            ]
            + [
                basis.get("reason")
                for bases in item["basis"].values()
                for basis in bases
            ]
            if classification
            else item["comparison"]["reasons"]
        )
        row["interpretation"] = {
            "scope": SCOPE,
            "rule_names": list(
                dict.fromkeys(
                    [rule["rule"] for rule in native["rules"]]
                    + [native["canonical_reference"]["rule"]]
                )
            ),
            "reason_codes": list(dict.fromkeys(code for code in reason_codes if code)),
            "kind": row["kind"],
            "status": row["status"],
            "coordinate_status": row["coordinate_status"],
            "original_input_scope_location": location("rows", key, "item"),
            "revision_agreement": "Only matching explicitly stated sequence revisions establish agreement; inspect original coordinate scopes.",
        }
    access._objects[ref] = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "options": {},
            "used_captures": [access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "explanation": explanation,
        "explanations": explanations,
        "support": supports,
        "scope": SCOPE,
        "coverage": {
            "basis": "retained_interface_declarations_and_family_pairs",
            "scope": SCOPE,
            "source_request_classification": "not_evaluated_by_this_adapter",
        },
        "outcome": outcome,
    }
    return ref


def payload(item):
    return item._view.explorer.access._objects[item._entry.location["result_ref"]]


def support(item):
    return [deepcopy(payload(item)["support"][item._entry.key])]


def explain(item):
    explorer = item._view.explorer
    body = payload(item)["explanations"][item._entry.key]
    location = {
        **item._entry.location,
        "segments": [
            {"type": "Key", "value": key} for key in ("explanations", item._entry.key)
        ],
    }
    view = explorer._inspect(
        location, item._view, title=f"Original interpretation inputs · {item.label}"
    )
    entries = tuple(
        _Entry(
            statement["location"],
            statement["id"],
            explorer.access._resolve(statement["location"])[0],
        )
        for statement in support(item)[0]["source_assertions"]
        if statement["state"] == "present"
    )
    explorer._session["views"].pop(id(view), None)
    return replace(
        view,
        _selection=replace(view._selection, _entries=entries),
        _selected=entries,
        _native_override=body,
        _reason="Original source statements and complete interpretation/input destinations; unretained support remains explicit in native_payload.",
    )


def links(item):
    from .card_ligand_site_history_v1 import _link_view

    explorer = item._view.explorer
    basis = support(item)
    rows = []
    for statement in basis[0]["source_assertions"]:
        if statement["state"] == "present":
            rows.append(
                _link(
                    explorer,
                    "source",
                    statement["id"],
                    basis,
                    location=statement["location"],
                )
            )
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Unavailable original input · " + statement["id"],
                    "target_ref": statement["id"],
                    "support": deepcopy(basis),
                    "rule": LINK_RULE,
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    for location in basis[0]["relationship_locations"]:
        record = explorer.access._resolve(location)[0]
        role = (
            "structure_context"
            if record["predicate"] == "has_structure"
            else "interface_statement"
        )
        link = _link(explorer, role, record["id"], basis, location=location)
        link["label"] = (
            f"{role.replace('_', ' ').capitalize()} · {record['object_ref']} · {record['id']}"
        )
        rows.append(link)
    if item._entry.value["kind"] == "interface_family_comparison":
        index = item._entry.value["item"]["family_site_index"]
        location = explorer._location(
            "sections", "features_positional", "family_site", "value"
        )
        location["segments"].append({"type": "Index", "value": index})
        rows.append(
            _link(
                explorer,
                "family_annotation",
                f"family_site[{index}]",
                basis,
                location=location,
            )
        )
    rows.append(
        _link(
            explorer,
            "source_request_context",
            "quality",
            basis,
            location=explorer._location("quality"),
        )
    )
    return _link_view(
        explorer,
        [{**row, "rule": LINK_RULE} for row in rows],
        item._view,
        f"Original context for {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
    )


def descriptor():
    return {
        "key": TOPIC,
        "label": "Interface classifications and family-site comparisons",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {key: {"type": "string"} for key in AGENT_COLUMNS},
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "quaternary_access_selection@1",
        "mandatory_interpretation": [
            "scope",
            "rule_names",
            "status",
            "coordinate_status",
            "revision_agreement",
            "reason_codes",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
    }


def options_for_quaternary(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(f"{TOPIC} has no scientific options.")
    return {}


@dataclass(frozen=True)
class _QuaternaryResult:
    result_ref: str
    wire: dict
    entries: tuple

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def native_item(self, key):
        return self.wire["rows"][key]["item"]

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def frame(self, access, selection, entry):
        key = entry.key
        row, original = self.wire["rows"][key], self.wire["support"][key]
        interpretation_location = access._location(
            self.location("rows", key, "interpretation")
        )
        return {
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "location": access._location(entry.location),
            "payload_location": access._location(self.location("rows", key, "item")),
            "relationship_ref": row["item"]["relationship_id"],
            "subject_ref": access._resolve(original["relationship_locations"][0])[0][
                "subject_ref"
            ],
            "state": "present",
            "support_location": access._location(self.location("support", key)),
            "support": {
                "ref": key,
                "format": SUPPORT_FORMAT,
                "basis": original["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": row["id"], "state": row["state"]}
                    for row in original["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation_location,
            "cells": {
                column: {
                    "state": "present",
                    "reason": None,
                    "value": deepcopy(self.value(key, column)),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": "derived_quaternary_interpretation",
                    "support_ref": key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", key, column)
                    ),
                    "interpretation_location": interpretation_location,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def defer_frame(frame):
    """Defer values and mandatory interpretation/support together, with read paths."""
    result = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    result.update(
        cells={
            key: {k: deepcopy(value) for k, value in cell.items() if k != "value"}
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return result


def restore_result(ref, wire):
    shell = _QuaternaryResult(ref, wire, ())
    native = wire["native_payload"]
    keys = [
        "interface:" + row["relationship_id"] for row in native.get("interfaces", [])
    ]
    keys.extend(
        f"comparison:{row['interface_relationship_id']}:{row['family_site_index']}"
        for row in native.get("agreement", [])
    )
    entries = tuple(
        _Entry(shell.location("rows", key), key, wire["rows"][key]) for key in keys
    )
    return _QuaternaryResult(ref, wire, entries)


def expected_result(access):
    from .card_exploration_storage import _access

    original = _access(access._captures, access._inputs, {}, {}, access._focal_key)
    original._mode = "live"
    ref = _materialize(original)
    return restore_result(ref, original._objects[ref])


def expected_links(access, result, key):
    from .card_exploration_storage import _access
    from .card_ligand_site_history_v1 import _Context

    original = _access(
        access._captures,
        access._inputs,
        {result.result_ref: result.wire},
        {},
        access._focal_key,
    )
    original._mode = "live"
    explorer = _Context(original)
    item = SimpleNamespace(
        _view=SimpleNamespace(explorer=explorer),
        _entry=SimpleNamespace(
            key=key,
            value=result.wire["rows"][key],
            location=result.location("rows", key),
        ),
        label=result.wire["rows"][key]["label"],
        payload_location=result.location("rows", key),
    )
    return links(item)


def _link(explorer, role, target, support, *, location=None):
    label = f"{role.capitalize()} · {target}"
    if role == "source" and location:
        original, _ = explorer.access._resolve(location)
        fields = {
            "sequence.checksums": "reference sequence checksums",
            "sequence.primary": "reference primary sequence",
            "identifiers.uniprot": "reference UniProt identity",
            "sequence.length": "reference sequence length",
            "annotations.isoforms": "UniProt isoform declaration",
            "relationships.has_predicted_structure": "predicted model metadata",
        }
        if isinstance(original, dict) and original.get("field_path") in fields:
            label = f"Source · {fields[original['field_path']]} · {target}"
    resolution = (
        {
            "candidates": [
                {
                    "location": location,
                    "capture": explorer.access._focal_key,
                    "basis": "exact_retained_node",
                }
            ],
            "paths": [],
            "blocked_paths": [],
            "availability": "available",
        }
        if location
        else _historical_resolution(explorer.access, target)
    )
    return {
        "role": role,
        "label": label,
        "target_ref": target,
        "support": deepcopy(support),
        "rule": "retained_context_links@2",
        **resolution,
    }
