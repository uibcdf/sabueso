"""Bounded presentation of retained molecule-to-target activity contexts."""

from .card_bioactivity_presentation_v1 import (
    CLASSES,
    _assay_lines,
    _citation_lines,
    _quantity,
    _record_lines,
    _scalar,
)

HEADERS = (
    "Index",
    "Target / original record",
    "Target capture",
    "Source molecule",
    "Grain",
    "Class",
    "Measurement",
    "Relation",
    "Native groups",
    "Source records",
    "Source / assay / document",
)
KINDS = {
    "activity_context_target": "Supplied target context",
    "activity_context_group": "Native measurement group",
    "activity_context_record": "Original source activity record",
}


def _aliases(refs, preview):
    if not refs:
        return "no admitted source molecule identity"
    labels = ", ".join(preview(ref, limit=60) for ref in refs[:3])
    return labels + (f" · {len(refs) - 3} more retained" if len(refs) > 3 else "")


def display_row(item, index, preview):
    row = item._entry.value
    broader = bool(
        row["interpretation"]["identity_membership"]["context_only_relationship_ids"]
    )
    multiple = (
        len(row["interpretation"]["identity_membership"]["included_molecule_refs"]) > 1
    )
    return (
        str(index),
        preview(row["label"]),
        _scalar(row["target_card_ref"], preview),
        _scalar(row["molecule_ref"], preview)
        if row["molecule_ref"] is not None
        else _aliases(row["molecule_refs"], preview),
        KINDS[row["kind"]],
        "broader native summary; inspect included records"
        if broader
        else "no single source-molecule summary"
        if multiple
        else CLASSES.get(row["class"], _scalar(row["class"], preview)),
        _quantity(row["measurement"], preview)
        if row["measurement"] is not None
        else "no quantity recomputed for this subset"
        if broader
        else "no single retained quantity",
        "no single relation for this scope"
        if broader or multiple
        else _scalar(row["relation"], preview),
        _scalar(row["measurement_count"], preview),
        _scalar(row["record_count"], preview),
        "inspect broader native context"
        if broader
        else "multiple source-molecule contexts"
        if multiple
        else " · ".join(
            _scalar(row[key], preview)
            for key in ("source", "assay_ref", "document_ref")
        ),
    )


def opening(view, preview):
    result = view._selection._scientific
    grain, options = result.wire["context"]["grain"], result.options
    lines = [
        "Retained activity context for this exact molecule within explicitly supplied protein captures; identity joins and original source outcomes remain inspectable.",
        "Focal molecule capture: "
        + _scalar(
            view.context.get("molecule_card_ref", view.context.get("card_ref")), preview
        ),
        "Captured target contexts are not a count of distinct biological targets or independent experiments. Aliased source molecule records retain their original group and record membership.",
        "Zero matches apply only to the supplied contexts and admitted identity edges. Missing context, missing support and unqueried or unavailable sources do not establish inactivity or absence of targets.",
        "Concentration classes are retained configured bands, not efficacy, selectivity or therapeutic effect. Single-point inhibition does not establish potency or a test concentration.",
        "Policies: "
        + "; ".join(
            _scalar(options.get(key), preview)
            for key in ("classification_rule", "measurement_rule", "target_scope_rule")
        )
        + ". Indirect records included: "
        + ("yes" if options.get("include_indirect") else "no")
        + ".",
    ]
    for key, label in (
        ("target_card_ref", "Exact supplied target capture"),
        ("molecule_ref", "Exact joined source molecule"),
        ("measurement_ref", "Exact native group or source-record identity"),
    ):
        if options.get(key) is not None:
            lines.append(label + ": " + _scalar(options[key], preview))
    lines.append(
        {
            "target": "Open a supplied target context for its original native groups; open a group for its original source records.",
            "group": "Each row retains its exact target pin, joined source molecule and native group. Open it for the original source records.",
            "record": "Open a source record for its complete measurement, assay, citation and qualifiers; display selection does not reevaluate science.",
        }[grain]
    )
    if any(
        row["interpretation"]["identity_membership"]["context_only_relationship_ids"]
        for row in result.wire["rows"].values()
    ):
        lines.append(
            "Rows and counts include only source records whose literal molecule identities were explicitly selected. Additional records in the native copy/group remain context; no narrower class or scalar is recomputed from that broader summary. Open the included source records for their own retained measurements."
        )
    lines.extend(
        (
            "explain() shows exact identity and activity statements, including unavailable references. related() opens molecule, target, source, assay, citation and full publication context; back() returns the exact preceding selection.",
            "The focal explorer remains the molecule. Target context always names its separate captured pin; the molecule return link preserves the originating target selection.",
            "Publication counts and links retain the entire target publication context, including other molecules. Citation metadata does not imply article reading or independent evidence.",
            "Grouped structural investigation flags retain an existing ordering limitation. Original occurrences remain inspectable and do not establish an authoritative investigation status.",
            "Saving this activity-context profile is unavailable until genuine producer controls and independent original saved reading are implemented.",
        )
    )
    if view.presentation == "detail" and view._selected:
        row = view._selected[0].value
        lines.append(
            "Original source record: " + _scalar(row["relationship_id"], preview)
        )
        lines.extend(_record_lines(row["item"], preview))
        lines.append("Complete original record and qualifiers: native_payload.")
    return lines


def context_opening(view, preview):
    """Describe an explicit destination without truncating retained data."""
    context = view.context
    role, node = context.get("activity_context"), view._native_override
    if node is None:
        node = view._explorer.access._resolve(view._selection._target["location"])[0]
    lines = [
        "Exact retained molecule and supplied-target context; no source request or identity inference.",
        (
            "Origin molecule capture: "
            if role == "target_card"
            else "Focal molecule capture: "
        )
        + _scalar(context.get("molecule_card_ref"), preview),
        "Target capture: " + _scalar(context.get("target_card_ref"), preview),
    ]
    membership = context.get("molecule_activity_navigation", {}).get(
        "identity_membership", {}
    )
    if membership.get("context_only_relationship_ids"):
        lines.append(
            "The original native summary also retains records outside the selected source-molecule identities. Those context-only records and their support remain inspectable; they do not add to the included record count."
        )
    if role == "target_card":
        lines.append(
            "This explicit crossing opens the supplied protein explorer. New questions use that target Card; back() returns to the molecule activity links."
        )
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
                f"Showing 3 of {len(members)} original entries; native_payload retains all entries."
            )
    elif role == "publication_context" and isinstance(node, dict):
        publication = node.get("publication", node)
        lines.extend(_citation_lines(publication, preview))
        if isinstance(publication, dict) and "measurements" in publication:
            lines.append(
                "Activity links in this complete target publication context: "
                + _scalar(publication["measurements"], preview)
                + ". This count is not restricted to the focal molecule."
            )
        if isinstance(node.get("links"), list):
            lines.append(f"Complete retained publication links: {len(node['links'])}.")
    elif role in ("original_relationship", "original_record", "native_record"):
        lines.extend(_record_lines(node, preview))
    elif role == "identity_context":
        lines.append(
            "Only retained source-stated identity edges join records; conflicting anchors, duplicate inputs and unavailable support remain explicit."
        )
    elif role == "native_ligand_crossing":
        lines.append(
            "This is the unchanged native crossing, including duplicate input diagnostics. Grouped structural investigation flags retain the known False/None ordering limitation; inspect original per-occurrence declarations. No new aggregation policy is applied."
        )
    lines.append(
        "Complete original values: native_payload. back() returns to the actual originating activity-context selection or links."
    )
    return lines
