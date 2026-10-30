"""Original RCSB generator plans, separate from physical membership or contacts.

Keep this native rule stable. Each assertion/parent/generator occurrence has its
own scope; source revisions are never pooled and no selected qualifier backfills
missing original inputs. A compact plan does not create transformed instances.
"""

import re
from collections import Counter
from copy import deepcopy

from .assembly_operations_v1 import expand, expansion_count, parse, tuple_text_bound
from .assembly_requests import budget, check_work
from .errors import ArgumentError
from .experimental_structure_admission_v1 import decision, declaration_scope

RULE = "rcsb_assembly_generation@1"
SCOPE = (
    "Symbolic source operation declarations, in original parent/generator order. "
    "Tuples are written in source product order and applied right to left. "
    "Duplicate declarations remain occurrences, not proven distinct physical copies. "
    "No physical membership, contacts, coordinates or biological relevance is computed."
    " Missing original input is not source absence; original acquisition scope "
    "remains inspectable through quality_location."
)


def generation(
    card, structure_ref, relationship_id, expand_operations, operation_budget
):
    from sabueso import __version__

    limit = budget(operation_budget)
    if type(expand_operations) is not bool:
        raise ArgumentError(
            "expand_operations requires a boolean.", argument="expand_operations"
        )
    if structure_ref is not None and (
        not isinstance(structure_ref, str)
        or not re.fullmatch(r"pdb:[A-Z0-9]{4}", structure_ref)
    ):
        raise ArgumentError(
            'structure_ref requires "pdb:<four-character id>".',
            argument="structure_ref",
        )
    if relationship_id is not None and (
        not isinstance(relationship_id, str)
        or not relationship_id.strip()
        or structure_ref is None
    ):
        raise ArgumentError(
            "relationship_id requires a nonempty id and structure_ref.",
            argument="relationship_id",
        )
    subject = declaration_scope(card)
    rows = []
    unplaced = []
    gaps = []
    pending = []
    work = 0
    for rel in card.relationship_store.store.values():
        if rel.get("predicate") != "has_structure":
            continue
        if structure_ref is not None and rel.get("object_ref") != structure_ref:
            continue
        if relationship_id is not None and rel.get("id") != relationship_id:
            continue
        admission = decision(card, rel)
        if admission["status"] != "admitted":
            unplaced.append({"relationship_id": rel["id"], "admission": admission})
            continue
        found = False
        for ref in rel.get("source_assertion_ids") or []:
            sa = card.source_assertion_store.get(ref)
            source = sa.get("source") if isinstance(sa, dict) else None
            if not isinstance(source, dict) or source.get("name") != "RCSB PDB":
                continue
            found = True
            value = sa.get("asserted_value")
            bound = (
                isinstance(value, dict)
                and sa.get("field_path") == "relationships.has_structure"
                and sa.get("subject_ref") == rel.get("object_ref")
                and value.get("object_ref") == rel.get("object_ref")
                and value.get("subject_ref") == rel.get("subject_ref")
                and isinstance(source.get("record_id"), str)
                and rel.get("object_ref") == "pdb:" + source["record_id"]
            )
            record = {
                "relationship_id": rel["id"],
                "source_assertion_id": ref,
                "structure_ref": rel.get("object_ref"),
                "status": "source_scope_unbound" if not bound else "not_retained",
                "assemblies": [],
            }
            rows.append(record)
            if not bound:
                continue
            inputs = value.get("assembly_generation_inputs")
            if "assembly_generation_inputs" not in value:
                continue
            if not isinstance(inputs, dict) or "assemblies" not in inputs:
                record["status"] = (
                    "retained_null" if inputs is None else "unrecognized_shape"
                )
                continue
            assemblies = inputs["assemblies"]
            record["retrieved_at"] = deepcopy(sa.get("retrieved_at"))
            record["entry_revision"] = deepcopy(value.get("accession_info"))
            record["status"] = (
                "retained_null"
                if assemblies is None
                else "unrecognized_shape"
                if not isinstance(assemblies, list)
                else "retained_empty"
                if not assemblies
                else "retained"
            )
            if not isinstance(assemblies, list):
                continue
            work += len(assemblies)
            check_work(work, limit, "source input")
            parent_counts = Counter(
                ids["assembly_id"]
                for assembly in assemblies
                if isinstance(assembly, dict)
                for ids in [assembly.get("rcsb_assembly_container_identifiers")]
                if isinstance(ids, dict) and isinstance(ids.get("assembly_id"), str)
            )
            for ai, assembly in enumerate(assemblies):
                parent = {
                    "assembly_index": ai,
                    "status": "unrecognized_shape",
                    "generators": [],
                }
                record["assemblies"].append(parent)
                if not isinstance(assembly, dict):
                    continue
                ids = assembly.get("rcsb_assembly_container_identifiers")
                parent_id = ids.get("assembly_id") if isinstance(ids, dict) else None
                parent_id = parent_id if isinstance(parent_id, str) else None
                parent["assembly_id"] = deepcopy(parent_id)
                parent["parent_identity"] = (
                    "unavailable"
                    if not parent_id
                    else "ambiguous"
                    if parent_counts[parent_id] > 1
                    else "source_parent_id"
                )
                operators = assembly.get("pdbx_struct_oper_list")
                parent["operator_input_state"] = (
                    "not_retained"
                    if "pdbx_struct_oper_list" not in assembly
                    else "retained_null"
                    if operators is None
                    else "unrecognized_shape"
                    if not isinstance(operators, list)
                    else "retained_empty"
                    if not operators
                    else "retained"
                )
                parent["operator_record_count"] = (
                    len(operators) if isinstance(operators, list) else None
                )
                generators = assembly.get("pdbx_struct_assembly_gen")
                parent["status"] = (
                    "not_retained"
                    if "pdbx_struct_assembly_gen" not in assembly
                    else "retained_null"
                    if generators is None
                    else "unrecognized_shape"
                    if not isinstance(generators, list)
                    else "retained_empty"
                    if not generators
                    else "retained"
                )
                if not isinstance(generators, list):
                    continue
                work += len(generators)
                check_work(work, limit, "source input")
                ordinal_counts = Counter(
                    row["ordinal"]
                    for row in generators
                    if isinstance(row, dict) and type(row.get("ordinal")) is int
                )
                for gi, generator in enumerate(generators):
                    item = {"generator_index": gi, "status": "unrecognized_shape"}
                    item["input_path"] = [
                        "asserted_value",
                        "assembly_generation_inputs",
                        "assemblies",
                        ai,
                        "pdbx_struct_assembly_gen",
                        gi,
                    ]
                    parent["generators"].append(item)
                    if not isinstance(generator, dict):
                        continue
                    item["ordinal_repeated"] = (
                        ordinal_counts[generator.get("ordinal")] > 1
                        if type(generator.get("ordinal")) is int
                        else None
                    )
                    expression = generator.get("oper_expression")
                    item["expression_state"] = (
                        "not_retained"
                        if "oper_expression" not in generator
                        else "retained_null"
                        if expression is None
                        else "retained"
                        if isinstance(expression, str)
                        else "unrecognized_shape"
                    )
                    work += len(expression) if isinstance(expression, str) else 1
                    labels = generator.get("asym_id_list")
                    if isinstance(labels, list):
                        work += len(labels)
                        check_work(work, limit, "source input")
                        work += sum(len(v) for v in labels if isinstance(v, str))
                    check_work(work, limit, "source input")
                    pending.append((item, generator, parent_id))
        if not found:
            gaps.append(
                {"relationship_id": rel["id"], "reason": "rcsb_source_not_retained"}
            )
    # Validate all source work before parsing; validate all tuple work before
    # expanding even the first generator. None never skips source admission.
    total = 0
    text_work = 0
    for item, generator, parent_id in pending:
        item.update(
            ordinal=generator.get("ordinal")
            if type(generator.get("ordinal")) is int
            else None,
            declared_assembly_id=generator.get("assembly_id")
            if isinstance(generator.get("assembly_id"), str)
            else None,
            operator_scope="not_reconciled",
        )
        if (
            not isinstance(parent_id, str)
            or not parent_id
            or generator.get("assembly_id") != parent_id
        ):
            item["status"] = "parent_scope_unbound"
            continue
        plan = parse(generator.get("oper_expression"))
        item["plan"] = plan
        item["status"] = plan["status"]
        if expand_operations and plan["status"] == "parsed":
            remaining = None if limit is None else max(0, limit - total)
            count = expansion_count(plan, remaining)
            total += count
            check_work(total, limit, "requested tuple expansion")
            text_work += tuple_text_bound(plan, count)
            check_work(
                text_work, limit, "conservative tuple text bound", upper_bound=True
            )
    for item, _, _ in pending:
        if expand_operations and item.get("status") == "parsed":
            item["operation_tuples"] = expand(item["plan"])
    incomplete = bool(unplaced or gaps) or any(
        row["status"] not in ("retained", "retained_empty")
        or any(
            parent["status"] not in ("retained", "retained_empty")
            or any(item["status"] != "parsed" for item in parent["generators"])
            for parent in row["assemblies"]
        )
        for row in rows
    )
    pin = card.pinned_ref() if card.id else None
    for row in rows:
        if pin is None:
            continue
        root = [
            {"type": "Key", "value": "source_assertion_store"},
            {"type": "Record", "value": row["source_assertion_id"]},
        ]
        location = {
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": pin,
            "snapshot_id": pin.rsplit("@", 1)[1],
            "segments": root,
        }
        row["source_location"] = location
        for parent in row["assemblies"]:
            for item in parent["generators"]:
                item["input_location"] = {
                    **location,
                    "segments": root
                    + [
                        {
                            "type": "Index" if type(value) is int else "Key",
                            "value": value,
                        }
                        for value in item["input_path"]
                    ],
                }
    return {
        "rule": RULE,
        "sabueso_version": __version__,
        "scope": SCOPE,
        "card_ref": pin,
        "status": "missing_prerequisite"
        if subject["reason"]
        else "retained"
        if rows
        else "not_retained",
        "card_subject": subject,
        "sources": rows,
        "unplaced": unplaced,
        "gaps": gaps,
        "request": {
            "structure_ref": structure_ref,
            "relationship_id": relationship_id,
            "expand_operations": expand_operations,
            "operation_budget": limit,
        },
        "physical_membership": "not_computed",
        "quality_location": {
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": pin,
            "snapshot_id": pin.rsplit("@", 1)[1],
            "segments": [{"type": "Key", "value": "quality"}],
        }
        if pin
        else None,
        "tuple_expansion_state": "not_requested"
        if not expand_operations
        else "not_available"
        if not rows
        else "incomplete"
        if incomplete
        else "expanded",
        "expanded_tuple_count": sum(
            len(item.get("operation_tuples", [])) for item, _, _ in pending
        )
        if expand_operations
        else None,
        "expanded_text_work_upper_bound": text_work if expand_operations else None,
    }
