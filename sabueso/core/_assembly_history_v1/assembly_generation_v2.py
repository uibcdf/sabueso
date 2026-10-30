# Frozen from 77fd770e4d2a8fa94eea3fbd723a84fc90875efb / SDK135.
"""Frozen operator-key reconciliation; physical component membership stays uncomputed."""

from ..errors import ArgumentError
from . import assembly_generation_v1 as original
from . import assembly_operator_binding_v1 as binding
from .assembly_operations_v1 import expand, expansion_count, tuple_text_bound
from .assembly_requests import budget, check_work

RULE = "rcsb_assembly_generation@2"
SCOPE = (
    "Original generator plans plus entry-scoped native operator-key references, "
    "within each original SourceAssertion. Every retained projection remains linked; "
    "names and equal transforms never identify operators. Descriptor checks cover "
    "only retained name/type/symmetry text, not matrices or coordinates. Unrepresented "
    "references concern retained input, not source-wide absence. Declared tuples "
    "do not establish physical copies, component membership, contacts or biological relevance."
)


class _UnpinnedCard:
    """Read-only forwarding view; defer full pin capture until all work passes."""

    def __init__(self, card):
        self._card = card

    def __getattr__(self, name):
        return getattr(self._card, name)

    def pinned_ref(self):
        return None


def _location(pin, source_id, path):
    return {
        "format": "card_access_location@1",
        "kind": "card",
        "card_ref": pin,
        "snapshot_id": pin.rsplit("@", 1)[1],
        "segments": [
            {"type": "Key", "value": "source_assertion_store"},
            {"type": "Record", "value": source_id},
            *[{"type": "Index" if type(v) is int else "Key", "value": v} for v in path],
        ],
    }


def generation(
    card, structure_ref, relationship_id, expand_operations, operation_budget
):
    limit = budget(operation_budget)
    if type(expand_operations) is not bool:
        raise ArgumentError(
            "expand_operations requires a boolean.", argument="expand_operations"
        )
    result = original.generation(
        _UnpinnedCard(card), structure_ref, relationship_id, False, limit
    )
    sources = [
        (s, binding.source_arrays(card, s))
        for s in result["sources"]
        if s["status"] in ("retained", "retained_empty")
    ]
    binding.preflight(sources, limit)
    pools = [(source, *binding.registry(arrays)) for source, arrays in sources]
    comparisons = sum(
        binding.comparison_work(source, len(numeric)) for source, _, _, numeric in pools
    )
    check_work(comparisons, limit, "operator candidate checks")
    reference_text = 0
    for source, records, issues, numeric in pools:
        reference_text = binding.bind(
            source, records, issues, numeric, limit, reference_text
        )
    parsed = [item for source in result["sources"] for item in binding.plans(source)]
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
            source["source_location"] = _location(pin, ref, [])
            for parent in source["assemblies"]:
                for item in parent["generators"]:
                    item["input_location"] = _location(pin, ref, item["input_path"])
            for node in source.get("operator_registry", []):
                for projection in node["projections"]:
                    projection["input_location"] = _location(
                        pin, ref, projection["input_path"]
                    )
            for issue in source.get("operator_input_issues", []):
                issue["input_location"] = _location(pin, ref, issue["input_path"])
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
        operator_binding_rule=binding.RULE,
        operator_binding_summary={
            "scope": "retained_parsed_generators_only",
            "resolved": sum(
                item.get("operator_scope") == "resolved" for item in parsed
            ),
            "partial": sum(item.get("operator_scope") == "partial" for item in parsed),
            "unresolved": sum(
                item.get("operator_scope") == "unresolved" for item in parsed
            ),
        },
        operator_candidate_checks=comparisons,
        operator_reference_text_work=reference_text,
    )
    result["request"].update(expand_operations=expand_operations, generation_rule=RULE)
    return result
