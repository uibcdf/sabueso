"""Bounded native disease-association presentation, without scientific inference."""

from sabueso.core.card_exploration_render import preview

ADAPTER = "disease_association_exploration@1"
KINDS = {
    "association_statement",
    "indication_statement",
    "variant_condition",
    "uniprot_disease_xref",
}


def applies(view):
    return (
        view._record_panel == "associations" and view.context.get("adapter") == ADAPTER
    )


def scope(view, native):
    if not applies(view) or not isinstance(native, dict):
        return None
    contexts = native.get("contexts", [])
    return {
        "rule": preview(native.get("rule", {}).get("rule"), 120),
        "scope": preview(native.get("scope"), 1800),
        "matched_occurrences": native.get("matched_occurrences"),
        "selection_rows": len(view.items()),
        "input_occurrences": len(native.get("input_occurrences", [])),
        "context_count": len(contexts),
        "exclusion_count": len(native.get("exclusions", [])),
        "outcome": view.outcome,
        "contexts": [
            {
                "card_ref": preview(row.get("card_ref"), 220),
                "nature": preview(row.get("nature"), 80),
                "stored_occurrences": row.get("stored_occurrences"),
                "matched_occurrences": row.get("matched_occurrences"),
            }
            for row in contexts[:8]
        ],
        "contexts_complete": len(contexts) <= 8,
    }


def graph(view, items):
    if not applies(view):
        return None
    edges = []
    for item in items:
        if item.kind not in KINDS:
            continue
        cells = item.cells
        values = {
            name: cells[name].value
            for name in ("subject_ref", "predicate", "object_ref")
        }
        if not all(isinstance(value, str) and value for value in values.values()):
            continue
        edges.append(
            {
                "item_ref": item.item_ref,
                **values,
                **{
                    name: preview(cells[name].value, 160)
                    for name in ("source", "channel", "identity_basis", "support_state")
                },
            }
        )
    return (
        {
            "rule": "retained_disease_association_graph@1",
            "edges": edges,
            "scope": "Matched original statement rows with explicit endpoints on the current page; context rows and unknown endpoints remain in the original reading. Source direction, identity basis and support are retained; no causal, target-validity or efficacy inference",
        }
        if edges
        else None
    )
