"""Readable clinical source scope without interpreting efficacy or trial names."""

HEADERS = (
    "Index",
    "Clinical unit",
    "Indication / trial",
    "ChEMBL maximum phase",
    "Registry status / phases",
    "Registry record state",
)
KINDS = {
    "clinical_molecule_phase": "Molecule phase",
    "clinical_indication": "Indication statement",
    "clinical_trial_citation": "Trial citation occurrence",
    "clinical_registry_record": "Trial registry context",
}


def display_row(item, index, preview):
    row = item._entry.value

    def scalar(key):
        cell = item.cells[key]
        return (
            preview(cell.value)
            if cell.value is not None
            else "not stated"
            if cell.state == "unknown"
            else "not applicable"
        )

    return (
        str(index),
        KINDS[row["kind"]],
        preview(item.label),
        scalar("chembl_max_phase"),
        scalar("registry_status") + " / " + scalar("registry_phases"),
        scalar("registry_state"),
    )


def opening(view, preview):
    native, coverage = view.native_payload, view.coverage
    return [
        "ChEMBL indications, individual cited trial occurrences and retained ClinicalTrials.gov registry context.",
        f"Captured scope: {len(native['indications'])} indications; {len(native['trials'])} trial contexts; {len(native['not_fetched'])} cited trial IDs not fetched.",
        "ChEMBL maximum phases and registry study phases/status are separate source statements. A citation, completed study or reported result does not establish efficacy.",
        "Each cited-trial occurrence retains its indication. Repeated trial IDs and shared disease headings do not merge indication terms or establish identity by intervention names.",
        *[
            f"{preview(row['source'])} · {preview(row['area'])}: {preview(row['state'])}."
            for row in coverage["rows"]
        ],
        "Open a clinical unit for its complete native item; explain() inspects role-bound source membership and related() opens original source, relationship and request context. back() returns to the exact selection.",
        "Independent original clinical saved reading remains pending. Captured Card export is available through explorer.access.export_card(path).",
    ]


def context_opening(view, preview):
    return [
        "Exact retained clinical context; source citations and registry descriptions keep separate roles and subjects.",
        "Context role: "
        + preview(view.context.get("clinical_context"))
        + ". No source was consulted by this navigation.",
        "Full original values remain in native_payload; back() returns to the originating clinical view or source links.",
    ]
