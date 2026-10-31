"""Frozen structure declaration links and exact assembly questions (@2)."""

from copy import deepcopy

from ._card_local_navigation_v1 import endpoint_link, local_link, source_links
from .card_protein_source_v1 import focal_subject
from .snapshot import canonical_json

RULE = "structure_declaration_context_links@2"
FORMAT = "sabueso.card_exploration@6"
VERIFIER = "structure_assembly_navigation_binding@1"
SCOPE = (
    "Original fields of this exact captured structure declaration. Ligands, "
    "assemblies, chains and author numbering retain their separate source scope. "
    "No ligand-to-assembly assignment, residue projection, observed-atom coverage "
    "or biological relevance is inferred. Missing fields are not absence."
)
FIELDS = (
    ("ligand_context", "ligands", list, "Original ligand declarations"),
    ("assembly_context", "assemblies", list, "Original assembly declarations"),
    ("chain_context", "chains", list, "Original chain declarations"),
    ("numbering_context", "author_numbering", dict, "Original author numbering"),
)


def _equal(a, b):
    return canonical_json(a) == canonical_json(b)


def context(explorer, location):
    """Bind a real native inventory item or an exact literal declaration node."""
    access = explorer.access
    _, source = access._resolve(location)
    segments = source["segments"]
    native = source["kind"] == "result"
    if native:
        ref = source["result_ref"]
        wire = access._objects[ref]
        if not (
            ref not in access._metadata_refs
            and isinstance(wire, dict)
            and len(segments) == 2
            and segments[0] == {"type": "Key", "value": "items"}
            and segments[1].get("type") == "Key"
            and isinstance(segments[1].get("value"), str)
            and wire.get("context", {}).get("adapter") == "structure_exploration@1"
            and wire["context"]["card_ref"] == access._focal.pin
        ):
            return None
        key = segments[1]["value"]
        support = [deepcopy(wire["support"][key])]
        parent_location = support[0]["relationship_location"]
        if not _equal(
            parent_location,
            {
                **explorer._location("relationship_store"),
                "segments": [
                    {"type": "Key", "value": "relationship_store"},
                    {"type": "Record", "value": key},
                ],
            },
        ):
            return None
    else:
        if not (
            len(segments) in (2, 3)
            and segments[0] == {"type": "Key", "value": "relationship_store"}
            and segments[1].get("type") == "Record"
            and isinstance(segments[1].get("value"), str)
            and (
                len(segments) == 2
                or segments[2] == {"type": "Key", "value": "qualifiers"}
            )
            and source["card_ref"] == access._focal.pin
            and source["snapshot_id"] == access._focal.snapshot
        ):
            return None
        parent_location = {**source, "segments": segments[:2]}
        support = explorer._support(parent_location)
    parent, _ = access._resolve(parent_location)
    subject = focal_subject(explorer)
    if not (
        subject is not None
        and isinstance(parent, dict)
        and parent.get("predicate") == "has_structure"
        and parent.get("subject_ref") == subject
    ):
        return None
    return {
        "source_location": source,
        "parent_location": parent_location,
        "parent": parent,
        "support": support,
        "native": native,
    }


def links(explorer, basis):
    parent, support = basis["parent"], basis["support"]
    result = source_links(explorer, RULE, support)
    for role in ("subject", "object"):
        result.append(
            endpoint_link(explorer, RULE, role, parent[f"{role}_ref"], support)
        )
    result.append(
        local_link(
            explorer,
            RULE,
            "structure_context",
            parent["object_ref"],
            support,
            "Original structure declaration · " + parent["object_ref"],
            basis["parent_location"],
        )
    )
    qualifiers = parent.get("qualifiers")
    for role, field, shape, label in FIELDS:
        present = isinstance(qualifiers, dict) and field in qualifiers
        value = qualifiers[field] if present else None
        state = (
            "unrecognized_parent_shape"
            if not isinstance(qualifiers, dict)
            else "not_retained"
            if not present
            else "retained_null"
            if value is None
            else "unrecognized_shape"
            if not isinstance(value, shape)
            else "retained_empty"
            if not value
            else "retained"
        )
        location = (
            {
                **basis["parent_location"],
                "segments": [
                    *basis["parent_location"]["segments"],
                    {"type": "Key", "value": "qualifiers"},
                    {"type": "Key", "value": field},
                ],
            }
            if present
            else None
        )
        result.append(
            {
                **local_link(
                    explorer, RULE, role, parent["object_ref"], support, label, location
                ),
                "declaration_field": field,
                "declaration_state": state,
            }
        )
    result.append(question_link(explorer, basis))
    return result


def related(item, basis):
    from .card_context_navigation import _link_view

    return _link_view(
        item._view.explorer,
        links(item._view.explorer, basis),
        item.open(),
        "Original structure context · " + item.label,
        source_location=item.payload_location,
        rule=RULE,
        reason=SCOPE,
    )


def missing_reason(link):
    if link["role"] == "source":
        return "The referenced original source record is not retained in this captured Card. Inspect its original support/history; this gap is not repaired by supplying a destination Card."
    if link["role"] in {row[0] for row in FIELDS}:
        return f"The original {link['declaration_field']} field is not retained in an inspectable qualifier mapping for this exact declaration. Inspect the original structure and sources; missing data do not establish absence."
    return None


