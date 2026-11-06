"""Bounded text/HTML previews. Full values are accessed through explicit objects."""

from html import escape


def preview(value, limit=120):
    """Never traverse/copy containers merely to abbreviate their display."""
    if isinstance(value, dict):
        return f"{len(value)} fields"
    if isinstance(value, (list, tuple)):
        return f"{len(value)} items"
    if value is None:
        return "null (retained)"
    if value is False:
        return "False"
    if isinstance(value, str) and value == "":
        return "'' (empty text)"
    if isinstance(value, str):
        return value[:limit] + ("…" if len(value) > limit else "")
    return str(value)[:limit]


def _ligand_reading(view, reading):
    """Readable literal destinations; original item labels/indices stay intact."""

    def scalar(field):
        return (
            preview(field["value"])
            if field["state"] in ("retained", "retained_empty", "retained_null")
            else field["state"].replace("_", " ")
        )

    lines = [
        f"Original ligand context · {preview(reading['structure_ref'])}",
        reading["scope"],
        f"{reading['level'].capitalize()}: {reading['state'].replace('_', ' ')}.",
    ]
    if (
        reading["level"] in ("components", "instances")
        and reading["entry_count"] is not None
    ):
        lines.append(
            f"Selected original entries: {reading['entry_count']} of {reading['node_entry_count']}. "
            "Display selection/order is preserved; entry numbers are original list indices."
        )
    for entry in reading["entries"]:
        if reading["level"] in ("components", "component"):
            instances = entry["instances"]
            lines.append(
                f"Original component entry {entry['index']}: "
                f"{scalar(entry['component_id'])} · {scalar(entry['description'])} · "
                f"instances: {instances['count'] if instances['count'] is not None else instances['state'].replace('_', ' ')} · "
                f"investigation flag: {scalar(entry['investigation_flag'])}"
            )
        else:
            from .card_access import _Entry
            from .card_ligand_instances_v1 import preview as instance_preview

            value, _ = view.explorer.access._resolve(entry["location"])
            text = (
                instance_preview(
                    view.explorer, _Entry(entry["location"], str(entry["index"]), value)
                )
                if isinstance(value, dict)
                else preview(value)
            )
            component = reading["component"]
            lines.append(
                f"Original instance entry {entry['index']}: component "
                f"{scalar(component['component_id'])} · instance "
                f"{scalar(entry['instance_id'])} · {text}"
            )
    if not reading["entries_complete"]:
        total = reading["entry_count"]
        lines.append(
            f"Showing {len(reading['entries'])} of {total} original entries; "
            "ligand_reading['entries'] contains all."
            if total is not None
            else "Original entry count is unknown; inspect native_payload."
        )
    lines.append(
        "Open a component, then its 'instances' field to inspect each occurrence. "
        "Original item labels and indices are unchanged. ligand_reading gives "
        "exact locations for explorer.inspect(locator=...) and bounded access.read(...); "
        "items()[i].explain() retains original support and back() returns to the original path."
    )
    return lines


def _opening(view):
    data = view.explorer.access._focal.data
    names = data.get("sections", {}).get("names", {})
    name = names.get("canonical_name", {}) if isinstance(names, dict) else None
    if isinstance(name, dict):
        name = name.get("value")
    lines = [preview(name)] if name else []
    lines.append(f"{view.explorer.profile} · captured Card")
    if view.explorer.profile == "protein":
        from .card_protein_exploration import field_entries, node

        gaps = {row["field"]: row["state"] for row in field_entries(view.explorer)[1]}

        for path, label in (
            ("annotations.organism", "Organism"),
            ("identifiers.uniprot", "UniProt accession"),
            ("sequence.length", "Sequence length"),
            ("annotations.function", "Function description"),
            ("annotations.catalytic_activity", "Catalytic activity"),
        ):
            value = node(view.explorer, path)
            if isinstance(value, dict) and "value" in value:
                lines.append(
                    f"{label}: {_field_text(path, value['value'])} · {_attribution(view.explorer, path)}"
                )
            elif path in ("annotations.function", "annotations.catalytic_activity"):
                lines.append(
                    f"{label}: "
                    + (
                        "unrecognized retained field; inspect the original content."
                        if gaps.get(path) == "unrecognized_shape"
                        else "not retained; no function is inferred from the name."
                    )
                )
        lines.append(
            f"Captured schema {preview(data.get('meta', {}).get('schema_version'))}; current sources have not been queried."
        )
        lines.append(
            "Start: items()[i].open() or explorer.questions(). All stored content: explorer.inspect()."
        )
    if view.explorer.profile in ("small_molecule", "disease"):
        from .card_protein_exploration import node

        fields = (
            (
                ("identifiers.inchikey", "Standard InChIKey"),
                ("properties.physchem.formula", "Molecular formula"),
                ("identifiers.smiles", "SMILES"),
            )
            if view.explorer.profile == "small_molecule"
            else (
                ("identifiers.mondo", "MONDO identifier"),
                ("annotations.definition", "Ontology definition"),
                ("names.synonyms", "Scoped synonyms"),
            )
        )
        for path, label in fields:
            value = node(view.explorer, path)
            if isinstance(value, dict) and "value" in value:
                lines.append(
                    f"{label}: {_field_text(path, value['value'])} · {_attribution(view.explorer, path)}"
                )
            else:
                lines.append(
                    f"{label}: no supported retained field value; inspect original content."
                )
        if view.explorer.profile == "small_molecule":
            lines.append(
                "Explore source-stated chemical identity and retained properties. No chemical calculation or target-context acquisition is performed."
            )
        else:
            lines.append(
                "Ontology terminology, not a diagnosis. Parent relationships and equivalent identifiers are separate routes; destination Cards are not opened here."
            )
        lines.append(
            f"Captured schema {preview(data.get('meta', {}).get('schema_version'))}; current sources have not been queried."
        )
        lines.append(
            "Start: items()[i].open() or explorer.questions(). All stored content: explorer.inspect()."
        )
    lines.append(
        f"{len(data.get('source_assertion_store', []))} retained source statements · "
        f"{len(data.get('relationship_store', []))} retained relationships"
    )
    quality = data.get("quality", {})
    if isinstance(quality, dict) and quality.get("conflicts"):
        lines.append(
            "Stored conflicts are present. Inspect explorer.view('quality') or original coverage/quality records."
        )
    return lines


