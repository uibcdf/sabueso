"""Frozen entry-scoped operator-key binding over original RCSB projections.

Native IDs identify records within one assertion/entry context. Repeated parent
projections keep every occurrence; equal names or transforms never identify IDs.
Only the retained identity descriptors are checked, not unqueried coordinates.
"""

import re
from collections import Counter
from decimal import Decimal

from .assembly_requests import check_work

RULE = "native_entry_operator_key@1"
FIELDS = ("name", "type", "symmetry_operation")
_NUMERIC = re.compile(r"0|[1-9][0-9]*\Z")


def source_arrays(card, source):
    if source["status"] not in ("retained", "retained_empty"):
        return []
    assertion = card.source_assertion_store.get(source["source_assertion_id"])
    return assertion["asserted_value"]["assembly_generation_inputs"]["assemblies"]


def preflight(sources, limit):
    """Bound all queried descriptor work before indexing or Card pin capture."""
    work = 0
    for _, assemblies in sources:
        work += len(assemblies)
        check_work(work, limit, "operator source records")
        for assembly in assemblies:
            if not isinstance(assembly, dict):
                continue
            operators = assembly.get("pdbx_struct_oper_list")
            if not isinstance(operators, list):
                continue
            work += len(operators)
            check_work(work, limit, "operator source records")
            for operator in operators:
                if not isinstance(operator, dict):
                    continue
                work += sum(
                    len(operator[k])
                    for k in ("id", *FIELDS)
                    if isinstance(operator.get(k), str)
                )
                check_work(work, limit, "operator descriptor text")


def registry(assemblies):
    """Index exact native keys, preserving every original projection path."""
    by_id = {}
    issues = []
    for ai, assembly in enumerate(assemblies):
        path = ["asserted_value", "assembly_generation_inputs", "assemblies", ai]
        if not isinstance(assembly, dict):
            issues.append({"state": "unrecognized_parent_shape", "input_path": path})
            continue
        if "pdbx_struct_oper_list" not in assembly:
            issues.append(
                {
                    "state": "not_retained",
                    "input_path": path,
                    "missing_field": "pdbx_struct_oper_list",
                }
            )
            continue
        path = [*path, "pdbx_struct_oper_list"]
        operators = assembly["pdbx_struct_oper_list"]
        if not isinstance(operators, list):
            issues.append(
                {
                    "state": "retained_null"
                    if operators is None
                    else "unrecognized_shape",
                    "input_path": path,
                }
            )
            continue
        for oi, operator in enumerate(operators):
            origin = [*path, oi]
            identifier = operator.get("id") if isinstance(operator, dict) else None
            if (
                not isinstance(identifier, str)
                or not identifier
                or any(c.isspace() for c in identifier)
            ):
                issues.append({"state": "unidentified_record", "input_path": origin})
                continue
            node = by_id.setdefault(
                identifier, {"operator_id": identifier, "projections": []}
            )
            states = {}
            values = {}
            for field in FIELDS:
                value = operator.get(field)
                states[field] = (
                    "not_retained"
                    if field not in operator
                    else "retained_null"
                    if value is None
                    else "retained"
                    if isinstance(value, str)
                    else "unrecognized_shape"
                )
                if isinstance(value, str):
                    values[field] = value
            node["projections"].append(
                {
                    "assembly_index": ai,
                    "operator_index": oi,
                    "input_path": origin,
                    "descriptor_states": states,
                    "descriptors": values,
                }
            )
    records = []
    for identifier, node in sorted(by_id.items()):
        counts = Counter(p["assembly_index"] for p in node["projections"])
        conflicting = [
            field
            for field in FIELDS
            if len(
                {
                    p["descriptors"][field]
                    for p in node["projections"]
                    if field in p["descriptors"]
                }
            )
            > 1
        ]
        malformed = any(
            "unrecognized_shape" in p["descriptor_states"].values()
            for p in node["projections"]
        )
        reasons = []
        if any(n > 1 for n in counts.values()):
            reasons.append("duplicate_records_within_parent")
        if conflicting:
            reasons.append("conflicting_retained_descriptors")
        if malformed:
            reasons.append("unrecognized_descriptor_shape")
        node.update(
            binding_state="ambiguous" if reasons else "resolved",
            reasons=reasons,
            conflicting_fields=conflicting,
            descriptor_scope=list(FIELDS),
            basis="native_entry_operator_identifier",
            registry_index=len(records),
        )
        records.append(node)
    numeric = sorted(
        (int(Decimal(n["operator_id"])), n["registry_index"])
        for n in records
        if _NUMERIC.fullmatch(n["operator_id"])
    )
    return records, issues, numeric


def plans(source):
    for parent in source["assemblies"]:
        for item in parent["generators"]:
            if item.get("status") == "parsed":
                yield item


def comparison_work(source, numeric_count):
    return sum(
        1 if term["kind"] == "id" else numeric_count
        for item in plans(source)
        for group in item["plan"]["groups"]
        for term in group["terms"]
    )


def bind(source, records, issues, numeric, limit, text_work):
    """Resolve compact references without expanding missing numeric ranges."""
    index = {node["operator_id"]: node["registry_index"] for node in records}
    source.update(
        operator_binding_rule=RULE,
        operator_key_scope="one_source_assertion_entry",
        operator_registry=records,
        operator_input_issues=issues,
        operator_input_state="partial"
        if issues
        else "retained"
        if records
        else "retained_empty",
    )
    for item in plans(source):
        bindings = []
        unresolved = 0
        resolved = 0
        for group in item["plan"]["groups"]:
            terms = []
            for term in group["terms"]:
                if term["kind"] == "id":
                    matches = [index[term["id"]]] if term["id"] in index else []
                    count = 1
                else:
                    begin, end = int(Decimal(term["begin"])), int(Decimal(term["end"]))
                    count = end - begin + 1
                    matches = [i for value, i in numeric if begin <= value <= end]
                text_work += sum(len(records[i]["operator_id"]) for i in matches)
                check_work(text_work, limit, "operator reference text")
                good = sum(records[i]["binding_state"] == "resolved" for i in matches)
                missing = count - len(matches)
                bad = count - good
                terms.append(
                    {
                        "reference": dict(term),
                        "state": "resolved"
                        if not bad
                        else "partial"
                        if good
                        else "unresolved",
                        "reference_count_decimal": format(Decimal(count), "f"),
                        "identified_count": len(matches),
                        "resolved_count": good,
                        "unrepresented_count_decimal": format(Decimal(missing), "f"),
                        "unrepresented_scope": "retained_operator_records_only",
                        "matches": [
                            {
                                "operator_id": records[i]["operator_id"],
                                "registry_index": i,
                                "binding_state": records[i]["binding_state"],
                            }
                            for i in matches
                        ],
                    }
                )
                resolved += good
                unresolved += bad
            bindings.append({"terms": terms})
        item["operator_bindings"] = bindings
        item["operator_scope"] = (
            "resolved" if not unresolved else "partial" if resolved else "unresolved"
        )
    return text_work
