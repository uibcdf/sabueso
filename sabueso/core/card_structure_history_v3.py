"""Frozen original structure explanation @3 / declaration admission @1 bindings over captured inputs only."""

from copy import deepcopy

from .card_access import _Entry, _handle
from .card_exploration_adapter_v1 import (
    ADAPTER,
    RESOLUTION_FIELD,
    _HistoricalResult,
    _rule_identity,
    _wire_explanation,
    _wire_inventory,
    _wire_row,
)
from .card_exploration_adapter_v1 import (
    _descriptor as _original_descriptor,
)
from .card_exploration_coverage_v1 import _v1_knowledge_state
from .card_exploration_history import _HistoricalInput, _rule
from .card_exploration_structure_v1 import (
    _v1_coverage_derivation,
    _v1_state_derivation,
    _v1_structure_inventory,
    _v1_structures_view,
    _v1_support,
)
from .structure_explanation_scope_v3 import RULE as EXPLANATION_RULE
from .structure_explanation_scope_v3 import evaluate


def _descriptor():
    value = _original_descriptor()
    value["mandatory_interpretation"].insert(1, "admission")
    return value


def _v2_structures_view(card, **options):
    from .experimental_structure_admission_v1 import view

    return view(card, summary=_v1_structures_view, rule=_rule, **options)


def _v2_structure_inventory(cards, **options):
    from .experimental_structure_admission_v1 import inventory

    return inventory(cards, summarize=_v1_structure_inventory, rule=_rule, **options)


def explain_original(*args, **kwargs):
    return evaluate(
        *args,
        **kwargs,
        rule=_rule,
        support=_v1_support,
        structures_view=_v2_structures_view,
        coverage_derivation=_v1_coverage_derivation,
        state_derivation=_v1_state_derivation,
    )


