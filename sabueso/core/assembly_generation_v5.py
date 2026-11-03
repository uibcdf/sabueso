"""Opt-in original nonpolymer keys, without changing earlier interpretations."""

from . import assembly_component_binding_v2 as binding
from . import assembly_generation_v4 as original
from . import assembly_occurrences_v1 as occurrences
from .assembly_generation_v2 import _UnpinnedCard
from .assembly_requests import budget
from .errors import ArgumentError

RULE = "rcsb_assembly_generation@5"
SCOPE = (
    "Source-declared component/operation occurrences with native polymer and "
    "nonpolymer instance keys inside each original entry SourceAssertion. "
    "Nonpolymer entry/entity/instance identifiers must be explicitly coherent; "
    "missing context is not completed from neighbor references, author labels or "
    "component codes. All original references, duplicate records, conflicts and "
    "unknown scopes remain inspectable. This does not establish distinct physical "
    "copies, transformed geometry, assembly contacts or biological relevance."
)


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
    # Frozen @4 supplies bounded original syntax/operators/polymer references,
    # without pin capture or expansion. Rebind before any requested delivery.
    result = original.generation(
        _UnpinnedCard(card), structure_ref, relationship_id, False, limit, False
    )
    sources = [
        (source, binding.original.source_value(card, source))
        for source in result["sources"]
        if source["status"] in ("retained", "retained_empty")
    ]
    binding.preflight([value for _, value in sources], limit)
    reference_work = 0
    for source, value in sources:
        records, issues, state = binding.extend(
            source["component_registry"],
            source["component_input_issues"],
            value,
            source["structure_ref"],
        )
        reference_work = binding.bind(
            source, value, records, issues, state, limit, reference_work
        )
    rows = occurrences.prepare(result)
    work = occurrences.preflight(rows, expand_operations, expand_occurrences, limit)
    pin = card.pinned_ref() if card.id else None
    if pin:
        original._locations(result, pin)
    occurrences.materialize(rows, expand_operations, expand_occurrences)
    component_items = [
        item
        for source in result["sources"]
        for parent in source["assemblies"]
        for item in parent["generators"]
        if "component_input_state" in item
    ]
    result.update(
        rule=RULE,
        scope=SCOPE,
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
        component_binding_rule=binding.RULE,
        component_reference_work=reference_work,
        component_binding_summary={
            "scope": "retained_parent_bound_generators_only",
            **{
                state: sum(item["component_scope"] == state for item in component_items)
                for state in ("resolved", "partial", "unresolved")
            },
            "unavailable": sum(
                item["component_scope"] not in ("resolved", "partial", "unresolved")
                for item in component_items
            ),
        },
        occurrence_plan_summary={
            "scope": "retained_generator_declarations_only",
            **{
                state: sum(
                    item["occurrence_plan"]["status"] == state for _, item in rows
                )
                for state in ("planned", "retained_empty", "unavailable")
            },
        },
        tuple_expansion_state=original._delivery(
            result, expand_operations, occurrence=False
        ),
        occurrence_expansion_state=original._delivery(
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
