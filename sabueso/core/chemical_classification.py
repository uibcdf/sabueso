"""Source-bound chemical classes and roles; no pharmacological inference."""

import re
from copy import deepcopy

from sabueso.mappings.molecule_identity import is_standard_inchikey

from .card_capture import _capture_cards
from .snapshot import canonical_json, digest

RULE = "chemical_classification_context@1"
FIELDS = ("annotations.chemical_classes", "annotations.chemical_roles")
FLAGS = ("biological_role", "chemical_role", "application")
SCOPE = (
    "Retained source chemical classes and roles, not target-specific activity, "
    "mechanism or therapeutic effect. Direct/inherited assignment is read only "
    "from a retained ChEBI-mapped statement with a coherent explicit focal identity. "
    "Missing retained information does not establish source/global absence."
)


def _refs(value):
    return (
        value
        if isinstance(value, list) and all(isinstance(v, str) for v in value)
        else []
    )


def _observation(statement):
    return {
        key: statement.get(key) for key in ("source", "retrieved_at", "source_metadata")
    }


def _subject(statement):
    source = statement.get("source") or {}
    if not isinstance(source, dict):
        return None
    record = source.get("record_id")
    if source.get("name") != "ChEBI" or not isinstance(record, str):
        return None
    if re.fullmatch(r"CHEBI:[1-9][0-9]*", record) is None:
        return None
    subject = "chebi:" + record.split(":", 1)[1]
    return subject if statement.get("subject_ref") == subject else None


def _identity(statement, focal, relationships, assertions):
    subject = _subject(statement)
    candidates, targets = [], set()
    if subject is None or not statement.get("retrieved_at"):
        return {
            "state": "unknown",
            "basis": "original_subject_or_observation_not_retained",
            "relationships": [],
        }
    for relationship in relationships:
        if (
            relationship.get("predicate") != "same_as"
            or relationship.get("subject_ref") != subject
        ):
            continue
        if relationship.get("qualifier_conflicts"):
            continue
        target = relationship.get("object_ref")
        for ref in _refs(relationship.get("source_assertion_ids")):
            original = assertions.get(ref) or {}
            value = original.get("asserted_value")
            if (
                original.get("field_path") == "relationships.same_as"
                and _subject(original) == subject
                and _observation(original) == _observation(statement)
                and isinstance(value, dict)
                and isinstance(target, str)
                and target.startswith("inchikey:")
                and value.get("object_ref") == target
                and value.get("inchikey") == target.removeprefix("inchikey:")
            ):
                targets.add(target)
                candidates.append(
                    {
                        "relationship_id": relationship["id"],
                        "source_assertion_id": ref,
                        "target_ref": target,
                    }
                )
    return {
        "state": "bound"
        if targets == {focal}
        else "ambiguous"
        if len(targets) > 1
        else "unknown",
        "basis": "original_source_stated_identity"
        if targets == {focal}
        else "focal_identity_not_uniquely_supported",
        "relationships": candidates,
    }


