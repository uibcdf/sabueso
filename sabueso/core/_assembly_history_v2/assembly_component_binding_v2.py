# Frozen original producer 7084894 / SDK152; shared earlier predicates stay frozen.
"""Source-bound nonpolymer instance keys, separate from physical membership.

Extend original polymer/neighbor references with independently retained native
records. Neither author labels nor component codes supply a missing native key.
"""

from collections import Counter

from .._assembly_history_v1 import assembly_component_binding_v1 as original
from .._assembly_history_v1.assembly_requests import check_work

RULE = "native_entry_component_key@2"
ROOT = ["asserted_value", "assembly_component_inputs"]
ENTITY_IDS = "rcsb_nonpolymer_entity_container_identifiers"
INSTANCE_IDS = "rcsb_nonpolymer_entity_instance_container_identifiers"
REQUIRED = (
    "entity_entry_id",
    "entity_id",
    "entity_record_id",
    "entry_id",
    "instance_entity_id",
    "instance_record_id",
)


def preflight(values, limit):
    """Bound selected nonpolymer rows/text before indexing, capture or expansion."""
    work = 0

    def collection(value):
        nonlocal work
        if not isinstance(value, list):
            return []
        work += len(value)
        check_work(work, limit, "nonpolymer source records")
        return value

    def text(container, names):
        nonlocal work
        if isinstance(container, dict):
            work += sum(
                len(container[name])
                for name in names
                if isinstance(container.get(name), str)
            )
            check_work(work, limit, "nonpolymer identifier text")

    for value in values:
        inputs = value.get("assembly_component_inputs")
        if not isinstance(inputs, dict):
            continue
        for entity in collection(inputs.get("nonpolymer_entities")):
            if not isinstance(entity, dict):
                continue
            text(entity, ("rcsb_id",))
            text(
                entity.get(ENTITY_IDS),
                ("rcsb_id", "entry_id", "entity_id", "nonpolymer_comp_id"),
            )
            for instance in collection(entity.get("nonpolymer_entity_instances")):
                if not isinstance(instance, dict):
                    continue
                text(instance, ("rcsb_id",))
                text(
                    instance.get(INSTANCE_IDS),
                    (
                        "rcsb_id",
                        "entry_id",
                        "entity_id",
                        "asym_id",
                        "auth_asym_id",
                        "auth_seq_id",
                        "comp_id",
                    ),
                )


def _inputs(value, issues):
    if "assembly_component_inputs" not in value:
        issues.append(
            {
                "state": "not_retained",
                "input_path": ["asserted_value"],
                "missing_field": "assembly_component_inputs",
            }
        )
        return [], "not_retained"
    inputs = value["assembly_component_inputs"]
    if not isinstance(inputs, dict):
        state = "retained_null" if inputs is None else "unrecognized_shape"
        issues.append({"state": state, "input_path": list(ROOT)})
        return [], state
    rows = original._collection(inputs, "nonpolymer_entities", ROOT, issues)
    raw = inputs.get("nonpolymer_entities")
    state = (
        "not_retained"
        if "nonpolymer_entities" not in inputs
        else "retained_null"
        if raw is None
        else "unrecognized_shape"
        if not isinstance(raw, list)
        else "retained"
        if raw
        else "retained_empty"
    )
    return rows, state


