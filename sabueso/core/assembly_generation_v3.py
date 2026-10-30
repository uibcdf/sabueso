"""Frozen component-key reconciliation, separate from physical assembly occurrences."""

from . import assembly_component_binding_v1 as binding
from . import assembly_generation_v2 as original
from .assembly_operations_v1 import expand, expansion_count, tuple_text_bound
from .assembly_requests import budget, check_work
from .errors import ArgumentError

RULE = "rcsb_assembly_generation@3"
SCOPE = (
    "Original generator plans and native operator/component keys within one "
    "entry SourceAssertion. Polymer instance records and ligand-neighbor references "
    "have distinct bases; neighbor references do not establish a complete instance "
    "record. Author labels never identify native label-asym keys. All original "
    "occurrences, ambiguities and unrepresented retained references remain visible. "
    "No physical occurrence uniqueness, transformed geometry, assembly contacts or "
    "biological relevance is computed. Missing retained input is not source absence."
)


def generation(
    card, structure_ref, relationship_id, expand_operations, operation_budget
):
    limit = budget(operation_budget)
    if type(expand_operations) is not bool:
        raise ArgumentError(
            "expand_operations requires a boolean.", argument="expand_operations"
        )
    result = original.generation(
        original._UnpinnedCard(card), structure_ref, relationship_id, False, limit
    )
    sources = [
        (s, binding.source_value(card, s))
        for s in result["sources"]
        if s["status"] in ("retained", "retained_empty")
    ]
    binding.preflight([value for _, value in sources], limit)
    reference_work = 0
    for source, value in sources:
        records, issues = binding.registry(value, source["structure_ref"])
        reference_work = binding.bind(
            source, value, records, issues, limit, reference_work
        )
    parsed = [
        item for source in result["sources"] for item in original.binding.plans(source)
    ]
    count = text = 0
    if expand_operations:
        for item in parsed:
            n = expansion_count(
                item["plan"], None if limit is None else max(0, limit - count)
            )
            count += n
            check_work(count, limit, "requested tuple expansion")
            text += tuple_text_bound(item["plan"], n)
            check_work(text, limit, "conservative tuple text bound", upper_bound=True)
    pin = card.pinned_ref() if card.id else None
    if pin:
        for source in result["sources"]:
            ref = source["source_assertion_id"]

            def locate(node, field="input"):
                node[field + "_location"] = original._location(
                    pin, ref, node[field + "_path"]
                )

            source["source_location"] = original._location(pin, ref, [])
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
    if expand_operations:
        for item in parsed:
            item["operation_tuples"] = expand(item["plan"])
    incomplete = bool(result["unplaced"] or result["gaps"]) or any(
        source["status"] not in ("retained", "retained_empty")
        or any(
            parent["status"] not in ("retained", "retained_empty")
            or any(item["status"] != "parsed" for item in parent["generators"])
            for parent in source["assemblies"]
        )
        for source in result["sources"]
    )
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
        tuple_expansion_state="not_requested"
        if not expand_operations
        else "not_available"
        if not result["sources"]
        else "incomplete"
        if incomplete
        else "expanded",
        expanded_tuple_count=count if expand_operations else None,
        expanded_text_work_upper_bound=text if expand_operations else None,
        component_binding_rule=binding.RULE,
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
        component_reference_work=reference_work,
    )
    result["request"].update(expand_operations=expand_operations, generation_rule=RULE)
    return result