def chemical_classification(card):
    """Read original field membership with complete support and explicit gaps.

    This native reader is the scientific foundation of the planned rich chemical
    profile, not delivery or acceptance of that human explorer panel.
    """
    captures, inputs = _capture_cards(card, ())
    capture = captures[inputs[0]]
    data = capture.data
    meta = data.get("meta", {})
    card_id = meta.get("card_id")
    prefix = "sabueso:small_molecule:inchikey:"
    focal = (
        "inchikey:" + card_id[len(prefix) :]
        if isinstance(card_id, str) and card_id.startswith(prefix)
        else None
    )
    if focal is not None and not is_standard_inchikey(focal.removeprefix("inchikey:")):
        focal = None
    identifiers = data.get("sections", {}).get("identifiers")
    selected_key = (
        identifiers.get("inchikey") if isinstance(identifiers, dict) else None
    )
    if isinstance(selected_key, dict) and selected_key.get("value") not in (
        None,
        focal.removeprefix("inchikey:") if focal else None,
    ):
        focal = None
    applicable = meta.get("entity_type") == "small_molecule"
    all_assertions = {row["id"]: row for row in data["source_assertion_store"]}
    identities = [
        row for row in data["relationship_store"] if row.get("predicate") == "same_as"
    ]
    needed = {
        ref for rel in identities for ref in _refs(rel.get("source_assertion_ids"))
    }
    fields, rows = {}, []
    bindings = {}
    annotations = data.get("sections", {}).get("annotations")
    container_state = (
        "not_retained"
        if annotations is None
        else "retained"
        if isinstance(annotations, dict)
        else "unrecognized_shape"
    )
    original_container = (
        deepcopy(annotations) if not isinstance(annotations, dict) else None
    )
    if not isinstance(annotations, dict):
        annotations = {}
    for path in FIELDS:
        key = path.split(".", 1)[1]
        present = key in annotations
        node = annotations.get(key)
        value = node.get("value") if isinstance(node, dict) else None
        refs = node.get("source_assertion_ids") if isinstance(node, dict) else None
        identified = isinstance(refs, list) and all(
            isinstance(ref, str) for ref in refs
        )
        selected = refs if identified else []
        needed.update(selected)
        alternatives = [
            r["id"]
            for r in all_assertions.values()
            if r.get("field_path") == path and r["id"] not in selected
        ]
        needed.update(alternatives)
        state = (
            "unrecognized_shape"
            if container_state == "unrecognized_shape"
            else "not_retained"
            if not present
            else "unrecognized_shape"
            if not isinstance(node, dict) or "value" not in node
            else "retained_null"
            if value is None
            else "retained_empty"
            if value == []
            else "retained"
            if isinstance(value, list)
            else "unrecognized_shape"
        )
        fields[path] = {
            "state": state,
            "original_node": deepcopy(node),
            "selection_support_state": "declared"
            if identified
            else "not_retained"
            if isinstance(node, dict) and "source_assertion_ids" not in node
            else "unrecognized",
            "missing_source_assertion_ids": [
                ref for ref in selected if ref not in all_assertions
            ],
            "alternative_source_assertion_ids": alternatives,
        }
        indexes = {}
        checks = fields[path]["support_checks"] = {}
        for ref in dict.fromkeys(selected):
            original = all_assertions.get(ref) or {}
            original_values = original.get("asserted_value")
            if not original:
                checks[ref] = "source_not_retained"
                continue
            if original.get("field_path") != path:
                checks[ref] = "field_path_mismatch"
                continue
            if not isinstance(original_values, list):
                checks[ref] = "source_list_unrecognized"
                continue
            bindings.setdefault(
                ref, _identity(original, focal, identities, all_assertions)
            )
            if not applicable or focal is None or bindings[ref]["state"] != "bound":
                checks[ref] = (
                    "not_applicable"
                    if not applicable
                    else "focal_identity_unknown"
                    if focal is None
                    else "identity_" + bindings[ref]["state"]
                )
                continue
            checks[ref] = "eligible_original_list"
            for index, original_value in enumerate(original_values):
                indexes.setdefault(canonical_json(original_value), []).append(
                    {"source_assertion_id": ref, "index": index}
                )
        if not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            location = {
                "format": "card_access_location@1",
                "kind": "card",
                "card_ref": capture.pin,
                "snapshot_id": capture.snapshot,
                "segments": [
                    {"type": "Key", "value": "sections"},
                    {"type": "Key", "value": "annotations"},
                    {"type": "Key", "value": key},
                    {"type": "Key", "value": "value"},
                    {"type": "Index", "value": index},
                ],
            }
            support = indexes.get(canonical_json(item), [])
            term = item.get("chebi_id") if isinstance(item, dict) else None
            valid = (
                isinstance(term, str)
                and re.fullmatch(r"CHEBI:[1-9][0-9]*", term) is not None
            )
            supported = bool(support) and valid
            direct = item.get("direct") if isinstance(item, dict) else None
            assignment = (
                "class_membership"
                if path == FIELDS[0]
                else "direct"
                if direct is True
                else "inherited"
                if direct is False
                else "not_stated"
                if direct is None
                else "unrecognized"
            )
            rows.append(
                {
                    "row_ref": digest(canonical_json(location)),
                    "kind": "class" if path == FIELDS[0] else "role",
                    "field_path": path,
                    "index": index,
                    "location": location,
                    "value": deepcopy(item),
                    "state": "source_supported"
                    if supported
                    else "unrecognized_term"
                    if not valid
                    else "support_unknown",
                    "support_reason": "exact_original_field_member"
                    if supported
                    else "invalid_chebi_term"
                    if not valid
                    else "selected_support_not_declared"
                    if not identified or not selected
                    else "no_eligible_original_member",
                    "assignment": assignment if supported else "unknown",
                    "categories": {
                        flag: item.get(flag)
                        if isinstance(item, dict) and type(item.get(flag)) is bool
                        else None
                        for flag in FLAGS
                    }
                    if supported and path == FIELDS[1]
                    else {},
                    "source_memberships": deepcopy(support),
                    "support_grain": "Original whole-field assertions and exact matching member positions; not independently acquired per-item lineage.",
                }
            )
    quality = data.get("quality")
    quality = quality if isinstance(quality, dict) else {}

    def original_quality(key):
        value = quality.get(key)
        return (
            deepcopy(
                [r for r in value if isinstance(r, dict) and r.get("field") in FIELDS]
            )
            if isinstance(value, list)
            else deepcopy(value)
        )

    status = (
        "not_applicable"
        if not applicable
        else "missing_prerequisite"
        if focal is None
        else "ok"
        if rows
        and all(
            r["state"] == "source_supported"
            and r["assignment"] not in ("unknown", "not_stated", "unrecognized")
            for r in rows
        )
        and all(f["state"] in ("retained", "retained_empty") for f in fields.values())
        else "partial"
        if rows
        else "empty"
        if all(f["state"] == "retained_empty" for f in fields.values())
        else "unknown"
    )
    return {
        "rule": RULE,
        "scope": SCOPE,
        "card_ref": capture.pin,
        "snapshot_id": capture.snapshot,
        "focal_ref": focal,
        "status": status,
        "annotation_container_state": container_state,
        "unrecognized_annotation_container": original_container,
        "rows": rows,
        "fields": fields,
        "identity_bindings": bindings,
        "input_relationships": deepcopy(identities),
        "input_source_assertions": {
            ref: deepcopy(all_assertions[ref])
            for ref in sorted(needed)
            if ref in all_assertions
        },
        "stored_conflicts": original_quality("conflicts"),
        "stored_alternatives": original_quality("alternatives"),
        "coverage_basis": "Retained field membership only; empty/missing fields do not establish that ChEBI or other sources have no classes or roles.",
    }
