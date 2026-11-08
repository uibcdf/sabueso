"""Readable association scope, without cross-source score ranking."""

HEADERS = (
    "Index",
    "Original unit",
    "Subject",
    "Predicate",
    "Object",
    "Source / channel",
    "Identity basis",
    "Support",
)


def opening(view, preview):
    native = view.native_payload
    name = native["focal_term"]["name_field"]
    name = name.get("value") if isinstance(name, dict) else None
    return [
        "Retained molecular and clinical associations for "
        + (preview(name) + " · " if name is not None else "")
        + preview(native["identity"]["focal"])
        + ".",
        f"Captured scope: {len(native['contexts'])} input contexts; {native['matched_occurrences']} matched original occurrences; {len(native['exclusions'])} excluded or unmatched occurrences.",
        "Exact identifiers and source-stated equivalents only. Names, synonyms, related xrefs and subclass edges do not join identities.",
        "Association, indication and variant-condition mentions do not establish mechanism, causality, target validity or efficacy. Source scores are not ranked across channels.",
        "Every context retains its original native payload and knowledge/request states. Missing or unmatched supplied context is not global absence.",
        "Open a row for its complete original item; explain() retains source roles and related() follows exact supplied input pins. back() returns to the actual initiating selection and question.",
        "Independent original disease association saved reading remains pending. Captured Card export is available through explorer.access.export_card(path).",
    ]


def display_row(item, index, preview):
    row = item._entry.value
    return (
        str(index),
        preview(row["kind"]),
        preview(row["subject_ref"]),
        preview(row["predicate"]),
        preview(row["object_ref"]),
        preview(row["source"]) + " / " + preview(row["channel"]),
        preview(row["identity_basis"]),
        preview(row["support_state"]),
    )


def context_opening(view, preview):
    return [
        "Exact original association/input context; source roles and directions are preserved.",
        "Context role: "
        + preview(view.context.get("association_context"))
        + ". No source was consulted.",
        "Original disease pin: "
        + preview(view.context.get("disease_card_ref"))
        + ". back() returns to the originating selection or source links.",
    ]
