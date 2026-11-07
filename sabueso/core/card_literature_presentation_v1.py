"""Bounded presentation of original publication links, support and locators."""

HEADERS = (
    "Index",
    "Publication",
    "Year",
    "Stored state",
    "Citations",
    "Primary structure citations",
    "ECO support",
    "Curated statements",
    "Mentions",
    "Structure mentions",
    "Source activity records",
    "Original relationships",
    "Metadata statements",
)
STATES = {
    "on_card": "Linked on this Card",
    "partial": "Partial original support",
    "not_on_card": "No stored publication link",
}


def _scalar(value, preview, *, limit=180):
    return "not stated" if value is None else preview(value, limit=limit)


def display_row(item, index, preview):
    row = item._entry.value
    label = (
        _scalar(row["title"], preview) + " · " + row["publication_ref"]
        if row["title"] is not None
        else row["publication_ref"] + " · title not retained"
    )
    return (
        str(index),
        label,
        _scalar(row["year"], preview),
        STATES.get(row["state"], _scalar(row["state"], preview)),
        *(
            _scalar(row[key], preview)
            for key in (
                "cited_by_count",
                "primary_citation_count",
                "support_count",
                "curated_count",
                "mention_count",
                "structure_mention_count",
                "measurement_count",
                "relationship_count",
                "article_metadata_count",
            )
        ),
    )


def _publication_lines(publication, preview):
    if not isinstance(publication, dict):
        return [
            "No publication is linked under this exact reference on the captured Card."
        ]
    lines = [
        label + ": " + _scalar(publication.get(key), preview, limit=320)
        for key, label in (
            ("publication_ref", "Exact publication reference"),
            ("title", "Retained title"),
            ("journal", "Retained journal"),
            ("year", "Retained year"),
            ("pubmed", "Retained PubMed identifier"),
            ("doi", "Retained DOI"),
        )
    ]
    for key, label in (
        ("cited_by", "Source citation links"),
        ("primary_citation_of", "Primary structure citation links"),
        ("supports", "ECO support links"),
        ("curated", "Human-curated statements"),
        ("mentions", "Direct mentions"),
        ("structure_mentions", "Structure mentions"),
        ("article_metadata", "Supplementary metadata statements"),
    ):
        lines.append(label + ": " + str(len(publication.get(key, []))) + ".")
    lines.append(
        "Source activity records in this complete publication context: "
        + _scalar(publication.get("measurements"), preview)
        + "."
    )
    return lines


def _explanation_lines(node, preview):
    lines = _publication_lines(node.get("publication"), preview)
    state = node.get("status")
    lines.append(
        "Retained publication state: "
        + STATES.get(state, _scalar(state, preview))
        + "."
    )
    if node.get("reason") is not None:
        lines.append(
            "Retained publication reason: " + _scalar(node["reason"], preview) + "."
        )
    for key, label in (
        ("links", "Complete original relationship links"),
        ("source_assertions", "Direct original statement references"),
        ("annotation_requests", "Retained article annotation requests"),
        ("unlinked_pdb_mentions", "Unlinked original PDB mention occurrences"),
    ):
        lines.append(label + ": " + str(len(node.get(key, []))) + ".")
    return lines


def opening(view, preview):
    """Explain native categories and distinguish request facts from content."""
    result = view._selection._scientific
    lines = [
        "Publications linked to the captured Card, with their retained source context.",
        "Source citations, primary structure citations, ECO support, human curation, mentions, activity records and supplementary metadata retain separate categories.",
        "A mention records naming. Citation or ECO links report source support; they do not establish article reading or project Evidence.",
        "Counts cover each publication's full retained context on this Card. Source activity records are not independent experiments.",
        "Source/query facts remain separate from publication-link state. Empty or unqueried source scope never establishes absence in an article or the literature.",
        "Open a publication for its complete native explanation; explain() inspects original statements and related() opens exact relationship, statement and locator destinations. back() returns to the originating selection.",
        "Saving this publication profile is unavailable until independent original saved reading is implemented. Full captured Card export: explorer.access.export_card(path).",
    ]
    if result.options["publication_ref"] is not None:
        native = result.wire["native_payload"]
        if "status" in native:
            lines.extend(_explanation_lines(native, preview))
        else:
            lines.append(
                "The publication links could not be evaluated; inspect the reported prerequisite limitation."
            )
    return lines


def context_opening(view, preview):
    """Present exact original endpoints without traversing the complete link graph."""
    role = view.context.get("literature_context")
    node = view._native_override
    if node is None:
        node = view._explorer.access._resolve(view._selection._target["location"])[0]
    lines = [
        "Original retained publication context; no source request or article acquisition.",
        "Citation, ECO support, mentions, curation, metadata and source measurements retain their original meanings.",
    ]
    if role == "publication_explanation" and isinstance(node, dict):
        lines.extend(_explanation_lines(node, preview))
    elif role == "publication_summary":
        lines.extend(_publication_lines(node, preview))
    elif role == "source" and isinstance(node, dict) and "asserted_value" in node:
        source = node.get("source") or {}
        lines.extend(
            label + ": " + _scalar(value, preview)
            for label, value in (
                ("Original source", source.get("name")),
                ("Original source record", source.get("record_id")),
                ("Original field", node.get("field_path")),
            )
        )
        value = node.get("asserted_value")
        if isinstance(value, dict) and "value" in value:
            declared = preview(value["value"])
            if "unit" in value:
                declared += " " + preview(value["unit"])
            lines.append("Original declared value: " + declared)
        else:
            lines.append("Original asserted value: " + preview(value))
        acquisition = node.get("acquisition") or {}
        lines.append(
            "Retained acquisition method: "
            + _scalar(acquisition.get("method"), preview)
            + "; origin: "
            + _scalar(acquisition.get("origin"), preview)
            + "."
        )
    elif (
        role == "original_relationship"
        and isinstance(node, dict)
        and "predicate" in node
    ):
        lines.extend(
            label + ": " + _scalar(node.get(key), preview)
            for key, label in (
                ("id", "Original relationship"),
                ("predicate", "Predicate"),
                ("subject_ref", "Original subject"),
                ("object_ref", "Original object"),
                ("qualifiers", "Complete retained qualifiers"),
                ("qualifier_conflicts", "Original qualifier alternatives"),
            )
        )
    else:
        lines.append("Original context role: " + _scalar(role, preview) + ".")
        lines.append("Retained content: " + preview(node) + ".")
        if isinstance(node, dict):
            lines.extend(
                label + ": " + _scalar(node[key], preview, limit=320)
                for key, label in (
                    ("locator", "Original locator"),
                    ("quote", "Original quoted fragment"),
                    ("locations", "Original occurrence locations"),
                    ("open_access", "Source open-access flag"),
                )
                if key in node
            )
    lines.append(
        "Full original values remain in native_payload; back() returns to the publication context links."
    )
    return lines
