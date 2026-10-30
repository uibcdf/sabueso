# Frozen from 77fd770e4d2a8fa94eea3fbd723a84fc90875efb / SDK135.
"""Frozen source declaration combinations, never transformed physical identities."""

from .assembly_operations_v1 import expand, expansion_count, tuple_text_bound
from .assembly_requests import check_work

RULE = "source_assembly_occurrence@1"
_MAX_COUNT = 2**63 - 1
SCOPE = (
    "Component-list positions combined with source-order operation tuples, within "
    "one original assertion/parent/generator context. Repeated declarations remain "
    "occurrences; equal keys never prove distinct or identical physical copies. "
    "Key binding, declared count and delivery are separate from physical membership, "
    "coordinate transforms, assembly contacts and biological relevance."
    " Missing bindings concern retained input, not source-wide absence."
)


def prepare(result):
    """Keep exact compact factors; do not enumerate operation combinations."""
    rows = []
    for source in result["sources"]:
        for parent in source["assemblies"]:
            for item in parent["generators"]:
                context = {
                    "relationship_id": source["relationship_id"],
                    "source_assertion_id": source["source_assertion_id"],
                    "assembly_index": parent["assembly_index"],
                    "assembly_id": parent.get("assembly_id"),
                    "parent_identity": parent.get("parent_identity"),
                    "generator_index": item["generator_index"],
                    "ordinal": item.get("ordinal"),
                }
                plan = {
                    "rule": RULE,
                    "scope": "source_declarations_only",
                    "context": context,
                    "status": "unavailable",
                    "reason": None,
                    "declared_occurrence_count": None,
                    "count_state": "unavailable",
                }
                item["occurrence_plan"] = plan
                rows.append((source, item))
                if item["status"] != "parsed":
                    plan["reason"] = item["status"]
                    continue
                state = item.get("component_input_state", "not_retained")
                if state not in ("retained", "retained_empty"):
                    plan["reason"] = state
                    continue
                components = item["component_bindings"]
                if any("asym_id" not in row for row in components):
                    plan["reason"] = "unrecognized_component_labels"
                    continue
                n = item["plan"]["operation_count"]
                count = (
                    0
                    if not components
                    else n * len(components)
                    if n is not None
                    else None
                )
                count = count if count is None or count <= _MAX_COUNT else None
                plan.update(
                    status="planned" if components else "retained_empty",
                    component_count=len(components),
                    operation_count=n,
                    declared_occurrence_count=count,
                    count_state="exact" if count is not None else "factored",
                    factors={
                        "component_positions_decimal": str(len(components)),
                        "operation_groups_decimal": [
                            g["count_decimal"] for g in item["plan"]["groups"]
                        ],
                    },
                    ordering="component_then_operation_source_order",
                    application_order="right_to_left",
                )
    return rows


def preflight(rows, expand_operations, expand_occurrences, limit):
    """Count the complete request before any tuple pool, row or Card pin capture."""
    operations = occurrences = operation_text = occurrence_text = 0
    counts = []
    for _, item in rows:
        n = None
        if expand_operations and item["status"] == "parsed":
            n = expansion_count(
                item["plan"], None if limit is None else max(0, limit - operations)
            )
            operations += n
            check_work(operations, limit, "requested tuple expansion")
        c = item["occurrence_plan"].get("component_count", 0)
        if expand_occurrences and c:
            available = None if limit is None else max(0, limit - occurrences) // c
            occurrence_operations = expansion_count(item["plan"], available)
            occurrences += c * occurrence_operations
            check_work(occurrences, limit, "requested declared occurrences")
            n = occurrence_operations
        counts.append(n)
    # All cardinalities pass first. Long repeated IDs have their own visible
    # conservative text ceiling, not a claim about total result memory in bytes.
    for (_, item), n in zip(rows, counts):
        if n is None:
            continue
        if expand_operations:
            operation_text += tuple_text_bound(item["plan"], n)
            check_work(
                operation_text, limit, "conservative tuple text bound", upper_bound=True
            )
        if expand_occurrences and item["occurrence_plan"]["status"] in (
            "planned",
            "retained_empty",
        ):
            components = item["component_bindings"]
            occurrence_text += len(components) * tuple_text_bound(item["plan"], n)
            occurrence_text += n * sum(len(row["asym_id"]) for row in components)
            check_work(
                occurrence_text,
                limit,
                "conservative occurrence text bound",
                upper_bound=True,
            )
    return {
        "expanded_tuple_count": operations if expand_operations else None,
        "expanded_text_work_upper_bound": operation_text if expand_operations else None,
        "expanded_occurrence_count": occurrences if expand_occurrences else None,
        "expanded_occurrence_text_work_upper_bound": occurrence_text
        if expand_occurrences
        else None,
    }


def materialize(rows, expand_operations, expand_occurrences):
    """Expand admitted declarations only after every requested preflight passed."""
    for source, item in rows:
        admitted = item["occurrence_plan"]["status"] in ("planned", "retained_empty")
        components = item.get("component_bindings", []) if admitted else []
        tuples = (
            expand(item["plan"])
            if item["status"] == "parsed"
            and (expand_operations or (expand_occurrences and components))
            else []
        )
        if expand_operations and item["status"] == "parsed":
            item["operation_tuples"] = tuples
        if not expand_occurrences or not admitted:
            continue
        item["declared_occurrences"] = []
        operators = {r["operator_id"]: r for r in source["operator_registry"]}
        for component in components:
            for oi, operator_ids in enumerate(tuples):
                matches = [operators.get(identifier) for identifier in operator_ids]
                states = [m["binding_state"] if m else "unresolved" for m in matches]
                all_states = [component["state"], *states]
                state = (
                    "ambiguous"
                    if "ambiguous" in all_states
                    else "unresolved"
                    if "unresolved" in all_states
                    else "referenced"
                    if "referenced" in all_states
                    else "resolved"
                )
                item["declared_occurrences"].append(
                    {
                        "declaration_index": len(item["declared_occurrences"]),
                        "component_binding_index": component["label_index"],
                        "operation_tuple_index": oi,
                        "asym_id": component["asym_id"],
                        "component_state": component["state"],
                        "component_registry_index": component["registry_index"],
                        "operator_ids": list(operator_ids),
                        "operator_states": states,
                        "operator_registry_indices": [
                            m["registry_index"] if m else None for m in matches
                        ],
                        "binding_state": state,
                    }
                )
