"""Bounded, inert presentation of native bioactivity grains and retained context."""

HEADERS = (
    "Index",
    "Molecule / record",
    "Grain",
    "Class",
    "Measurement",
    "Relation",
    "Native groups",
    "Source records",
    "Source / assay / document",
)
KINDS = {
    "bioactivity_molecule": "Molecule",
    "bioactivity_group": "Native measurement group",
    "bioactivity_record": "Source activity record",
}
CLASSES = {
    "active": "Active concentration band",
    "weak": "Weak concentration band",
    "inactive": "Inactive concentration band",
    "inconclusive": "Inconclusive",
    "not_determined": "Not determined",
    "discordant": "Discordant retained classes",
}


def _scalar(value, preview, *, limit=180):
    return "not stated" if value is None else preview(value, limit=limit)


def _quantity(node, preview):
    if node is None:
        return "quantity unavailable"
    if not isinstance(node, dict) or "value" not in node or "unit" not in node:
        return "unrecognized retained quantity"
    return _scalar(node["value"], preview) + " " + _scalar(node["unit"], preview)


def display_row(item, index, preview):
    row = item._entry.value
    label = preview(row["label"])
    if row["kind"] == "bioactivity_molecule" and row["item"].get("name") is None:
        label += " · name not retained"
    return (
        str(index),
        label,
        KINDS[row["kind"]],
        CLASSES.get(row["class"], _scalar(row["class"], preview)),
        _quantity(row["measurement"], preview)
        if row["measurement"] is not None
        else "no single retained quantity",
        _scalar(row["relation"], preview),
        _scalar(row["measurement_count"], preview),
        _scalar(row["record_count"], preview),
        " · ".join(
            _scalar(row[key], preview)
            for key in ("source", "assay_ref", "document_ref")
        ),
    )


def opening(view, preview):
    result = view._selection._scientific
    grain, options = result.wire["context"]["grain"], result.options
    lines = [
        "Retained bioactivity records for the captured protein; native membership and effective scientific options are preserved.",
        "Concentration classes are configured bands, not efficacy, selectivity or therapeutic effect. Single-point inhibition does not establish potency or a test concentration.",
        "Native measurement groups and source-record counts are distinct; neither is a count of independent experiments. Missing values and missing source inputs remain unknown.",
        "Policies: "
        + "; ".join(
            _scalar(options.get(key), preview)
            for key in (
                "classification_rule",
                "measurement_rule",
                "target_scope_rule",
            )
        )
        + ". Indirect records included: "
        + ("yes" if options.get("include_indirect") else "no")
        + ".",
    ]
    if options.get("molecule_ref") is not None:
        lines.append("Exact molecule: " + _scalar(options["molecule_ref"], preview))
    if options.get("measurement_ref") is not None:
        lines.append(
            "Exact native measurement group: "
            + _scalar(options["measurement_ref"], preview)
        )
    membership = result.wire["context"].get("focus_membership")
    if membership is not None:
        lines.append(
            f"Original records included in this exact molecule/policy focus: {len(membership['included_relationship_ids'])}. "
            f"Other records retained only in the complete native group context: {len(membership['context_only_relationship_ids'])}. "
            "The complete native_payload and its source support remain inspectable."
        )
    lines.append(
        {
            "molecule": "Open a molecule for its native groups; open a group for every original source activity record.",
            "group": "Each row is an original native measurement group, including singleton relationship IDs. Open it for its original source records.",
            "record": "Open a source record for its original measurement, assay, citation and qualifiers; display never reevaluates science.",
        }[grain]
    )
    lines.extend(
        (
            "explain() retains the actual activity/assay source statements, including unavailable references; related() opens exact assay, citation and relationship context. back() returns to the originating selection.",
            "Citation metadata is retained context, not article reading, a dedicated document SourceAssertion or independent evidence. Publication-level counts cover their full retained scope.",
            "Saving this bioactivity profile is unavailable until independent original saved reading is implemented. Raw Card export: explorer.access.export_card(path).",
        )
    )
    if view.presentation == "detail" and view._selected:
        row = view._selected[0].value
        lines.append("Original record: " + _scalar(row.get("relationship_id"), preview))
        lines.extend(_record_lines(row["item"], preview))
        lines.append(
            "Complete unabridged retained record and qualifiers: native_payload."
        )
    return lines


