"""Readable source-bound ligand-site comparisons over one captured Card (#148).

The existing native readers own all science. This presentation has no historical
verifier yet; its result and originating navigation are explicitly unsavable.
"""

from copy import deepcopy
from dataclasses import replace

from .card_access import _Entry, _handle

TOPIC = "ligand_site_comparisons"
ADAPTER = "ligand_site_exploration@1"
LINK_RULE = "ligand_site_context_links@1"
COLUMNS = ("ligand_ref", "comparison_status", "outcome", "matched_sites", "reason")
HEADERS = (
    "Index",
    "Ligand",
    "Ligand reference",
    "Comparison",
    "Finding",
    "Matched sites",
    "Context",
)
SCOPE = (
    "One retained protein–ligand contact declaration per item, not a count of ligand "
    "molecules. Source-declared sequence numbering only; atomic proximity and sequence "
    "revision agreement are not established. Unknown comparison is not a negative "
    "overlap. Aggregated contacts, structure-local instances and assemblies remain "
    "separate contexts. Source/request coverage: explorer.view('coverage')."
)
OUTCOMES = {
    "overlaps_annotated_site": "Overlap with a retained annotated site",
    "no_annotated_overlap": "No overlap among retained comparable sites",
    "no_annotated_sites": "No annotated sites retained on this Card",
    "numbering_not_comparable": "Contact numbering is not comparable",
    "comparison_not_computed": "Comparison not computed",
}
REASONS = {
    "annotation_axis_not_canonical": "The annotation is not placed on the focal canonical sequence.",
    "annotation_positions_uncertain_or_invalid": "Annotation bounds are uncertain or invalid.",
    "annotation_sequence_revision_differs": "Annotation and reference revisions are invalid or inconsistent.",
    "canonical_identity_sequence_or_length_unavailable": "Canonical identity, sequence or length is unavailable or inconsistent.",
    "conflicting_canonical_inputs": "Canonical reference inputs conflict.",
    "conflicting_annotation_inputs": "Annotation inputs conflict.",
    "canonical_source_support_unavailable": "Canonical reference source support is unavailable.",
    "annotation_source_support_unavailable": "Annotation source support is unavailable.",
    "contact_numbering_not_comparable": "The original contact numbering is not canonical UniProt numbering.",
    "contact_positions_unstated_or_invalid": "Contact positions are unstated, uncertain or invalid.",
    "native_annotation_scope_not_retained": "The original annotation coordinate context was not retained.",
}
SITE_LABELS = {
    "active_site": "Active site",
    "binding_site": "Binding site",
    "family_site": "Family-model site",
}


def _row(item, native):
    comparison = item["comparison"]
    missing = comparison["uncomputed_annotation_indices"]
    reasons = [comparison["contact_scope"].get("reason")]
    reasons.extend(native["annotated_sites"][i]["scope"].get("reason") for i in missing)
    reasons = list(dict.fromkeys(reason for reason in reasons if reason))
    reason = " ".join(
        REASONS.get(
            code,
            "Coordinate context could not be admitted; inspect its original scope and reason code.",
        )
        for code in reasons
    )
    if item["site_class"] == "no_annotated_sites":
        reason = "No retained annotation is available for comparison; this is not external source absence."
    if not reason:
        reason = "Compared using source-declared canonical numbering; unstated revisions do not establish agreement."
    outcome = OUTCOMES.get(item["site_class"], "Unrecognized retained classification")
    if comparison["status"] == "partial":
        outcome += "; other annotations were not compared"
    matches = "; ".join(
        f"{SITE_LABELS.get(row['kind'], row['kind'])}: {row.get('description') or 'Unnamed annotation'} ({row.get('source') or 'source not retained'})"
        for row in item["annotated_overlap"]
    ) or (
        "None among comparable retained annotations"
        if comparison["status"] == "computed"
        else "Not computed"
    )
    return {
        "label": item["name"]
        if isinstance(item.get("name"), str) and item["name"]
        else item["ligand_ref"],
        "ligand_ref": item["ligand_ref"],
        "comparison_status": comparison["status"],
        "outcome": outcome,
        "matched_sites": matches,
        "reason": reason,
        "item": deepcopy(item),
    }


def _location(explorer, store, ref):
    return {
        **explorer._location(store),
        "segments": [
            {"type": "Key", "value": store},
            {"type": "Record", "value": ref},
        ],
    }