def _field_text(path, value):
    """Bounded formatting of declared fields, never a generated interpretation."""
    if value is None:
        return "unknown (retained null)"
    if path.startswith("features_positional.") and isinstance(value, list):
        from .card_protein_source_render import feature

        return (
            "; ".join(feature(row) for row in value[:2])
            + (f" … ({len(value)} annotations)" if len(value) > 2 else "")
            if value
            else "[] (retained empty annotation list)"
        )
    if path == "annotations.definition" and isinstance(value, dict):
        return (
            preview(value.get("text"))
            + " · references: "
            + preview(value.get("references"))
        )
    if path == "names.synonyms" and isinstance(value, list):
        from .card_exploration_labels import synonym_scope

        return "; ".join(
            f"{preview(row.get('name'))} ({preview(synonym_scope(row.get('kind')))})"
            if isinstance(row, dict)
            else preview(row)
            for row in value[:2]
        ) + (f" … ({len(value)} total)" if len(value) > 2 else "")
    if path == "annotations.catalytic_activity" and isinstance(value, list):
        parts = []
        for record in value[:2]:
            if isinstance(record, dict):
                parts.append(
                    " · ".join(
                        f"{label}: {preview(record[key])}"
                        for key, label in (
                            ("ec_number", "EC"),
                            ("reaction", "Reaction"),
                            ("rhea_id", "Rhea"),
                        )
                        if key in record
                    )
                    or preview(record)
                )
            else:
                parts.append(preview(record))
        return (
            "; ".join(parts) + (f" … ({len(value)} total)" if len(value) > 2 else "")
            if value
            else "[] (retained empty list)"
        )
    if isinstance(value, list):
        return (
            "; ".join(preview(item) for item in value[:2])
            + (f" … ({len(value)} total)" if len(value) > 2 else "")
            if value
            else "[] (retained empty list)"
        )
    return preview(value) + (
        " residues" if path == "sequence.length" and type(value) is int else ""
    )


def _selected_references(field):
    """A malformed member invalidates the selection declaration as a whole."""
    if not isinstance(field, dict) or "source_assertion_ids" not in field:
        return None, "selection references not retained"
    refs = field["source_assertion_ids"]
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        return None, "unrecognized selection references"
    return refs, None


def _attribution(explorer, path, field=None):
    """Show actual retained attribution; no credit for an unretained assertion."""
    from .card_protein_exploration import node

    field = node(explorer, path) if field is None else field
    refs, reason = _selected_references(field)
    if refs is None:
        return (
            "source attribution not retained"
            if reason == "selection references not retained"
            else f"source attribution unknown: {reason}"
        )
    names = []
    missing = False
    for ref in refs[:4]:
        if isinstance(ref, str):
            statement = explorer._statement(ref)
            if statement["state"] != "present":
                missing = True
                continue
            record, _ = explorer.access._resolve(statement["location"])
            source = record.get("source", {})
            name = source.get("name") if isinstance(source, dict) else None
            if isinstance(name, str) and name not in names:
                names.append(name)
    return (
        (
            ", ".join(preview(name, 50) for name in names[:3])
            or "source attribution not retained"
        )
        + ("; some support not retained" if missing else "")
        + (f"; {len(refs)} support references, see explain()" if len(refs) > 4 else "")
    )


def _method(explorer, field):
    refs, reason = _selected_references(field)
    if refs is None:
        return f"selected-source method unknown: {reason}"
    methods = []
    missing = False
    for ref in refs[:4]:
        statement = explorer._statement(ref)
        if statement["state"] != "present":
            missing = True
            continue
        record, _ = explorer.access._resolve(statement["location"])
        metadata = record.get("source_metadata") or {}
        method = metadata.get("method") if isinstance(metadata, dict) else None
        if isinstance(method, str) and method not in methods:
            methods.append(method)
    partial = (
        f"partial preview: 4 of {len(refs)} references; inspect explain()"
        if len(refs) > 4
        else None
    )
    if methods:
        return " · ".join(
            [
                "selected-source method: "
                + ", ".join(preview(value) for value in methods),
                *(["some supporting records not retained"] if missing else []),
                *([partial] if partial else []),
            ]
        )
    if missing:
        return "selected-source method unknown: supporting records not retained" + (
            f" · {partial}" if partial else ""
        )
    if partial:
        return f"selected-source method unknown: {partial}"
    return "method not stated in selected support"