def verify_links(view):
    from .card_exploration_verification import equal, require

    payload, explorer = view.native_payload, view.explorer
    require(
        set(payload) == {"rule", "inputs", "focal", "source_location", "links"},
        "Unknown structure navigation metadata member.",
    )
    basis = context(explorer, payload["source_location"])
    require(
        basis is not None
        and equal(basis["source_location"], payload["source_location"]),
        "Structure navigation has no exact original declaration/item.",
    )
    require(
        payload["inputs"] == sorted(explorer.access._captures)
        and payload["focal"] == explorer.access._focal_key,
        "Structure navigation has a foreign capture context.",
    )
    require(
        equal(payload["links"], links(explorer, basis)),
        "Original structure field/source/endpoint decisions differ.",
    )
    origin = view._origin
    while origin is not None and origin._link_panel:
        origin = origin._origin
    if basis["native"]:
        require(
            origin is not None
            and origin._selection._scientific is not None
            and origin.result_ref == payload["source_location"]["result_ref"]
            and origin._focus == payload["source_location"]["segments"][1]["value"],
            "Structure navigation has a different originating inventory detail.",
        )
    else:
        require(
            origin is not None
            and equal(
                explorer.access._resolve(origin._selection._target["location"])[1],
                basis["source_location"],
            ),
            "Structure navigation has a different originating declaration detail.",
        )


def question_link(explorer, basis):
    """Prepare one exact request without executing the scientific reader."""
    from .card_assembly_history_v1 import options_for_assembly
    from .errors import ArgumentError

    parent = basis["parent"]
    try:
        options = options_for_assembly(
            {
                "structure_ref": parent["object_ref"],
                "relationship_id": parent["id"],
            }
        )
    except ArgumentError:
        options = None
    request = {
        "rule": "structure_assembly_request@1",
        "parent_location": basis["parent_location"],
        "state": "ready" if options is not None else "unsupported",
        "reason": (
            "Uses this exact retained structure declaration; missing generation input remains explicit. "
            "No source query, physical membership or biological relevance is inferred."
            if options is not None
            else "This declaration has no supported PDB structure reference; no assembly request is guessed."
        ),
        "request": {"question": "assembly_generation", "options": options}
        if options is not None
        else None,
    }
    return {
        "rule": RULE,
        "role": "question",
        "label": "Assembly components and operations for this declaration",
        "target_ref": "assembly_generation",
        "support": deepcopy(basis["support"]),
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available" if options is not None else "unsupported",
        "assembly_request": request,
    }


def register_bundle(bundle):
    """Choose an explicit new codec only when this navigation is retained."""
    if not any(
        record["flags"]["_link_panel"]
        and isinstance(record["native_payload"], dict)
        and record["native_payload"].get("rule") == RULE
        for record in bundle["views"].values()
    ):
        return
    from .card_exploration_assembly import ADAPTERS

    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    bundle.setdefault("scientific_results", {})


def verify_destination(view):
    """Bind a followed scientific answer to its originating exact declaration."""
    from .card_exploration_verification import equal, require

    origin = view._origin
    if not (
        origin is not None
        and origin._link_panel
        and origin.native_payload.get("rule") == RULE
    ):
        return
    # A captured destination starts its own explorer, whose later explicit
    # questions are independent of this panel's assembly shortcut. Preserve
    # that boundary only for an actual selected captured-Card destination.
    if view._explorer._origin is origin:
        require(
            any(
                link.get("role") != "question"
                and candidate["capture"] == view._explorer.access._focal_key
                for entry in origin._selected
                for link in (entry.value,)
                for candidate in link.get("candidates", [])
            ),
            "Independent Card exploration has no original captured-Card destination.",
        )
        return
    questions = [
        row for row in origin.native_payload["links"] if row["role"] == "question"
    ]
    if (
        view._selection._scientific is not None
        or view._record_panel is not None
        or view._field_panel is not None
    ):
        require(
            view._record_panel == "assembly_generation",
            "Assembly destination differs from its exact originating declaration.",
        )
    if view._record_panel == "assembly_generation":
        require(len(questions) == 1, "Missing original assembly question.")
        original = questions[0]["assembly_request"]
        request = original["request"]
        require(
            original["state"] == "ready"
            and equal(view.context["options"], request["options"])
            and (
                view.request is None
                or equal(view.request, {**request, "topic": "assembly_generation"})
            ),
            "Assembly destination differs from its exact originating declaration.",
        )
    elif (
        isinstance(view.native_payload, dict)
        and "assembly_request" in view.native_payload
        and "link" in view.native_payload
    ):
        native = view.native_payload
        require(
            len(questions) == 1
            and equal(native["link"], questions[0])
            and equal(native["assembly_request"], questions[0]["assembly_request"])
            and native["assembly_request"]["state"] != "ready"
            and view._status == native["assembly_request"]["state"]
            and view._reason == native["assembly_request"]["reason"],
            "Unavailable assembly destination differs from its original question.",
        )
