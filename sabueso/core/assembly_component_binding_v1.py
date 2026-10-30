"""Exact entry label-asym references, without physical occurrence inference.

Polymer instance records and ligand-neighbor references have different bases.
Never complete an original record, use author labels as keys, or pool assertions.
"""

from collections import Counter

from .assembly_requests import check_work

RULE = "native_entry_component_key@1"
IDENTIFIERS = "rcsb_polymer_entity_instance_container_identifiers"
ENTITY_IDS = "rcsb_polymer_entity_container_identifiers"
ROOT = ["asserted_value", "ligand_contact_inputs"]


def key(value):
    return (
        isinstance(value, str) and bool(value) and not any(c.isspace() for c in value)
    )


def source_value(card, source):
    return card.source_assertion_store.get(source["source_assertion_id"])[
        "asserted_value"
    ]


def preflight(values, limit):
    """Count all selected collections and identifier text before building a registry."""
    work = 0

    def collection(value):
        nonlocal work
        if not isinstance(value, list):
            return []
        work += len(value)
        check_work(work, limit, "component source records")
        return value

    def text(value, fields):
        nonlocal work
        if isinstance(value, dict):
            work += sum(len(value[f]) for f in fields if isinstance(value.get(f), str))
            check_work(work, limit, "component identifier text")

    for value in values:
        inputs = value.get("ligand_contact_inputs")
        if not isinstance(inputs, dict):
            continue
        for entity in collection(inputs.get("polymer_entities")):
            if not isinstance(entity, dict):
                continue
            text(entity, ("rcsb_id",))
            text(entity.get(ENTITY_IDS), ("entity_id", "entry_id"))
            for instance in collection(entity.get("polymer_entity_instances")):
                if not isinstance(instance, dict):
                    continue
                text(
                    instance.get(IDENTIFIERS),
                    ("asym_id", "auth_asym_id", "entity_id", "entry_id"),
                )
                for neighbor in collection(instance.get("rcsb_ligand_neighbors")):
                    text(neighbor, ("ligand_asym_id", "ligand_comp_id"))


def _collection(container, field, path, issues):
    if field not in container:
        issues.append(
            {"state": "not_retained", "input_path": path, "missing_field": field}
        )
        return []
    value = container[field]
    if isinstance(value, list):
        return value
    issues.append(
        {
            "state": "retained_null" if value is None else "unrecognized_shape",
            "input_path": [*path, field],
        }
    )
    return []


def _descriptors(fields):
    states, values = {}, {}
    for name, container, field in fields:
        value = container.get(field)
        states[name] = (
            "not_retained"
            if field not in container
            else "retained_null"
            if value is None
            else "retained"
            if isinstance(value, str)
            else "unrecognized_shape"
        )
        if isinstance(value, str):
            values[name] = value
    return states, values


def _identifiers(container, field, path, issues):
    value = container.get(field)
    if isinstance(value, dict):
        return value
    issue = {
        "state": "not_retained"
        if field not in container
        else "retained_null"
        if value is None
        else "unrecognized_shape",
        "input_path": path if field not in container else [*path, field],
        "role": field,
    }
    if field not in container:
        issue["missing_field"] = field
    issues.append(issue)
    return None