def _region_text(native):
    chains = native.get("complete_chains")
    if chains is None:
        return "region coordinate annotations not retained"
    return (
        "complete chains in retained coordinate annotations: "
        + (", ".join(preview(chain, 30) for chain in chains[:4]) if chains else "none")
        + (f" … ({len(chains)} total)" if len(chains) > 4 else "")
    )


def _requested_positions(region):
    """Format already normalized positions; inspect only a bounded prefix.

    Sorted uniqueness belongs to request validation. A contiguous normalized
    request can therefore use its endpoints without scanning a large list.
    """
    count = len(region)
    if region[-1] - region[0] + 1 == count:
        text = str(region[0]) if count == 1 else f"{region[0]}–{region[-1]}"
    else:
        prefix = region[:12]
        spans = []
        begin = end = prefix[0]
        for position in prefix[1:]:
            if position == end + 1:
                end = position
            else:
                spans.append(str(begin) if begin == end else f"{begin}–{end}")
                begin = end = position
        spans.append(str(begin) if begin == end else f"{begin}–{end}")
        text = ", ".join(spans) + (" …" if count > len(prefix) else "")
    return f"{text} ({count} {'position' if count == 1 else 'positions'})"


def _declared_ranges(view, item):
    """Show literal retained spans, never infer coordinate/reference agreement."""
    support = view._selection._scientific.wire["support"].get(item._entry.key, {})
    location = support.get("relationship_location")
    if location is None:
        return "original declaration not retained"
    relationship, _ = view.explorer.access._resolve(location)
    conflicts = relationship.get("qualifier_conflicts") or {}
    if isinstance(conflicts, dict) and "ranges" in conflicts:
        return "conflicting declarations; inspect explain()"
    ranges = (relationship.get("qualifiers") or {}).get("ranges")
    if ranges is None:
        return "not retained"
    if not isinstance(ranges, list):
        return "retained value: " + preview(ranges, 80)
    if not ranges:
        return "empty retained list"
    spans = []
    for pair in ranges[:4]:
        if (
            isinstance(pair, (list, tuple))
            and len(pair) == 2
            and all(type(value) is int for value in pair)
        ):
            spans.append(str(pair[0]) if pair[0] == pair[1] else f"{pair[0]}–{pair[1]}")
        else:
            spans.append("retained value: " + preview(pair, 24))
    return preview(
        (f"{len(ranges)} retained ranges; " if len(ranges) > 4 else "")
        + ", ".join(spans)
        + (" …" if len(ranges) > 4 else "")
    )


def _coordinate_reason(reason):
    if reason == "original_polymer_inputs_unavailable":
        return "the original experimental mapping inputs were not retained"
    if reason in {
        "canonical_identity_sequence_or_length_unavailable",
        "canonical_source_support_unavailable",
        "native_canonical_value_differs",
        "conflicting_canonical_source_values",
    }:
        return (
            "the retained sequence or identity lacks matching original source support"
        )
    if reason in {
        "conflicting_canonical_inputs",
        "invalid_or_conflicting_canonical_revision",
    }:
        return "the reference sequence, identity or revision is conflicting or invalid"
    if reason in {
        "structure_source_support_unavailable",
        "structure_source_scope_incompatible",
        "native_structure_source_differs",
    }:
        return "original experimental support is missing or belongs to a different source scope"
    if reason in {
        "recorded_coordinate_projection_differs",
        "conflicting_coordinate_qualifiers",
        "conflicting_original_coordinate_projections",
    }:
        return "the retained residue projection conflicts with its original inputs"
    return "the original experimental residue numbering is incomplete, ambiguous or invalid"


def _regional_reading(reading):
    lines = [
        f"Coordinates for this region: {len(reading['region'])} requested canonical positions.",
        "Sequence axis: "
        + (
            preview(reading["sequence_ref"])
            if reading["sequence_ref"] is not None
            else "not retained in the original coordinate basis"
        ),
    ]
    basis = reading["coordinate_basis"]
    if basis["status"] == "comparable":
        lines.append(
            "Original source-declared numbering was admitted; agreement of structure/reference revisions is not established."
        )
    elif basis["status"] == "not_retained":
        lines.append(
            "Coordinate admission was not retained in this historical result. Its reported regional values remain original; no current coordinate calculation is performed."
        )
    else:
        lines.append(
            "Original regional comparison is uncomputed: "
            + _coordinate_reason(basis["reason"])
            + "."
        )
    complete = reading["complete_chains"]
    lines.append(
        "Chains covering every requested position in the original result: "
        + (
            "not computed"
            if complete is None
            else ", ".join(preview(chain, 30) for chain in complete[:6])
            + (f" … ({len(complete)} total)" if len(complete) > 6 else "")
            if complete
            else "none among the recorded chains"
        )
        + "."
    )
    chains = reading["chains"]
    for row in chains[:6]:
        count = row["missing_count"]
        lines.append(
            f"Chain {preview(row['chain'], 40)}: "
            + (
                "regional gaps not computed"
                if count is None
                else f"{count} requested positions without coordinates in the original result"
            )
            + (
                "; original author numbering is inspectable."
                if row["numbering_location"] is not None
                else "; original author numbering is not retained for this chain."
            )
        )
    count = reading["chain_count"]
    if count is not None and count > 6:
        lines.append(
            f"Showing 6 of {count} chain records; regional_reading['chains'] contains all."
        )
    if not chains:
        lines.append(
            "No per-chain regional rows are available; unknown coordinates are not missing residues or evidence of no supporting structures."
        )
    lines.append(
        "Original assembly declarations: "
        + {
            "retained": "retained records",
            "retained_empty": "explicitly empty list",
            "retained_null": "retained null value",
            "not_retained": "not retained",
            "unrecognized_shape": "retained with an unrecognized shape",
            "unrecognized_parent_shape": "parent qualifiers have an unrecognized shape",
        }[reading["assembly_context"]["state"]]
        + ". Chain/contact membership of an assembly is not computed."
    )
    lines.append(
        "Use related() for original numbering, assemblies and sources; regional_reading contains exact locations for every chain's full recorded gaps."
    )
    return lines


