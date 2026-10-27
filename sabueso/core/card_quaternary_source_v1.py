"""Frozen original subunit, assembly and interface presentation membership.

This pane reads source declarations, not the oligomer classifier. Keep v1 typed
locations and membership stable for independent saved reading. A component,
assembly identifier or residue label never establishes physical identity.
"""

from .card_access import _Entry
from .card_protein_source_v1 import focal_subject

TOPIC = "quaternary_structure"
NAVIGATION_RULE = "quaternary_context_links@1"
SCOPE = (
    "Original subunit annotation, structure-specific biological assembly records "
    "and interface relationships, kept as distinct statement types. Assembly IDs "
    "are local to their structure; source stoichiometry and methods are retained "
    "declarations. Interface residue numbering remains as recorded. No aggregate "
    "contact-to-instance correspondence, assembly projection, interface geometry "
    "or biological relevance is inferred. Missing declarations are not absence; "
    "inspect coverage for source/request states and explain() for original support."
)
COLUMNS = (
    "label",
    "kind",
    "structure_ref",
    "assembly_id",
    "partner_ref",
    "value",
    "type",
)
SELECT = ("label", "kind", "structure_ref", "assembly_id", "partner_ref")


def child(location, kind, value):
    return {
        **location,
        "segments": [*location["segments"], {"type": kind, "value": value}],
    }


def entries(explorer):
    """Select exact captured nodes; duplicates preserve their original ordinals."""
    subject = focal_subject(explorer)
    if subject is None:
        return (), [{"field": "relationship subject", "state": "missing_prerequisite"}]
    found, gaps = [], []
    location = explorer._location("sections", "annotations", "subunit")
    from .errors import ArgumentError

    try:
        node, _ = explorer.access._resolve(location)
    except ArgumentError:
        gaps.append({"field": "annotations.subunit", "state": "not_retained"})
    else:
        if isinstance(node, dict) and "value" in node:
            found.append(_Entry(location, "annotations.subunit", node))
        else:
            gaps.append(
                {
                    "field": "annotations.subunit",
                    "state": "unrecognized_shape",
                    "location": location,
                }
            )
    for row in explorer.access._focal.data["relationship_store"]:
        if row["subject_ref"] != subject:
            continue
        root = child(explorer._location("relationship_store"), "Record", row["id"])
        if row["predicate"] == "has_interface_with":
            found.append(_Entry(root, row["id"], row))
        elif row["predicate"] == "has_structure":
            q = row.get("qualifiers")
            parent = child(root, "Key", "qualifiers")
            if not isinstance(q, dict):
                gaps.append(
                    {
                        "field": row["id"],
                        "state": "unrecognized_shape",
                        "location": parent,
                    }
                )
                continue
            location = child(parent, "Key", "assemblies")
            value = q.get("assemblies")
            if not isinstance(value, list) or not value:
                gaps.append(
                    {
                        "field": row["id"],
                        "state": "retained_empty"
                        if value == []
                        else "not_retained"
                        if value is None
                        else "unrecognized_shape",
                        "location": location,
                    }
                )
                continue
            for ordinal, record in enumerate(value):
                leaf = child(location, "Index", ordinal)
                if isinstance(record, dict):
                    found.append(
                        _Entry(leaf, f"{row['id']}:assembly:{ordinal}", record, ordinal)
                    )
                else:
                    gaps.append(
                        {
                            "field": f"{row['id']}:assembly:{ordinal}",
                            "state": "unrecognized_shape",
                            "location": leaf,
                        }
                    )
    return tuple(found), gaps


def context(explorer, entry):
    """Derive presentation context only from exact typed parents, never labels."""
    s = entry.location["segments"]
    if s[0] == {"type": "Key", "value": "sections"}:
        return "subunit_annotation", None
    row, _ = explorer.access._resolve({**entry.location, "segments": s[:2]})
    return ("assembly" if len(s) == 5 else "interface"), row


def label(explorer, entry):
    kind, row = context(explorer, entry)
    if kind == "subunit_annotation":
        return "Source subunit annotation"
    if kind == "interface":
        return "Interface statement · " + row["object_ref"]
    identifier = entry.value.get("id")
    return (
        f"{row['object_ref']} · assembly {identifier if identifier is not None else 'unknown'}"
        f" · original record {entry.ordinal + 1}"
    )


def values(explorer, entry):
    kind, row = context(explorer, entry)
    return {
        "kind": kind,
        "structure_ref": row["object_ref"] if kind == "assembly" else None,
        "assembly_id": entry.value.get("id") if kind == "assembly" else None,
        "partner_ref": row["object_ref"] if kind == "interface" else None,
        "value": entry.value.get("value")
        if kind == "subunit_annotation"
        else entry.value,
    }


