"""Readable native genomic and per-tissue scope without clinical inference."""

HEADERS = (
    "Index",
    "Native occurrence",
    "Variant / isoform",
    "Genomic scope",
    "Tissue basis",
    "Resolved tissues",
    "Source support",
)


def display_row(item, index, preview):
    row = item._entry.value
    return (
        str(index),
        "Population variant"
        if row["kind"] == "population_variant"
        else "Isoform context",
        preview(item.label),
        preview(row["assembly"]) + " / " + preview(row["chromosome"]),
        preview(row["pext_basis"]),
        "not stated" if row["tissue_count"] is None else preview(row["tissue_count"]),
        preview(row["support_state"]),
    )


def opening(view, preview):
    return [
        "Population variants and UniProt isoforms retain their own original occurrences; this panel does not join natural sequence variants to genomic variants.",
        "Mode: "
        + preview(view.context["options"]["mode"])
        + "; native rule: "
        + preview(view.native_payload["rule"]["rule"])
        + ".",
        "Genomic assembly/chromosome, exact transcript/CDS support and per-tissue denominators remain explicit. A missing/conflicting tissue value is unknown, never zero expression or harmlessness.",
        "Inspect complete native items and explanations for every tissue, unknown, excluded input and source scope. Source/context links return to the actual initiating selection and question.",
        "Saving retains original values, source context and executed requests for independent offline reading. Unexecuted saved queries remain explicitly not_saved.",
    ]


def context_opening(view, preview):
    return [
        "Exact original variant/isoform tissue context; no source acquisition or alignment.",
        "Context role: " + preview(view.context.get("variant_context")) + ".",
        "Full source values remain in native_payload; back() returns to the originating view.",
    ]