def _record_lines(item, preview):
    if not isinstance(item, dict):
        return ["Original source record shape: " + preview(item)]
    if "relationship" not in item and "qualifiers" not in item:
        lines = [
            "Complete retained native molecule or measurement-group context; source records remain a separate grain."
        ]
        for key, label in (
            ("molecule_ref", "Molecule"),
            ("group", "Native group"),
            ("class", "Retained class"),
            ("measurement_count", "Native group count"),
            ("record_count", "Source-record count"),
        ):
            if key in item:
                lines.append(label + ": " + _scalar(item[key], preview))
        return lines
    relationship = item.get("relationship", item)
    if not isinstance(relationship, dict):
        return ["Original relationship is not retained as an object."]
    qualifiers = relationship.get("qualifiers", {})
    qualifiers = qualifiers if isinstance(qualifiers, dict) else {}
    measurement = qualifiers.get("measurement", {})
    measurement = measurement if isinstance(measurement, dict) else {}
    lines = [
        "Original reported measurement: "
        + " · ".join(
            (
                _scalar(measurement.get("type"), preview),
                "relation " + _scalar(measurement.get("relation"), preview),
                _scalar(measurement.get("value"), preview)
                + " "
                + _scalar(measurement.get("units"), preview),
            )
        ),
        "Normalized retained quantity: "
        + _quantity(measurement.get("normalized"), preview),
    ]
    for key, label in (
        ("upper_value", "Original upper bound"),
        ("text_value", "Original text value"),
        ("activity_comment", "Activity comment"),
        ("data_validity_comment", "Data validity comment"),
        ("potential_duplicate", "Source potential-duplicate flag"),
    ):
        if key in measurement:
            lines.append(label + ": " + _scalar(measurement[key], preview))
    lines.extend(_assay_lines(qualifiers.get("assay"), preview))
    lines.extend(_citation_lines(qualifiers.get("document"), preview))
    return lines


def _assay_lines(assay, preview):
    if not isinstance(assay, dict):
        return ["Assay context not retained."]
    return [
        label + ": " + _scalar(assay.get(key), preview, limit=320)
        for key, label in (
            ("id", "Assay"),
            ("type", "Assay type"),
            ("description", "Retained assay description"),
            ("organism", "Assay organism"),
            ("confidence_score", "Source assay confidence score"),
            ("relationship_type", "Source target assignment"),
            ("variant_mutation", "Source variant mutation"),
        )
    ]


def _citation_lines(citation, preview):
    if not isinstance(citation, dict):
        return ["Citation context not retained."]
    lines = [
        label + ": " + _scalar(citation.get(key), preview, limit=320)
        for key, label in (
            ("id", "Source document"),
            ("publication_ref", "Exact publication reference"),
            ("title", "Retained title"),
            ("journal", "Retained journal"),
            ("year", "Retained year"),
            ("pubmed", "Retained PubMed identifier"),
            ("doi", "Retained DOI"),
        )
        if key in citation
    ]
    if not any(citation.get(key) for key in ("publication_ref", "pubmed", "doi")):
        lines.append(
            "No exact publication identifier retained; publication continuation is unavailable."
        )
    return lines


def context_opening(view, preview):
    """Readable original context without copying a complete publication link graph."""
    role = view.context.get("bioactivity_context")
    node = view._native_override
    if node is None:
        node = view._explorer.access._resolve(view._selection._target["location"])[0]
    lines = [
        "Retained activity/assay/citation context from the captured Card. No source request or article reading.",
        "Citation fields keep their original activity/assay support grain; no document SourceAssertion is invented.",
    ]
    if role in ("assay_context", "citation_context"):
        members = node if isinstance(node, list) else [node]
        lines.append(f"Retained context entries: {len(members)}.")
        for member in members[:3]:
            value = member
            if isinstance(member, dict):
                value = member.get(
                    "assay" if role == "assay_context" else "document", member
                )
            lines.extend(
                _assay_lines(value, preview)
                if role == "assay_context"
                else _citation_lines(value, preview)
            )
        if len(members) > 3:
            lines.append(
                f"Showing 3 of {len(members)} original context entries; native_payload retains every entry."
            )
    elif role == "publication_context" and isinstance(node, dict):
        publication = node.get("publication", node)
        lines.extend(_citation_lines(publication, preview))
        if isinstance(publication, dict) and "measurements" in publication:
            lines.append(
                "Source activity links in this full retained publication context: "
                + _scalar(publication["measurements"], preview)
                + ". This count is not restricted to the selected molecule."
            )
        if isinstance(node.get("links"), list):
            lines.append(f"Complete retained publication links: {len(node['links'])}.")
    elif role in ("original_relationship", "original_record"):
        lines.extend(_record_lines(node, preview))
    lines.append(
        "Full original values: native_payload; back() returns to the activity context links."
    )
    return lines