def _support(explorer, item, native):
    def references(value):
        return (
            [ref for ref in value if isinstance(ref, str)]
            if isinstance(value, list)
            else []
        )

    ids = set(native["canonical_reference"].get("inputs", []))
    ids.update(
        references(item["comparison"]["contact_scope"].get("source_assertion_ids"))
    )
    for annotation in native["annotated_sites"]:
        refs = annotation["scope"].get("field_source_assertion_ids")
        if isinstance(refs, list):
            ids.update(ref for ref in refs if isinstance(ref, str))
    relationships = {
        r["id"]: r for r in explorer.access._focal.data["relationship_store"]
    }
    for ref in item["structure_support"]["relationship_ids"]:
        ids.update(references(relationships[ref].get("source_assertion_ids")))
    return {
        "basis": "derived_ligand_site_comparison",
        "rule": deepcopy(native["classification"]),
        "coordinate_scope_rule": "ligand_site_coordinate_scope@1",
        "relationship_location": _location(
            explorer, "relationship_store", item["relationship_id"]
        ),
        "source_assertions": [explorer._statement(ref) for ref in sorted(ids)],
        "scope": "Original classification inputs; source context is not independent support for a project conclusion.",
    }


def _materialize(explorer):
    from .card_scientific_access import _CapturedCard, _rule_identity

    native, rows, explanations, support = {}, {}, {}, {}
    status, reason = "not_applicable", "Ligand-site comparisons require a protein Card."
    if explorer.profile == "protein" and not explorer.access._focal.pin:
        status, reason = (
            "missing_prerequisite",
            "A captured protein identity is required; inspect the original content.",
        )
    elif explorer.profile == "protein":
        from .ligand_explanation import _explain_ligand_site
        from .ligand_sites import ligand_sites_view

        card = _CapturedCard(explorer.access._focal)
        native = ligand_sites_view(card)
        for item in native["items"]:
            key = item["relationship_id"]
            rows[key] = _row(item, native)
            explanations[key] = _explain_ligand_site(card, key, native)
            support[key] = _support(explorer, item, native)
        status = "ok" if rows else "empty"
        reason = (
            None
            if rows
            else "No ligand contact declarations are retained; inspect source/request coverage rather than inferring no binding."
        )
    identity = deepcopy(native)
    if "classification" in identity:
        identity["classification"] = _rule_identity(identity["classification"])
    ref = _handle(
        "XR_",
        {"adapter": ADAPTER, "focal": explorer.access._focal_key, "native": identity},
    )
    for key, row in rows.items():

        def result_location(*keys):
            return {
                "format": "card_access_location@1",
                "kind": "result",
                "result_ref": ref,
                "segments": [{"type": "Key", "value": value} for value in keys],
            }

        row["support_location"] = result_location("support", key)
        row["explanation_location"] = result_location("explanations", key)
        row["interpretation"] = {
            "scope": SCOPE,
            "classification_rule": native["classification"]["rule"],
        }
    payload = {
        "context": {
            **explorer.context,
            "adapter": ADAPTER,
            "options": {},
            "used_captures": [explorer.access._focal_key],
        },
        "native_payload": native,
        "rows": rows,
        "explanations": explanations,
        "support": support,
        "scope": SCOPE,
        "outcome": {"status": status, "reason": reason},
    }
    explorer.access._objects[ref] = payload
    return ref


def view(explorer, origin):
    key = (ADAPTER, explorer.access._focal_key)
    if key not in explorer._navigation_cache:
        explorer._navigation_cache[key] = _materialize(explorer)
    ref = explorer._navigation_cache[key]
    location = {
        "format": "card_access_location@1",
        "kind": "result",
        "result_ref": ref,
        "segments": [],
    }
    payload = explorer.access._objects[ref]
    result = explorer._inspect(
        location, origin, title="Ligand contacts and annotated-site comparisons"
    )
    entries = tuple(
        _Entry(
            {
                **location,
                "segments": [
                    {"type": "Key", "value": "rows"},
                    {"type": "Key", "value": key},
                ],
            },
            key,
            row,
        )
        for key, row in sorted(
            payload["rows"].items(), key=lambda pair: (pair[1]["ligand_ref"], pair[0])
        )
    )
    return replace(
        result,
        _selection=replace(result._selection, _entries=entries),
        _selected=entries,
        _record_panel=TOPIC,
        _native_override=payload["native_payload"],
        _context_override=payload["context"],
        _status=payload["outcome"]["status"],
        _reason=payload["outcome"]["reason"],
        presentation="table",
    )


def payload(item):
    return item._view.explorer.access._objects[item._entry.location["result_ref"]]


def support(item):
    return [deepcopy(payload(item)["support"][item._entry.key])]


def explain(item):
    explorer = item._view.explorer
    location = {
        **item._entry.location,
        "segments": [
            {"type": "Key", "value": "explanations"},
            {"type": "Key", "value": item._entry.key},
        ],
    }
    result = explorer._inspect(
        location, item._view, title=f"Comparison support · {item.label}"
    )
    entries = tuple(
        _Entry(
            statement["location"],
            statement["id"],
            explorer.access._resolve(statement["location"])[0],
        )
        for statement in support(item)[0]["source_assertions"]
        if statement["state"] == "present"
    )
    return replace(
        result,
        _selection=replace(result._selection, _entries=entries),
        _selected=entries,
        _native_override=payload(item)["explanations"][item._entry.key],
        _reason="Original input statements for this comparison; missing input support remains explicit in native_payload.",
    )