def expected_structures(access, options):
    """Evaluate once per normalized scientific request; all later reads use the result."""
    native, explanations, excluded, rows = ({}, {}, [], {})
    rules = []
    outcome = {
        "status": "not_applicable",
        "reason": "The structures adapter requires a protein Card.",
    }
    coverage = {
        "basis": "stored_literal",
        "classification": "not_evaluated",
        "rows": [],
    }
    if access.profile == "protein" and (not access._focal.pin):
        outcome = {
            "status": "missing_prerequisite",
            "reason": "A captured Card identity is required for pinned structural explanations. Use literal inspection.",
        }
    elif access.profile == "protein":
        card = _HistoricalInput(access._focal)
        native = _v2_structure_inventory(
            [card],
            regions=options["region"],
            include_fragments=options["include_fragments"],
        )
        rules = [
            native["rule"],
            _v1_coverage_derivation(),
            _v1_state_derivation(),
            native["admission_rule"],
        ]
        knowledge = _v1_knowledge_state(card)
        coverage = {
            "basis": "original_scoped_knowledge_state",
            "rule": knowledge["rule"],
            "rows": [
                row
                for row in knowledge["rows"]
                if row["area"].startswith("relationships.has_structure")
            ],
            "quality_location": access._card_location(
                segments=[{"type": "Key", "value": "quality"}]
            ),
            "scope_note": "Retained source/request scope; inventory sequence coverage does not establish coordinate completeness.",
        }
        for row in native["items"]:
            key = row["relationship_id"]
            rows[key] = _wire_row(row)
            explanations[key] = explain_original(
                [card],
                card.id,
                row["structure_ref"],
                native,
                relationship_id=key,
                regions=options["region"],
                include_fragments=options["include_fragments"],
            )
        excluded_rows = (
            _v2_structures_view(card, include_fragments=True, region=options["region"])[
                "items"
            ]
            if native["excluded"].get(card.id)
            else []
        )
        for excluded_row in excluded_rows:
            if excluded_row["coverage_class"] != "fragment_or_peptide":
                continue
            original = explain_original(
                [card],
                card.id,
                excluded_row["structure_ref"],
                native,
                relationship_id=excluded_row["relationship_id"],
                regions=options["region"],
                include_fragments=options["include_fragments"],
            )
            excluded.append(
                {
                    "structure_ref": excluded_row["structure_ref"],
                    "relationship_id": excluded_row["relationship_id"],
                    "reason": original["reason"],
                    "explanation": _wire_explanation(original),
                }
            )
        for record in native["unplaced"].get(card.id, []):
            original = explain_original(
                [card],
                card.id,
                record["structure_ref"],
                native,
                relationship_id=record["relationship_id"],
                regions=options["region"],
                include_fragments=options["include_fragments"],
            )
            excluded.append(
                {
                    "structure_ref": record["structure_ref"],
                    "relationship_id": record["relationship_id"],
                    "status": "unplaced",
                    "reason": record["reason"],
                    "explanation": _wire_explanation(original),
                }
            )
        outcome = {
            "status": "ok" if rows else "empty",
            "reason": None
            if rows
            else "The existing inventory admits no retained entries under these options; inspect coverage and exclusions.",
        }
    identity_native = _wire_inventory(native)
    if "rule" in identity_native:
        identity_native["rule"] = _rule_identity(identity_native["rule"])
    if "admission_rule" in identity_native:
        identity_native["admission_rule"] = _rule_identity(
            identity_native["admission_rule"]
        )
    coverage_identity = (
        {**coverage, "rule": _rule_identity(coverage["rule"])}
        if "rule" in coverage
        else coverage
    )
    result_ref = _handle(
        "XR_",
        {
            "format": "scientific_exploration_result@1",
            "adapter": ADAPTER,
            "inputs": sorted(access._captures),
            "focal": access._focal_key,
            "options": options,
            "native": identity_native,
            "coverage": coverage_identity,
            "rules": [_rule_identity(rule) for rule in rules],
            "explanation_rule": EXPLANATION_RULE,
            "outcome": outcome,
        },
    )
    result = _HistoricalResult(
        result_ref, native, explanations, {}, deepcopy(options), ()
    )
    support, interpretations = ({}, {})
    relationships = {
        record["id"]: record for record in access._focal.data["relationship_store"]
    }
    available = {
        record["id"] for record in access._focal.data["source_assertion_store"]
    }
    for key, row in rows.items():
        rel = relationships[key]
        support[key] = {
            "basis": "relationship_level",
            "relationship_id": key,
            "relationship_location": access._card_location(
                segments=[
                    {"type": "Key", "value": "relationship_store"},
                    {"type": "Record", "value": key},
                ]
            ),
            "source_assertion_ids": deepcopy(rel.get("source_assertion_ids", [])),
            "rules": [deepcopy(rule) for rule in rules],
            "explanation_location": result.location("explanations", key),
        }
        support[key]["source_assertions"] = [
            {
                "id": ref,
                "state": "present" if ref in available else "not_retained",
                "location": access._card_location(
                    segments=[
                        {"type": "Key", "value": "source_assertion_store"},
                        {"type": "Record", "value": ref},
                    ]
                )
                if ref in available
                else None,
            }
            for ref in rel.get("source_assertion_ids", [])
        ]
        interpretations[key] = {
            "structure_kind": "experimental",
            "admission": deepcopy(row["admission"]),
            "coverage_scope": "retained_sequence_ranges",
            "region": deepcopy(options["region"]),
            "region_axis": "captured canonical protein positions (existing UniProt-numbered reader)",
            "coordinate_completeness": "not_established_by_coverage",
            "qualifier_conflicts": deepcopy(row.get("qualifier_conflicts")),
            "state": deepcopy(row["state"]),
            "inventory_status": explanations[key]["status"],
            "inventory_reason": explanations[key]["reason"],
            "rules": [rule["rule"] for rule in rules],
            "quantity_expectations": {
                "resolution": {"field": RESOLUTION_FIELD, "unit": "angstrom"}
            },
        }
    wire = {
        "native_payload": _wire_inventory(native),
        "items": rows,
        "explanations": {
            key: _wire_explanation(value) for key, value in explanations.items()
        },
        "support": support,
        "interpretations": interpretations,
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "explanation_rule": EXPLANATION_RULE,
            "options": deepcopy(options),
            "rules": deepcopy(rules),
            "used_captures": [access._focal_key],
        },
        "coverage": coverage,
        "exclusions": excluded,
        "outcome": outcome,
        "schema": _descriptor(),
    }
    result = _HistoricalResult(
        result_ref,
        native,
        explanations,
        wire,
        deepcopy(options),
        tuple(
            (
                _Entry(result.location("items", key), key, row)
                for key, row in sorted(
                    rows.items(), key=lambda pair: pair[1]["structure_ref"]
                )
            )
        ),
        _native_rows={row["relationship_id"]: row for row in native.get("items", [])},
    )
    return result