def links(explorer, entry):
    """Exact local source/structure context; no assembly or instance identity join."""
    from copy import deepcopy

    support = explorer._support(entry.location)
    result, seen = [], set()

    def local(role, target, location, basis, label):
        result.append(
            {
                "role": role,
                "label": label,
                "target_ref": target,
                "support": deepcopy(basis),
                "rule": NAVIGATION_RULE,
                "candidates": [
                    {
                        "location": location,
                        "capture": explorer.access._focal_key,
                        "basis": "exact_retained_node",
                    }
                ]
                if location is not None
                else [],
                "paths": [],
                "blocked_paths": [],
                "availability": "available"
                if location is not None
                else "missing_prerequisite",
            }
        )

    for basis in support:
        for statement in [
            *basis.get("statements", []),
            *basis.get("derivation_input_statements", []),
        ]:
            if statement["id"] in seen:
                continue
            seen.add(statement["id"])
            local(
                "source",
                statement["id"],
                statement["location"] if statement["state"] == "present" else None,
                support,
                "Original source statement · " + statement["id"],
            )
    kind, row = context(explorer, entry)
    if kind == "assembly":
        location = {**entry.location, "segments": entry.location["segments"][:2]}
        local(
            "structure_context",
            row["object_ref"],
            location,
            support,
            "Original structure declaration · " + row["object_ref"],
        )
    elif kind == "interface":
        local(
            "interface_context",
            row["id"],
            entry.location,
            support,
            "Original interface relationship · " + row["object_ref"],
        )
        q = row.get("qualifiers")
        structures = q.get("structures") if isinstance(q, dict) else None
        refs = (
            {s for s in structures if isinstance(s, str)}
            if isinstance(structures, list)
            else set()
        )
        for structure in explorer.access._focal.data["relationship_store"]:
            if (
                structure["predicate"] == "has_structure"
                and structure["subject_ref"] == row["subject_ref"]
                and structure["object_ref"] in refs
            ):
                location = child(
                    explorer._location("relationship_store"), "Record", structure["id"]
                )
                local(
                    "structure_context",
                    structure["object_ref"],
                    location,
                    [*support, *explorer._support(location)],
                    "Source-referenced structure declaration · "
                    + structure["object_ref"],
                )
    return result


def related(item):
    from .card_context_navigation import _link_view

    explorer = item._view.explorer
    return _link_view(
        explorer,
        links(explorer, item._entry),
        item.open(),
        "Original quaternary context · " + item.label,
        source_location=item.payload_location,
        rule=NAVIGATION_RULE,
    )


def verify_links(view):
    """Bind original local destinations to their actual typed source item."""
    from .card_exploration_verification import equal, require

    explorer = view.explorer
    payload = view.native_payload
    source = payload.get("source_location")
    original, _ = entries(explorer)
    found = [entry for entry in original if equal(entry.location, source)]
    require(len(found) == 1, "Quaternary links have no exact original source item.")
    require(
        payload.get("focal") == explorer.access._focal_key
        and payload.get("inputs") == sorted(explorer.access._captures),
        "Quaternary links have a foreign capture context.",
    )
    require(
        equal(payload["links"], links(explorer, found[0])),
        "Original quaternary source/structure destinations differ.",
    )
    origin = view._origin
    while origin is not None and origin._link_panel:
        origin = origin._origin
    require(
        origin is not None
        and equal(
            explorer.access._resolve(origin._selection._target["location"])[1], source
        ),
        "Quaternary navigation has a different originating detail.",
    )


def preview(explorer, entry):
    """Bounded source wording; retain all original values in open/native access."""
    from .card_exploration_render import preview as show

    def text(value, limit=180):
        if value is None:
            return "unknown"
        if isinstance(value, list):
            return (
                "; ".join(show(part, limit) for part in value[:3])
                + (
                    f" … ({len(value)} original records; open() for all)"
                    if len(value) > 3
                    else ""
                )
                if value
                else "[] (retained empty list)"
            )
        return show(value, limit)

    kind, row = context(explorer, entry)
    if kind == "subunit_annotation":
        return "Subunit declaration: " + text(entry.value.get("value"), 350)
    if kind == "assembly":
        value = entry.value
        parts = [
            f"{title}: {text(value.get(key))}"
            for key, title in (
                ("oligomeric_state", "Source oligomeric state"),
                ("stoichiometry", "Stoichiometry"),
                ("oligomeric_count", "Recorded subunit count"),
                ("defined_by", "Defined by"),
                ("method", "Source method"),
            )
        ]
    else:
        q = row.get("qualifiers")
        if not isinstance(q, dict):
            return "Interface qualifier shape unrecognized; open original relationship"
        parts = [
            "Partner: " + show(q.get("partner_name")),
            "Original structures: " + text(q.get("structures")),
            "Recorded numbering: "
            + (show(q["numbering"]) if q.get("numbering") is not None else "unknown"),
            "Original residue spans: "
            + (
                "; ".join(
                    f"{text(r.get('start'), 35)}–{text(r.get('end'), 35)}"
                    if isinstance(r, dict)
                    else show(r, 60)
                    for r in q["residues"][:3]
                )
                + (
                    f" … ({len(q['residues'])} records; open() for all)"
                    if len(q["residues"]) > 3
                    else ""
                )
                if isinstance(q.get("residues"), list) and q["residues"]
                else text(q.get("residues"))
            ),
            "Assembly correspondence: not established by this pane",
        ]
    if row.get("qualifier_conflicts"):
        parts.append(
            "Unresolved qualifier conflicts; inspect full original alternatives"
        )
    return " · ".join(parts)