def _structural_support(context):
    native, support = context["native"], context["support"]
    status = native.get("status")
    lines = [
        f"Why this structure is shown: {preview(native.get('structure_ref'))}",
        "Inventory outcome: "
        + (
            "grouped by retained structural state; this is not a structure recommendation."
            if status == "grouped"
            else preview(status)
            if status is not None
            else "not retained"
        ),
    ]
    if native.get("reason") is not None:
        lines.append("Original inventory reason: " + preview(native["reason"]))
    rule = native.get("rule", {})
    lines.append("Explanation rule: " + preview(rule.get("rule")))
    rules = native.get("rules", [])
    lines.append(
        "Original classification rules: "
        + ", ".join(preview(row.get("rule"), 90) for row in rules[:4])
        + (f" … ({len(rules)} total)" if len(rules) > 4 else "")
    )
    options = context["options"]
    region = options.get("region")
    lines.append(
        f"Scientific options: include fragments = {preview(options['include_fragments'])}; "
        + (
            "no region restriction."
            if region is None
            else "canonical region positions "
            + ", ".join(preview(value, 20) for value in region[:12])
            + (f" … ({len(region)} total)" if len(region) > 12 else "")
        )
    )
    item = native.get("item") or {}
    coordinate = item.get("coordinate_scope")
    if isinstance(coordinate, dict):
        if coordinate["status"] == "comparable":
            lines.append(
                "Comparison uses the source-declared accession axis and the retained source-backed sequence; the structure-reference revision is not stated."
            )
        else:
            lines.append(
                "Residue comparison not computed: "
                + _coordinate_reason(coordinate.get("reason"))
                + ". Open related() for the original declaration and source inputs; unknown completeness is not missing residues."
            )
    state = item.get("state") or {}
    labels = {
        "method": "Method",
        "coverage": "Sequence coverage class",
        "sequence": "Sequence state",
        "ligands": "Ligand state",
        "oligomer": "Oligomer state",
        "in_complex": "Complex state",
    }
    for key, label in labels.items():
        value = state.get(key)
        lines.append(f"{label}: {'unknown' if value is None else preview(value)}")
    if item.get("qualifier_conflicts"):
        lines.append(
            "Unresolved qualifier conflicts are retained; inspect native_payload['item']['qualifier_conflicts']."
        )
    missing = sum(
        row["state"] == "not_retained" for row in support["source_assertions"]
    )
    if missing:
        lines.append(f"{missing} relationship source records not retained.")
    elif not support["source_assertion_ids"]:
        lines.append("No source references are declared for this relationship.")
    lines.extend(
        [
            "Source records support the stored structure relationship, not individual qualifiers or the derived grouping.",
            "Sequence coverage does not establish coordinate completeness. Full group members, reference context and rules remain in native_payload.",
        ]
    )
    return lines


def _component_link_preview(view, link):
    """Short actions over retained findings; full instructions stay in the link."""
    if (
        "component_request" not in link
        and link.get("rule") != "assembly_component_detail_links@1"
    ):
        return None
    from .card_assembly_component_context_v1 import (
        ASSEMBLY_RULE,
        DETAIL_RULE,
        LIST_RULE,
        STATES,
    )

    label, state = link["label"], []
    if link.get("rule") == DETAIL_RULE:
        actions = {
            "component_binding": "Inspect declared position",
            "native_key": "Inspect key, gaps and conflicts",
            "component_record": "Read original input record",
            "source": "Read supporting source record",
            "original_declaration": "Read original generator",
        }
        action = actions.get(link.get("role"))
        if (
            action is None
            or link["availability"] != "available"
            or len(link["candidates"]) != 1
        ):
            return None
    elif link.get("rule") == LIST_RULE:
        request = link["component_request"]
        wire = view.explorer.access._objects[request["result_ref"]]
        binding = wire["rows"][request["row_key"]]["item"]["component_bindings"][
            request["component_index"]
        ]
        # These are original findings, not a new native evaluation or identity join.
        status = STATES.get(binding["state"], binding["state"])
        state.append(preview(status))
        suffix = f" · {status}"
        if binding.get("repeated"):
            state.append("Repeated declaration label")
            suffix += " · repeated declaration label"
        # Move only the original generated suffix into the state column. Keep
        # descriptors literal, even if they contain words resembling a state.
        if label.endswith(suffix):
            label = label[: -len(suffix)]
        action = "Open exact position"
    elif link.get("rule") == ASSEMBLY_RULE and link.get("role") == "components":
        action = "Open declared positions"
    else:
        action = preview(link["component_request"]["reason"], 240)
    return preview(label), " · ".join([*state, preview(link["availability"]), action])