def registry(value, structure_ref):
    """Retain role-specific original records; neighbor references are not instances."""
    issues, by_id = [], {}
    if "ligand_contact_inputs" not in value:
        return [], [
            {
                "state": "not_retained",
                "input_path": ["asserted_value"],
                "missing_field": "ligand_contact_inputs",
            }
        ]
    inputs = value["ligand_contact_inputs"]
    if not isinstance(inputs, dict):
        return [], [
            {
                "state": "retained_null" if inputs is None else "unrecognized_shape",
                "input_path": list(ROOT),
            }
        ]

    def add(identifier, role, path, fields, entity_path=None, instance_path=None):
        if not key(identifier):
            issues.append(
                {"state": "unidentified_record", "role": role, "input_path": path}
            )
            return
        states, descriptors = _descriptors(fields)
        reasons = []
        if "unrecognized_shape" in states.values():
            reasons.append("unrecognized_descriptor_shape")
        if any(
            "pdb:" + descriptors[f] != structure_ref
            for f in ("entry_id", "entity_entry_id")
            if f in descriptors
        ):
            reasons.append("foreign_entry_identity")
        if (
            all(f in descriptors for f in ("entity_id", "instance_entity_id"))
            and descriptors["entity_id"] != descriptors["instance_entity_id"]
        ):
            reasons.append("conflicting_parent_entity_identity")
        if "entity_record_id" in descriptors:
            prefix = structure_ref.removeprefix("pdb:") + "_"
            record_id = descriptors["entity_record_id"]
            if not record_id.startswith(prefix) or len(record_id) == len(prefix):
                reasons.append("unbound_entity_record_identity")
            elif (
                "entity_id" in descriptors
                and record_id != prefix + descriptors["entity_id"]
            ):
                reasons.append("conflicting_entity_record_identity")
        reference = {
            "role": role,
            "input_path": path,
            "descriptor_states": states,
            "descriptors": descriptors,
            "reasons": reasons,
        }
        if entity_path is not None:
            reference["entity_input_path"] = entity_path
        if instance_path is not None:
            reference["instance_input_path"] = instance_path
        by_id.setdefault(identifier, []).append(reference)

    for ei, entity in enumerate(_collection(inputs, "polymer_entities", ROOT, issues)):
        ep = [*ROOT, "polymer_entities", ei]
        if not isinstance(entity, dict):
            issues.append({"state": "unrecognized_entity_shape", "input_path": ep})
            continue
        entity_ids = _identifiers(entity, ENTITY_IDS, ep, issues) or {}
        for ii, instance in enumerate(
            _collection(entity, "polymer_entity_instances", ep, issues)
        ):
            ip = [*ep, "polymer_entity_instances", ii]
            if not isinstance(instance, dict):
                issues.append(
                    {"state": "unrecognized_instance_shape", "input_path": ip}
                )
                continue
            ids = _identifiers(instance, IDENTIFIERS, ip, issues)
            if ids is not None:
                add(
                    ids.get("asym_id"),
                    "polymer_instance",
                    ip,
                    [
                        ("entity_id", entity_ids, "entity_id"),
                        ("entity_record_id", entity, "rcsb_id"),
                        ("entity_entry_id", entity_ids, "entry_id"),
                        ("instance_entity_id", ids, "entity_id"),
                        ("entry_id", ids, "entry_id"),
                        ("author_asym_id", ids, "auth_asym_id"),
                    ],
                    ep,
                )
            ids = ids or {}
            for ni, neighbor in enumerate(
                _collection(instance, "rcsb_ligand_neighbors", ip, issues)
            ):
                np = [*ip, "rcsb_ligand_neighbors", ni]
                if not isinstance(neighbor, dict):
                    issues.append(
                        {"state": "unrecognized_neighbor_shape", "input_path": np}
                    )
                    continue
                add(
                    neighbor.get("ligand_asym_id"),
                    "ligand_neighbor_reference",
                    np,
                    [
                        ("ligand_comp_id", neighbor, "ligand_comp_id"),
                        ("entity_id", entity_ids, "entity_id"),
                        ("entity_record_id", entity, "rcsb_id"),
                        ("entity_entry_id", entity_ids, "entry_id"),
                        ("instance_entity_id", ids, "entity_id"),
                        ("entry_id", ids, "entry_id"),
                    ],
                    ep,
                    ip,
                )
    records = []
    for identifier, references in sorted(by_id.items()):
        polymers = [r for r in references if r["role"] == "polymer_instance"]
        neighbors = [r for r in references if r["role"] == "ligand_neighbor_reference"]
        components = {
            r["descriptors"]["ligand_comp_id"]
            for r in neighbors
            if "ligand_comp_id" in r["descriptors"]
        }
        reasons = sorted({reason for r in references for reason in r["reasons"]})
        if len(polymers) > 1:
            reasons.append("duplicate_polymer_instance_records")
        if polymers and neighbors:
            reasons.append("conflicting_source_roles")
        if len(components) > 1:
            reasons.append("conflicting_ligand_component_references")
        records.append(
            {
                "asym_id": identifier,
                "registry_index": len(records),
                "binding_state": "ambiguous"
                if reasons
                else "resolved"
                if polymers
                else "referenced",
                "basis": "native_polymer_instance_identifier"
                if polymers and not neighbors
                else "native_ligand_neighbor_reference"
                if neighbors and not polymers
                else "conflicting_native_roles",
                "references": references,
                "reasons": reasons,
            }
        )
    return records, issues


def bind(source, value, records, issues, limit, work):
    index = {r["asym_id"]: r for r in records}
    source.update(
        component_binding_rule=RULE,
        component_key_scope="one_source_assertion_entry",
        component_registry=records,
        component_input_issues=issues,
        component_input_state="partial"
        if issues
        else "retained"
        if records
        else "retained_empty",
    )
    for parent in source["assemblies"]:
        for item in parent["generators"]:
            item["component_bindings"] = []
            if "plan" not in item:
                item["component_scope"] = (
                    "parent_scope_unbound"
                    if item["status"] == "parent_scope_unbound"
                    else "unrecognized_generator"
                )
                continue
            raw = value["assembly_generation_inputs"]["assemblies"][
                parent["assembly_index"]
            ]["pdbx_struct_assembly_gen"][item["generator_index"]]
            labels = raw.get("asym_id_list")
            item["component_input_state"] = (
                "not_retained"
                if "asym_id_list" not in raw
                else "retained_null"
                if labels is None
                else "unrecognized_shape"
                if not isinstance(labels, list)
                else "retained"
                if labels
                else "retained_empty"
            )
            if not isinstance(labels, list) or not labels:
                item["component_scope"] = item["component_input_state"]
                continue
            counts = Counter(label for label in labels if key(label))
            states = []
            for li, label in enumerate(labels):
                work += 1 + (len(label) if isinstance(label, str) else 0)
                check_work(work, limit, "component reference work")
                node = index.get(label) if key(label) else None
                state = (
                    node["binding_state"]
                    if node
                    else "unresolved"
                    if key(label)
                    else "unrecognized_label"
                )
                row = {
                    "label_index": li,
                    "state": state,
                    "input_path": [*item["input_path"], "asym_id_list", li],
                    "registry_index": node["registry_index"] if node else None,
                }
                if key(label):
                    row.update(asym_id=label, repeated=counts[label] > 1)
                item["component_bindings"].append(row)
                states.append(state)
            item["component_scope"] = (
                "resolved"
                if all(s == "resolved" for s in states)
                else "partial"
                if any(s in ("resolved", "referenced") for s in states)
                else "unresolved"
            )
    return work
