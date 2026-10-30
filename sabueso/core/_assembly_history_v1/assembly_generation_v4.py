# Frozen from 77fd770e4d2a8fa94eea3fbd723a84fc90875efb / SDK135.
"""Frozen declared component/operation occurrences over original native inputs."""

from ..errors import ArgumentError
from . import assembly_generation_v3 as original
from . import assembly_occurrences_v1 as occurrences
from .assembly_generation_v2 import _location, _UnpinnedCard
from .assembly_requests import budget

RULE = "rcsb_assembly_generation@4"


def _locations(result, pin):
    for source in result["sources"]:
        ref = source["source_assertion_id"]

        def locate(node, field="input"):
            node[field + "_location"] = _location(pin, ref, node[field + "_path"])

        source["source_location"] = _location(pin, ref, [])
        for parent in source["assemblies"]:
            for item in parent["generators"]:
                locate(item)
                for reference in item.get("component_bindings", []):
                    locate(reference)
        for node in source.get("operator_registry", []):
            for projection in node["projections"]:
                locate(projection)
        for node in source.get("component_registry", []):
            for reference in node["references"]:
                locate(reference)
                for field in ("entity_input", "instance_input"):
                    if field + "_path" in reference:
                        locate(reference, field)
        for issue in [
            *source.get("operator_input_issues", []),
            *source.get("component_input_issues", []),
        ]:
            locate(issue)


def _delivery(result, requested, *, occurrence):
    if not requested:
        return "not_requested"
    if not result["sources"]:
        return "not_available"
    incomplete = bool(result["unplaced"] or result["gaps"]) or any(
        source["status"] not in ("retained", "retained_empty")
        or any(
            parent["status"] not in ("retained", "retained_empty")
            or any(
                item["occurrence_plan"]["status"] not in ("planned", "retained_empty")
                if occurrence
                else item["status"] != "parsed"
                for item in parent["generators"]
            )
            for parent in source["assemblies"]
        )
        for source in result["sources"]
    )
    return "incomplete" if incomplete else "expanded"


def generation(
    card,
    structure_ref,
    relationship_id,
    expand_operations,
    operation_budget,
    expand_occurrences=False,
):
    limit = budget(operation_budget)
    for name, value in [
        ("expand_operations", expand_operations),
        ("expand_occurrences", expand_occurrences),
    ]:
        if type(value) is not bool:
            raise ArgumentError(f"{name} requires a boolean.", argument=name)
    result = original.generation(
        _UnpinnedCard(card), structure_ref, relationship_id, False, limit
    )
    rows = occurrences.prepare(result)
    work = occurrences.preflight(rows, expand_operations, expand_occurrences, limit)
    pin = card.pinned_ref() if card.id else None
    if pin:
        _locations(result, pin)
    occurrences.materialize(rows, expand_operations, expand_occurrences)
    result.update(
        rule=RULE,
        scope=occurrences.SCOPE,
        card_ref=pin,
        quality_location={
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": pin,
            "snapshot_id": pin.rsplit("@", 1)[1],
            "segments": [{"type": "Key", "value": "quality"}],
        }
        if pin
        else None,
        occurrence_rule=occurrences.RULE,
        occurrence_plan_summary={
            "scope": "retained_generator_declarations_only",
            **{
                state: sum(
                    item["occurrence_plan"]["status"] == state for _, item in rows
                )
                for state in ("planned", "retained_empty", "unavailable")
            },
        },
        tuple_expansion_state=_delivery(result, expand_operations, occurrence=False),
        occurrence_expansion_state=_delivery(
            result, expand_occurrences, occurrence=True
        ),
        **work,
    )
    result["request"].update(
        expand_operations=expand_operations,
        expand_occurrences=expand_occurrences,
        generation_rule=RULE,
    )
    return result