def _presentation_ancestors(view, *, include_details=False):
    """Follow only presentation steps within one original result and request."""
    while True:
        yield view
        operation = view._display_request
        display = isinstance(operation, dict) and operation.get("operation") in (
            "filter",
            "sort",
            "presentation",
        )
        previous = view._origin
        if (
            previous is None
            or not (display or (include_details and view._focus is not None))
            or previous.result_ref != view.result_ref
            or previous._request != view._request
        ):
            return
        view = previous


def _parts(view):
    opening = _opening(view) if view.title == "Card overview" else []
    if view._explorer.mode == "saved":
        opening.insert(
            0,
            "Saved exploration · retained values, sources and navigation; no scientific recomputation.",
        )
    if view.outcome["reason"]:
        opening.append(view.outcome["reason"])
    from .card_display_filter_v2 import marked

    if any(marked(parent._display_request) for parent in _presentation_ancestors(view)):
        opening.append(
            f"Display filter: {len(view._selected)} matching retained items. "
            f"Underlying scientific status remains {preview(view.outcome['status'])}."
        )
    if (
        view._link_panel
        and view._selected
        and view._selected[0].value.get("rule") == "assembly_component_list_links@1"
    ):
        opening.append(
            "Open a position to inspect identifiers, gaps/conflicts and original records. Repeated labels stay separate; matched keys do not establish physical copies."
        )
        if view.explorer.mode == "saved":
            opening.append(
                "Only retained destinations can reopen; an unvisited link reports not_saved."
            )
    if view.request is not None:
        request = view.request
        opening.append(f"Question: {request['question']}")
        if request["question"] == "region_coverage":
            original = view
            for original in _presentation_ancestors(view, include_details=True):
                pass
            question_origin = original._origin
            if (
                question_origin is not None
                and question_origin._link_panel
                and (
                    question_origin.native_payload.get("rule")
                    == "retained_context_links@5"
                    or (
                        question_origin.native_payload.get("rule")
                        == "retained_context_links@6"
                        and any(
                            row.get("model_context", {}).get("rule")
                            == "model_fragment_structure_request@2"
                            for row in question_origin.native_payload.get("links", [])
                        )
                    )
                )
            ):
                from .card_model_fragment_regions_v1 import SCOPE

                opening.append(SCOPE)
            if (
                question_origin is not None
                and question_origin._link_panel
                and question_origin.native_payload.get("rule")
                == "retained_context_links@8"
            ):
                for row in question_origin.native_payload.get("links", []):
                    if row.get("role") == "question":
                        opening.append(row["model_context"]["reason"])
            options = request["options"]
            region = options["region"]
            opening.append(f"Sequence axis: {preview(options['sequence_ref'])}")
            if region:
                opening.append("Positions: " + _requested_positions(region))
                opening.append(
                    "Declared ranges retain source statements. Regional coordinate "
                    "completeness requires the original mapping inputs and is shown separately."
                )
    if view._record_panel == "coverage" and view.explorer._coverage_result.native:
        opening.append(
            "Classification: "
            + view.explorer._coverage_result.native["rule"]["rule"]
            + "; source/request states remain distinct. Unknown counts are not zero; no global completeness score is inferred."
        )
    if view._record_panel == "assembly_generation":
        from .card_assembly_dispatch import presentation

        assembly = presentation(view)
        SCOPE, detail_lines = assembly.SCOPE, assembly.detail_lines

        opening.append(SCOPE)
        opening.append(
            "Open an item for its complete original context; explain() shows the basis and related() opens input/source destinations. Save this exploration to preserve its original findings, requests and navigation."
        )
        opening.extend(detail_lines(view, preview))
    if view._record_panel == "quaternary_interpretation":
        if view._explorer.mode == "saved":
            from .card_quaternary_history_v1 import SCOPE
        else:
            from .card_quaternary_exploration import SCOPE

        opening.append(SCOPE)
        opening.append(
            "Saving retains the original interpretation, input statements and supported navigation for independent reading."
        )
        if view.presentation == "detail" and view._selected:
            opening.append(
                f"Finding kind: {view._selected[0].value['kind']}. Full original scientific result: native_payload; original statements: explain()."
            )
    if view._record_panel == "ligand_site_comparisons":
        if view._explorer.mode == "saved":
            from .card_ligand_site_history_v1 import SCOPE
        else:
            from .card_ligand_site_exploration import SCOPE

        opening.append(SCOPE)
        opening.append(
            "Saving preserves the original comparison, sources and navigation for verified independent reading."
        )
        if view.presentation == "detail" and view._selected:
            native = view._selected[0].value["item"]
            opening.append(
                f"Recorded contact positions: {preview(native['recorded_residues'], 200)}. Full original values: native_payload."
            )
    if view._field_panel:
        opening.append(
            "Retained fields with original support; source coverage is not evaluated. Open explain() to review source records and stored alternatives."
        )
        from .card_ligand_instances_v1 import SUMMARY as INSTANCE_SUMMARY
        from .card_protein_source_v1 import SCOPES

        if view._field_panel == "ligand_instances":
            opening.append(INSTANCE_SUMMARY)
        elif view._field_panel == "quaternary_structure":
            from .card_quaternary_source_v1 import SCOPE

            opening.append(SCOPE)
            gaps = view.native_payload.get("field_gaps", [])
            counts = {
                state: sum(gap.get("state") == state for gap in gaps)
                for state in ("not_retained", "retained_empty", "unrecognized_shape")
            }
            if any(counts.values()):
                opening.append(
                    f"Declaration gaps: {counts['not_retained']} not retained, {counts['retained_empty']} explicitly empty, {counts['unrecognized_shape']} unrecognized. These describe captured content, not external source absence."
                )
        elif view._field_panel == "annotated_regions":
            opening.append(
                "Choose an annotation, then related() to inspect its structural question and original inputs. Unknown scope remains visible; no source query is made."
            )
        elif view._field_panel in SCOPES:
            opening.append(SCOPES[view._field_panel])
    from .card_exploration_labels import (
        explanation_context,
        relationship_basis,
        source_record,
        structural_explanation,
    )

    structural = structural_explanation(view)
    if structural is not None:
        opening.extend(_structural_support(structural))
        opening.append(
            "Open a source record below; back() returns to your structural selection."
            if len(view.items()) and source_record(view.items()[0])
            else "Return with back() and open the structure's related() links to follow original sources; retained detail remains inspectable."
        )
    original_support = explanation_context(view)
    if "selection_support_state" in original_support or any(
        "source_assertion_ids" in support
        for support in original_support.get("support", [])
    ):
        opening.append(
            "Source roles describe the original retained selection, not source reliability."
        )
        if original_support.get("selection_support_state") == "declared":
            opening.append(
                "Alternative statements are other retained statements for this field; they can agree with the selected value and do not replace it."
            )
        if original_support.get("selection_support_state") in (
            "not_retained",
            "unrecognized",
        ):
            opening.append(
                "Selection references are missing or unrecognized; field statements have no assigned selection role."
            )
        missing = sum(
            statement.get("state") == "not_retained"
            for support in original_support["support"]
            for statement in support.get("statements", [])
        )
        if missing:
            opening.append(
                f"{missing} supporting source records not retained; inspect native_payload['support'] for their exact references."
            )
        if original_support.get("stored_conflicts"):
            opening.append(
                "Stored conflicts remain unresolved; inspect native_payload['stored_conflicts']."
            )
        if original_support.get("stored_alternatives"):
            opening.append(
                "Stored alternative-selection context is retained in native_payload['stored_alternatives']."
            )
    if view._field_panel == "definition":
        opening.append(
            "Synonym scopes describe terminology; they do not establish disease identity."
        )
    scientific = view._selection._scientific
    if scientific is not None and not view._record_panel:
        opening.append(
            "Inventory sequence coverage does not establish coordinate completeness."
        )
        opening.append(
            f"Full captured inventory: {len(scientific.wire['exclusions'])} scientific exclusions; inspect exclusions for original reasons."
        )
        if scientific.wire["context"].get("explanation_rule") in (
            "structure_inventory_explanation@3",
            "structure_inventory_explanation@4",
        ):
            unplaced = sum(
                row.get("status") == "unplaced" for row in scientific.wire["exclusions"]
            )
            if unplaced:
                opening.append(
                    f"Full captured inventory: {unplaced} retained declarations cannot be assigned to this protein; inspect exclusions for their reasons and original source support."
                )
        if (
            scientific.wire["context"].get("explanation_rule")
            == "structure_inventory_explanation@4"
        ):
            unknown = sum(
                row["coordinate_scope"]["status"] != "comparable"
                for row in scientific.wire["native_payload"].get("items", [])
            )
            if unknown:
                opening.append(
                    f"Full captured inventory: {unknown} declarations lack verified original residue numbering; their regional completeness and sequence comparisons remain unknown. Open an item and explain() for its reason and original source links."
                )
        for row in scientific.wire["coverage"].get("rows", [])[:4]:
            opening.append(
                f"{preview(row['source'])}: {preview(row['state'])} (retained source/request scope)"
            )
    if scientific is not None and view._focus is not None:
        reading = view._regional_reading(chain_limit=6)
        if reading is not None:
            opening.extend(_regional_reading(reading))
        for key, value in scientific.native_item(view._focus)["state"].items():
            opening.append(
                f"Structural state · {preview(key)}: {'unknown' if value is None else preview(value)}"
            )
    ligand_reading = view._ligand_reading(entry_limit=6)
    if ligand_reading is not None:
        opening.extend(_ligand_reading(view, ligand_reading))
    from .card_navigation_preview_v1 import guidance, plan

    indices, navigation_counts = plan(view)
    rows = []
    for index in indices:
        item = view.items()[index]
        # Literal previews preserve null/zero/false; units remain paired with
        # native values without invoking a scientific adapter.
        value = item._entry.value
        if view._link_panel:
            if value.get("role") == "question":
                context_key = (
                    "assembly_request"
                    if value.get("rule")
                    in (
                        "structure_declaration_context_links@2",
                        "structure_declaration_context_links@3",
                    )
                    else "model_context"
                    if value.get("rule")
                    in (
                        "retained_context_links@4",
                        "retained_context_links@5",
                        "retained_context_links@6",
                        "retained_context_links@8",
                    )
                    else "annotation_context"
                )
                rows.append(
                    (
                        str(index),
                        preview(item.label),
                        f"{preview(value['availability'])} · {preview(value[context_key]['reason'], 240)}",
                    )
                )
                continue
            component_preview = _component_link_preview(view, value)
            if component_preview is not None:
                rows.append((str(index), *component_preview))
                continue
            rows.append(
                (
                    str(index),
                    preview(item.label),
                    f"{preview(value['availability'])} · {len(value['candidates'])} captured destinations",
                )
            )
            continue
        if view._record_panel:
            from .card_exploration_profiles import RECORD_COLUMNS

            record_row = (
                str(index),
                *(
                    "unknown" if value.get(key) is None else preview(value[key])
                    for key in RECORD_COLUMNS[view._record_panel]
                ),
            )
            if view._record_panel == "coverage":
                basis = value.get("basis")
                detail = basis.get("detail") if isinstance(basis, dict) else None
                record_row += (
                    "not retained" if detail is None else preview(detail, limit=240),
                )
            if view._record_panel == "assembly_generation":
                from .card_assembly_dispatch import presentation

                display_row = presentation(view).display_row

                record_row = display_row(item, index, preview)
            if view._record_panel == "quaternary_interpretation":
                kinds = {
                    "interface_classification": "Interface classification",
                    "interface_family_comparison": "Interface/family comparison",
                }
                states = {
                    "computed": "Computed",
                    "partial": "Partly determined",
                    "not_computed": "Not computed",
                    "comparable": "Comparable",
                }
                record_row = (
                    str(index),
                    preview(item.label),
                    kinds[value["kind"]],
                    preview(value["partner_ref"]),
                    states[value["status"]],
                    states[value["coordinate_status"]],
                    preview(value["finding"]),
                    preview(value["reason"]),
                )
            if view._record_panel == "ligand_site_comparisons":
                state = {
                    "computed": "Compared",
                    "partial": "Partly compared",
                    "not_computed": "Not compared",
                }.get(value["comparison_status"], "Unknown comparison state")
                record_row = (
                    record_row[0],
                    preview(item.label),
                    record_row[1],
                    state,
                    *record_row[3:],
                )
            if view._record_panel == "classification":
                basis, rule = relationship_basis(item)
                record_row += (
                    preview(basis) + (f" · {preview(rule)}" if rule else ""),
                )
                if basis == "Source-supported broader term":
                    record_row = (
                        *record_row[:-1],
                        record_row[-1] + "; no derivation recorded",
                    )
            rows.append(record_row)
            continue
        if scientific is not None:
            import pyunitwizard as puw

            native = scientific.native_item(item._entry.key)
            resolution = native["resolution"]
            resolution_text = (
                "resolution unknown"
                if resolution is None
                else f"{preview(puw.get_value(resolution, to_unit='angstrom'))} angstrom"
            )
            chains = native["chains"]
            chains_text = (
                "unknown"
                if chains is None
                else (
                    ", ".join(preview(chain) for chain in chains[:4])
                    + (f" … ({len(chains)} total)" if len(chains) > 4 else "")
                    if isinstance(chains, list)
                    else preview(chains)
                )
            )
            rows.append(
                (
                    str(index),
                    preview(item.label),
                    "unknown"
                    if native["method"] is None
                    else preview(native["method"]),
                    resolution_text,
                    chains_text,
                    "unknown"
                    if native["coverage"] is None
                    else preview(native["coverage"]),
                    "unknown"
                    if native["coverage_class"] is None
                    else preview(native["coverage_class"]),
                )
                + (
                    (_declared_ranges(view, item), _region_text(native))
                    if view.request and view.request["question"] == "region_coverage"
                    else ()
                )
            )
            continue
        elif view._field_panel:
            if view._field_panel == "quaternary_structure":
                from .card_quaternary_source_v1 import preview as quaternary_preview

                rows.append(
                    (
                        str(index),
                        preview(item.label),
                        quaternary_preview(view.explorer, item._entry),
                    )
                )
                continue
            if view._field_panel == "annotated_regions":
                from .card_annotation_regions_v1 import context
                from .card_protein_source_render import feature

                binding = context(view.explorer, item._entry.location)
                status = (
                    "Structural question available"
                    if binding["state"] == "ready"
                    else "Structural context unavailable: "
                    + preview(binding["reason"], 170)
                )
                if (
                    binding["state"] == "ready"
                    and binding["sequence_revisions"]["state"] != "matching"
                ):
                    status += "; sequence revision agreement unknown"
                rows.append(
                    (
                        str(index),
                        preview(item.label),
                        feature(value, include_description=False) + " · " + status,
                    )
                )
                continue
            from .card_exploration_profiles import is_field

            if not is_field(item._entry):
                if view._field_panel == "ligand_instances":
                    from .card_ligand_instances_v1 import preview as instance_preview

                    shown = instance_preview(view.explorer, item._entry)
                elif view._field_panel in ("predicted_structures", "sites"):
                    from .card_protein_source_render import relationship

                    shown = relationship(view._field_panel, value)
                else:
                    shown = f"{preview(value['subject_ref'])} → {preview(value['object_ref'])}; source-stated identity, not a similarity match"
                if value.get("qualifier_conflicts"):
                    shown += (
                        " · unresolved qualifier conflicts; inspect original record"
                    )
                rows.append((str(index), preview(item.label), shown))
                continue
            shown = _field_text(item._entry.key, value["value"])
            if "unit" in value:
                shown += " " + preview(value["unit"])
            if view._field_panel == "properties":
                shown += " · " + _method(view.explorer, value)
            state = (
                "conflicting"
                if item._conflicts
                else "unknown"
                if value["value"] is None
                else "present"
            )
            shown += (
                f" · {_attribution(view.explorer, item._entry.key, value)} · {state}"
            )
        elif view._question_catalog:
            shown = (
                preview(value["scope"])
                + "; required options: "
                + (", ".join(value["required_options"]) or "none")
            )
        elif view._route_catalog:
            shown = preview(value["description"]) + (
                f" · {value['availability']}" if "availability" in value else ""
            )
        elif source_record(item):
            source = value.get("source")
            version = source.get("version") if isinstance(source, dict) else None
            retrieved = value.get("retrieved_at")
            asserted = (
                preview(value["asserted_value"])
                if "asserted_value" in value
                else "asserted value not retained"
            )
            shown = f"{asserted} · source version {preview(version) if version is not None else 'unknown'} · retrieved {preview(retrieved) if retrieved is not None else 'unknown'}"
            metadata = value.get("source_metadata")
            method = metadata.get("method") if isinstance(metadata, dict) else None
            shown += (
                f" · method: {preview(method)}"
                if method is not None
                else " · method not stated"
            )
            if isinstance(metadata, dict) and metadata.get("unit") is not None:
                shown += " · source unit: " + preview(metadata["unit"])
        elif (
            item._entry.location["kind"] == "card"
            and len(item._entry.location["segments"]) == 5
            and item._entry.location["segments"][:2]
            == [
                {"type": "Key", "value": "sections"},
                {"type": "Key", "value": "features_positional"},
            ]
            and item._entry.location["segments"][3] == {"type": "Key", "value": "value"}
            and item._entry.location["segments"][4]["type"] == "Index"
        ):
            from .card_protein_source_render import feature

            shown = feature(value)
        elif isinstance(value, dict) and "value" in value:
            shown = preview(value["value"])
            if "unit" in value:
                shown += f" {preview(value['unit'])}"
        else:
            shown = preview(value)
        rows.append((str(index), preview(item.label), shown))
    count = len(view.items())
    footer = [
        f"{count} items" + (f" · showing 10, {count - 10} more" if count > 10 else "")
    ]
    footer.extend(guidance(navigation_counts))
    footer.append(
        "items()[i].open() · items()[i].explain() · items()[i].related() · back()"
    )
    footer.append(
        "Full values: rows(), native_payload. "
        + (
            "No destination Card supplied; explorer is None. Retained context and back() remain available."
            if view.explorer is None
            else "Start: explorer.topics()."
        )
    )
    return opening, rows, footer