def _reference(
    entity,
    instance,
    entity_ids,
    ids,
    ep,
    ip,
    structure_ref,
    duplicate,
    duplicate_instance,
):
    fields = [
        ("entity_entry_id", entity_ids, "entry_id"),
        ("entity_id", entity_ids, "entity_id"),
        ("entity_record_id", entity, "rcsb_id"),
        ("entity_container_record_id", entity_ids, "rcsb_id"),
        ("entity_comp_id", entity_ids, "nonpolymer_comp_id"),
        ("entry_id", ids, "entry_id"),
        ("instance_entity_id", ids, "entity_id"),
        ("instance_record_id", instance, "rcsb_id"),
        ("instance_container_record_id", ids, "rcsb_id"),
        ("comp_id", ids, "comp_id"),
        ("author_asym_id", ids, "auth_asym_id"),
        ("author_seq_id", ids, "auth_seq_id"),
    ]
    states, descriptors = original._descriptors(fields)
    gaps = [
        name for name in REQUIRED if states[name] in ("not_retained", "retained_null")
    ]
    reasons = []
    if "unrecognized_shape" in states.values():
        reasons.append("unrecognized_descriptor_shape")
    if any(
        name in descriptors and not original.key(descriptors[name]) for name in REQUIRED
    ):
        reasons.append("invalid_native_identifier")
    entry = structure_ref.removeprefix("pdb:")
    if any(
        name in descriptors and descriptors[name] != entry
        for name in ("entity_entry_id", "entry_id")
    ):
        reasons.append("foreign_entry_identity")
    if (
        all(name in descriptors for name in ("entity_id", "instance_entity_id"))
        and descriptors["entity_id"] != descriptors["instance_entity_id"]
    ):
        reasons.append("conflicting_parent_entity_identity")
    # Check each explicit record ID against its own stated fields; never complete
    # a missing field from the ID or from a neighboring/other entity record.
    for name in ("entity_record_id", "entity_container_record_id"):
        if (
            name in descriptors
            and "entity_id" in descriptors
            and descriptors[name] != entry + "_" + descriptors["entity_id"]
        ):
            reasons.append("conflicting_entity_record_identity")
    for name in ("instance_record_id", "instance_container_record_id"):
        if name in descriptors and descriptors[name] != entry + "." + ids["asym_id"]:
            reasons.append("conflicting_instance_record_identity")
    codes = [
        descriptors[name]
        for name in ("entity_comp_id", "comp_id")
        if name in descriptors
    ]
    if any(not original.key(code) for code in codes):
        reasons.append("invalid_component_identifier")
    if len(set(codes)) > 1:
        reasons.append("conflicting_nonpolymer_component_identity")
    if duplicate:
        reasons.append("duplicate_nonpolymer_entity_records")
    if duplicate_instance:
        reasons.append("duplicate_nonpolymer_instance_record_ids")
    return {
        "role": "nonpolymer_instance",
        "input_path": ip,
        "entity_input_path": ep,
        "descriptor_states": states,
        "descriptors": descriptors,
        "identity_gaps": gaps,
        "identity_state": "ambiguous"
        if reasons
        else "incomplete"
        if gaps
        else "resolved",
        "reasons": sorted(set(reasons)),
    }


def _record_ids(record, field):
    identifiers = record.get(field)
    return {
        value
        for value in (
            record.get("rcsb_id"),
            identifiers.get("rcsb_id") if isinstance(identifiers, dict) else None,
        )
        if original.key(value)
    }


