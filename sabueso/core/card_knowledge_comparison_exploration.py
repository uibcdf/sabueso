"""Human reading of the shared typed knowledge-comparison result."""

from dataclasses import replace

from .card_access import _handle
from .card_knowledge_comparison_access import materialize
from .card_knowledge_comparison_dispatch import SAVE_REASON
from .card_protein_context_exploration import display_filter as display_filter
from .card_protein_context_exploration import display_sort as display_sort
from .card_protein_context_exploration import explain as explain
from .card_protein_context_exploration import open_item as open_item

HEADERS = (
    "Index",
    "Knowledge scope",
    "Original self",
    "Original other",
    "Comparison",
    "Source support",
)


def view(explorer, origin, options):
    result = materialize(explorer.access, options)
    captured = explorer._inspect(
        result.location(), origin, title=result.wire["schema"]["label"]
    )
    explorer._session["views"].pop(id(captured), None)
    return replace(
        captured,
        _selection=replace(
            captured._selection,
            _result_ref=result.result_ref,
            _selection_ref=_handle(
                "XA_",
                {
                    "format": "protein_knowledge_human_selection@1",
                    "result_ref": result.result_ref,
                },
            ),
            _entries=result.entries,
            _scientific=result,
        ),
        _selected=result.entries,
        _record_panel="protein_context",
        _native_override=result.native,
        _context_override=result.wire["context"],
        _request=origin.request if origin else None,
        _status=result.wire["outcome"]["status"],
        _reason=result.wire["outcome"]["reason"],
        presentation="table",
    )


def opening(view, preview):
    return [
        "Comparison rule: card_knowledge_diff@2. Compare only the explicitly supplied captures. Equal values or positions never merge protein identity.",
        "Field rows compare typed stored representations, including units. Free text, uncertain positions, incomplete maps and multiple candidates stay explicit.",
        "Relationship rows compare exact object references; original direction, channels, qualifiers, conflicts and source records remain separate.",
        "The residue map is a caller input. Sabueso does not align sequences or validate its scientific correspondence.",
        SAVE_REASON
        if view.native_payload["rule"]["sabueso_version"] == "0.14.0+243.gf6d8e4a"
        else "Saving retains the executed comparison and its original source context; unexecuted questions remain unavailable.",
    ]


def display_row(item, index, preview):
    row = item._entry.value
    value = row["item"]
    if row["kind"] == "knowledge_relationships":
        a, b = value["self_records"], value["other_records"]
    elif row["kind"] == "supplied_residue_map":
        a, b = value["self_axis"], value["other_axis"]
    else:
        a, b = value.get("self"), value.get("other")
    return [
        str(index),
        preview(row["label"]),
        preview(a),
        preview(b),
        row["state"],
        row["support_state"],
    ]


def links(item):
    from .card_context_navigation import _link, _link_view
    from .card_protein_context_access import location

    result, explorer = item._view._selection._scientific, item._view.explorer
    support = result.wire["support"][item._entry.key]
    records = []

    def add(role, label, target, capture=None):
        record = _link(explorer, role, label, [support], location=target)
        if capture is not None:
            record["candidates"][0]["capture"] = capture
        record.update(label=label, rule="knowledge_comparison_links@1")
        records.append(record)

    add(
        "original_item",
        "Complete native comparison",
        item._entry.value["original_location"],
    )
    for input_ in support["inputs"]:
        capture = input_["capture"]
        add(
            "whole_card_context",
            "Complete supplied Card · " + input_["role"],
            location(explorer.access, capture),
            capture,
        )
    for source in support["source_assertions"]:
        if source["location"] is not None:
            add(
                "source",
                "Original source · " + source["state"] + " · " + source["id"],
                source["location"],
                source["capture"],
            )
        else:
            records.append(
                {
                    "role": "source",
                    "label": "Source not retained · " + source["id"],
                    "target_ref": source["id"],
                    "support": [support],
                    "rule": "knowledge_comparison_links@1",
                    "availability": "missing_prerequisite",
                    "candidates": [],
                    "paths": [],
                    "blocked_paths": [],
                }
            )
    return _link_view(
        explorer,
        records,
        item._view,
        "Knowledge comparison sources · " + item.label,
        source_location=item._entry.value["original_location"],
        support_location=result.location("support", item._entry.key),
        rule="knowledge_comparison_links@1",
    )