def _headers(view):
    if view._record_panel == "coverage":
        return [
            "Index",
            "Area",
            "Source",
            "State",
            "Count",
            "Release",
            "Source/request scope",
        ]
    if view._record_panel == "assembly_generation":
        from .card_assembly_dispatch import presentation

        return list(presentation(view).HEADERS)
    if view._record_panel == "quaternary_interpretation":
        if view._explorer.mode == "saved":
            from .card_quaternary_history_v1 import HEADERS
        else:
            from .card_quaternary_exploration import HEADERS

        return list(HEADERS)
    if view._record_panel == "ligand_site_comparisons":
        if view._explorer.mode == "saved":
            from .card_ligand_site_history_v1 import HEADERS
        else:
            from .card_ligand_site_exploration import HEADERS

        return list(HEADERS)
    if view._record_panel:
        return ["Index", "Subject", "Relationship", "Broader term reference", "Basis"]
    return (
        [
            "Index",
            "Structure",
            "Method",
            "Resolution",
            "Chains",
            "Sequence coverage",
            "Coverage class",
        ]
        + (
            ["Declared ranges", "Requested region"]
            if view.request and view.request["question"] == "region_coverage"
            else []
        )
        if view._selection._scientific is not None
        else ["Index", "Label", "Value"]
    )