def extend(records, prior_issues, value, structure_ref):
    """Reconcile references inside one original source, retaining every basis."""
    issues = list(prior_issues)
    entities, state = _inputs(value, issues)
    by_id = {row["asym_id"]: list(row["references"]) for row in records}
    prior_reasons = {row["asym_id"]: row["reasons"] for row in records}
    record_ids = Counter(
        identifier
        for entity in entities
        if isinstance(entity, dict)
        for identifier in _record_ids(entity, ENTITY_IDS)
    )
    instance_record_ids = Counter(
        identifier
        for entity in entities
        if isinstance(entity, dict)
        for instances in [entity.get("nonpolymer_entity_instances")]
        if isinstance(instances, list)
        for instance in instances
        if isinstance(instance, dict)
        for identifier in _record_ids(instance, INSTANCE_IDS)
    )
    entity_keys = Counter(
        (ids["entry_id"], ids["entity_id"])
        for entity in entities
        if isinstance(entity, dict)
        for ids in [entity.get(ENTITY_IDS)]
        if isinstance(ids, dict)
        if original.key(ids.get("entry_id")) and original.key(ids.get("entity_id"))
    )
    for ei, entity in enumerate(entities):
        ep = [*ROOT, "nonpolymer_entities", ei]
        if not isinstance(entity, dict):
            issues.append(
                {
                    "state": "unrecognized_entity_shape",
                    "role": "nonpolymer_entity",
                    "input_path": ep,
                }
            )
            continue
        entity_ids = original._identifiers(entity, ENTITY_IDS, ep, issues) or {}
        pair = (entity_ids.get("entry_id"), entity_ids.get("entity_id"))
        duplicate = (
            any(
                record_ids[identifier] > 1
                for identifier in _record_ids(entity, ENTITY_IDS)
            )
        ) or (all(original.key(v) for v in pair) and entity_keys[pair] > 1)
        for ii, instance in enumerate(
            original._collection(entity, "nonpolymer_entity_instances", ep, issues)
        ):
            ip = [*ep, "nonpolymer_entity_instances", ii]
            if not isinstance(instance, dict):
                issues.append(
                    {
                        "state": "unrecognized_instance_shape",
                        "role": "nonpolymer_instance",
                        "input_path": ip,
                    }
                )
                continue
            ids = original._identifiers(instance, INSTANCE_IDS, ip, issues)
            duplicate_instance = any(
                instance_record_ids[identifier] > 1
                for identifier in _record_ids(instance, INSTANCE_IDS)
            )
            if duplicate_instance:
                issues.append(
                    {
                        "state": "duplicate_record_identity",
                        "role": "nonpolymer_instance",
                        "input_path": ip,
                    }
                )
            if ids is None:
                continue
            identifier = ids.get("asym_id")
            if not original.key(identifier):
                issues.append(
                    {
                        "state": "unidentified_record",
                        "role": "nonpolymer_instance",
                        "input_path": ip,
                    }
                )
                continue
            reference = _reference(
                entity,
                instance,
                entity_ids,
                ids,
                ep,
                ip,
                structure_ref,
                duplicate,
                duplicate_instance,
            )
            by_id.setdefault(identifier, []).append(reference)
    output = []
    for identifier, references in sorted(by_id.items()):
        polymers = [r for r in references if r["role"] == "polymer_instance"]
        neighbors = [r for r in references if r["role"] == "ligand_neighbor_reference"]
        nonpolymers = [r for r in references if r["role"] == "nonpolymer_instance"]
        reasons = set(prior_reasons.get(identifier, ()))
        reasons.update(reason for r in references for reason in r["reasons"])
        if len(nonpolymers) > 1:
            reasons.add("duplicate_nonpolymer_instance_records")
        if polymers and nonpolymers:
            reasons.add("conflicting_source_roles")
        codes = {
            r["descriptors"][name]
            for r in [*neighbors, *nonpolymers]
            for name in ("ligand_comp_id", "entity_comp_id", "comp_id")
            if name in r["descriptors"]
        }
        if len(codes) > 1:
            reasons.add("conflicting_ligand_component_references")
        resolved = polymers or any(
            r["identity_state"] == "resolved" for r in nonpolymers
        )
        basis = (
            "native_polymer_instance_identifier"
            if polymers
            else "native_nonpolymer_instance_identifier"
            if resolved or not neighbors
            else "native_ligand_neighbor_reference"
        )
        output.append(
            {
                "asym_id": identifier,
                "registry_index": len(output),
                "binding_state": "ambiguous"
                if reasons
                else "resolved"
                if resolved
                else "referenced"
                if neighbors
                else "unresolved",
                "basis": "conflicting_native_roles"
                if polymers and (neighbors or nonpolymers)
                else basis,
                "references": references,
                "reasons": sorted(reasons),
            }
        )
    return output, issues, state


def bind(source, value, records, issues, state, limit, work):
    work = original.bind(source, value, records, issues, limit, work)
    source.update(component_binding_rule=RULE, nonpolymer_input_state=state)
    return work