def links(item):
    """Exact retained inputs and structure context, without aggregate/instance joins."""
    from .card_context_navigation import _link, _link_view

    explorer = item._view.explorer
    basis = support(item)
    rows = []
    for statement in basis[0]["source_assertions"]:
        if statement["state"] == "present":
            rows.append(
                _link(
                    explorer,
                    "source",
                    statement["id"],
                    basis,
                    location=statement["location"],
                )
            )
        else:
            rows.append(
                {
                    "role": "source",
                    "label": "Unavailable original input · " + statement["id"],
                    "target_ref": statement["id"],
                    "support": deepcopy(basis),
                    "rule": LINK_RULE,
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                    "availability": "missing_prerequisite",
                }
            )
    native = item._entry.value["item"]
    seen = set()
    for annotation in payload(item)["native_payload"].get("annotated_sites", []):
        context = annotation["scope"]
        field, index = context["field_path"], context["index"]
        if (field, index) in seen:
            continue
        seen.add((field, index))
        location = explorer._location("sections", *field.split("."), "value")
        if index is not None:
            location["segments"].append({"type": "Index", "value": index})
        link = _link(
            explorer, "annotation", explorer.access._focal.pin, basis, location=location
        )
        link["label"] = (
            "Original annotation · "
            + annotation["kind"]
            + " · "
            + str(annotation.get("description") or "Unnamed annotation")
        )
        rows.append(link)
    rel_id = native["relationship_id"]
    rows.append(
        _link(
            explorer,
            "contact",
            rel_id,
            basis,
            location=_location(explorer, "relationship_store", rel_id),
        )
    )
    rows.append(_link(explorer, "object", native["ligand_ref"], basis))
    for ref in native["structure_support"]["relationship_ids"]:
        location = _location(explorer, "relationship_store", ref)
        link = _link(
            explorer,
            "structure",
            ref,
            basis,
            location=location,
        )
        link["label"] = "Original structure context · " + ref
        rows.append(link)
        record = explorer.access._resolve(location)[0]
        conflicts = record.get("qualifier_conflicts")
        if conflicts:
            link["label"] += " · conflicting qualifiers"
        focal = payload(item)["native_payload"]["canonical_reference"]["sequence_ref"]
        if not isinstance(focal, str) or record["subject_ref"] != focal:
            continue
        qualifiers = record.get("qualifiers") or {}
        context_support = explorer._support(location)
        if "assemblies" in qualifiers:
            assembly_location = {
                **location,
                "segments": [
                    *location["segments"],
                    {"type": "Key", "value": "qualifiers"},
                    {"type": "Key", "value": "assemblies"},
                ],
            }
            assembly = _link(
                explorer,
                "assembly_context",
                record["object_ref"],
                context_support,
                location=assembly_location,
            )
            assembly["label"] = "Original assembly context · " + record["object_ref"]
            if conflicts:
                assembly["label"] += " · conflicting qualifiers"
            rows.append(assembly)
        ligands = qualifiers.get("ligands")
        for ligand_index, ligand in enumerate(
            ligands if isinstance(ligands, list) else []
        ):
            if (
                not isinstance(ligand, dict)
                or "pdb.ligand:" + str(ligand.get("comp_id")) != native["ligand_ref"]
            ):
                continue
            instances = ligand.get("instances")
            for instance_index, instance in enumerate(
                instances if isinstance(instances, list) else []
            ):
                instance_location = {
                    **location,
                    "segments": [
                        *location["segments"],
                        {"type": "Key", "value": "qualifiers"},
                        {"type": "Key", "value": "ligands"},
                        {"type": "Index", "value": ligand_index},
                        {"type": "Key", "value": "instances"},
                        {"type": "Index", "value": instance_index},
                    ],
                }
                context = _link(
                    explorer,
                    "instance_context",
                    record["object_ref"],
                    context_support,
                    location=instance_location,
                )
                context["label"] = (
                    f"Structure-local context · {record['object_ref']} · component {ligand['comp_id']} · original occurrence {instance_index + 1}"
                )
                if conflicts:
                    context["label"] += " · conflicting qualifiers"
                context["component_scope"] = {
                    "rule": LINK_RULE,
                    "component_ref": native["ligand_ref"],
                    "basis": "same source-declared PDB component only; no aggregate-to-instance correspondence or assembly projection",
                    "qualifier_conflicts": deepcopy(conflicts),
                }
                rows.append(context)
    rows = [{**row, "rule": LINK_RULE} for row in rows]
    return _link_view(
        explorer,
        rows,
        item._view,
        f"Original context for {item.label}",
        source_location=item.payload_location,
        rule=LINK_RULE,
    )