def _summary_row(row, view):
    if view._record_panel:
        return (
            row[0]
            + ". "
            + " · ".join(
                f"{label}: {value}" for label, value in zip(_headers(view)[1:], row[1:])
            )
        )
    if len(row) == 3:
        return f"{row[0]}. {row[1]}: {row[2]}"
    return (
        f"{row[0]}. {row[1]}: {row[2]} · {row[3]} · chains {row[4]} · sequence coverage {row[5]} · {row[6]}"
        + (f" · declared ranges {row[7]} · {row[8]}" if len(row) == 9 else "")
    )


def render_text(view):
    opening, rows, footer = _parts(view)
    body = (
        [" | ".join(_headers(view)), *(" | ".join(row) for row in rows)]
        if view.presentation == "table"
        else [_summary_row(row, view) for row in rows]
    )
    return "\n".join([preview(view.title), *opening, *body, *footer])


def render_html(view):
    """Escape source text; the preview is inert, with explicit Python actions."""
    opening, rows, footer = _parts(view)
    body = (
        "<table><thead><tr>"
        + "".join(f"<th>{escape(label)}</th>" for label in _headers(view))
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table>"
        if view.presentation == "table"
        else "".join(f"<div>{escape(_summary_row(row, view))}</div>" for row in rows)
    )
    return (
        "<section><strong>"
        + escape(preview(view.title))
        + "</strong>"
        + "".join(f"<div>{escape(line)}</div>" for line in opening)
        + body
        + "".join(f"<div>{escape(line)}</div>" for line in footer)
        + "</section>"
    )
