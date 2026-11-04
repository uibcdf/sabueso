"""Original component navigation over retained, independently verified findings.

These named predicates are frozen. They read original rows and source locations;
they never calculate new science, construct Cards or import a current catalog.
"""

from copy import deepcopy
from dataclasses import replace

from ._card_local_navigation_v1 import local_link, source_links
from .card_assembly_history_v2 import expected_links, restore_result
from .card_exploration_verification import equal, require

ASSEMBLY_RULE = "assembly_generation_links@3"
LIST_RULE = "assembly_component_list_links@1"
DETAIL_RULE = "assembly_component_detail_links@1"
REQUEST_RULE = "assembly_component_request@1"
FORMAT = "sabueso.card_exploration@8"
VERIFIER = "assembly_component_navigation_binding@1"
NAVIGATION_RULES = (
    "structure_declaration_context_links@3",
    ASSEMBLY_RULE,
    LIST_RULE,
    DETAIL_RULE,
)
SCOPE = (
    "Original declared component positions, including repeats. Native polymer/nonpolymer "
    "records, neighbor references, missing identity and conflicts retain their own source "
    "basis. Inspectable records do not establish a resolved key, distinct physical copies, "
    "geometry, assembly contacts or biological relevance. No sources are queried."
)
STATES = {
    "resolved": "Native key matched",
    "referenced": "Neighbor reference only",
    "ambiguous": "Ambiguous native key",
    "unresolved": "No retained native match",
    "unrecognized_label": "Unrecognized original label",
}
ROLES = {
    "polymer_instance": "Polymer record",
    "nonpolymer_instance": "Nonpolymer record",
    "ligand_neighbor_reference": "Neighbor reference",
}


def _result(access, ref, row_key):
    wire = access._objects.get(ref)
    require(
        isinstance(wire, dict)
        and wire.get("context", {}).get("adapter")
        == "assembly_generation_exploration@2"
        and wire["context"]["card_ref"] == access._focal.pin
        and wire["context"]["snapshot_id"] == access._focal.snapshot
        and isinstance(row_key, str)
        and row_key in wire["rows"],
        "Component navigation has no original focal assembly row.",
    )
    return restore_result(ref, wire)


def _registry(result, row, binding):
    index = binding.get("registry_index")
    if index is None:
        return None, None
    require(
        type(index) is int and index >= 0, "Invalid original component registry index."
    )
    records = result.wire["native_payload"]["sources"][row["source_index"]][
        "component_registry"
    ]
    require(index < len(records), "Missing original component registry record.")
    return records[index], result.location(
        "native_payload", "sources", row["source_index"], "component_registry", index
    )


def _request(result, key, index, reason):
    return {
        "rule": REQUEST_RULE,
        "result_ref": result.result_ref,
        "row_key": key,
        "component_index": index,
        "reason": reason,
    }


def _shortcut(rule, role, label, support, request):
    return {
        "rule": rule,
        "role": role,
        "label": label,
        "target_ref": "declared_component_positions",
        "support": deepcopy(support),
        "candidates": [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available",
        "component_request": request,
    }


def assembly_payload(access, result, key):
    payload = expected_links(access, result, key)
    payload["rule"] = ASSEMBLY_RULE
    for link in payload["links"]:
        link["rule"] = ASSEMBLY_RULE
    if result.wire["rows"][key]["kind"] == "assembly_generator":
        request = _request(
            result,
            key,
            None,
            "Inspect each original declared position and its binding state; positions are not distinct physical molecules.",
        )
        payload["links"].insert(
            0,
            _shortcut(
                ASSEMBLY_RULE,
                "components",
                "Declared components and identifier states",
                [result.wire["support"][key]],
                request,
            ),
        )
    return payload


def _position(result, key, index):
    row = result.wire["rows"][key]
    require(
        row["kind"] == "assembly_generator",
        "Component navigation needs an original generator.",
    )
    bindings = row["item"].get("component_bindings", [])
    require(
        type(index) is int and 0 <= index < len(bindings),
        "Component position is not an original typed index.",
    )
    return row, bindings[index]


def _label(index, binding, registry):
    roles, codes = set(), set()
    for ref in registry.get("references", []) if registry is not None else []:
        roles.add(ROLES.get(ref["role"], ref["role"]))
        for field in ("comp_id", "entity_comp_id", "ligand_comp_id"):
            value = ref.get("descriptors", {}).get(field)
            if isinstance(value, str):
                codes.add(value)
    state = STATES.get(binding["state"], binding["state"])
    parts = [f"Position {index + 1}", str(binding.get("asym_id", "unrecognized label"))]
    if roles:
        parts.append(" / ".join(sorted(roles)))
    if codes:
        parts.append(" / ".join(sorted(codes)))
    parts.append(state)
    if binding.get("repeated"):
        parts.append("repeated declaration label")
    return " · ".join(parts)


def list_payload(access, result, key):
    row = result.wire["rows"][key]
    require(
        row["kind"] == "assembly_generator", "Component list has no original generator."
    )
    support = [result.wire["support"][key]]
    links = []
    for index, binding in enumerate(row["item"].get("component_bindings", [])):
        registry, _ = _registry(result, row, binding)
        request = _request(
            result,
            key,
            index,
            "Open this exact declared position, original identifiers and source records; no physical copy is inferred.",
        )
        links.append(
            _shortcut(
                LIST_RULE,
                "component",
                _label(index, binding, registry),
                support,
                request,
            )
        )
    links.append(
        local_link(
            _context(access),
            LIST_RULE,
            "original_declaration",
            row["label"],
            support,
            "Original generator declaration and retained component input",
            result.location("rows", key, "item"),
        )
    )
    return _payload(access, LIST_RULE, result.location("rows", key, "item"), links)


def detail_payload(access, result, key, index):
    row, binding = _position(result, key, index)
    registry, location = _registry(result, row, binding)
    support, context = [result.wire["support"][key]], _context(access)
    links = [
        local_link(
            context,
            DETAIL_RULE,
            "component_binding",
            str(binding.get("asym_id", "unrecognized label")),
            support,
            "Original declared position and binding state",
            result.location("rows", key, "item", "component_bindings", index),
        )
    ]
    if registry is not None:
        links.append(
            local_link(
                context,
                DETAIL_RULE,
                "native_key",
                registry["asym_id"],
                support,
                "Complete original native key, identity gaps and conflicts",
                location,
            )
        )
        for ordinal, ref in enumerate(registry["references"]):
            role = ROLES.get(ref["role"], ref["role"])
            for field, label in (
                ("input_location", "Original input"),
                ("entity_input_location", "Entity context"),
                ("instance_input_location", "Instance context"),
            ):
                if ref.get(field) is not None:
                    links.append(
                        local_link(
                            context,
                            DETAIL_RULE,
                            "component_record",
                            f"reference:{ordinal}:{field}",
                            support,
                            f"{role} · {label} · reference {ordinal + 1}",
                            ref[field],
                        )
                    )
    links.extend(source_links(context, DETAIL_RULE, support))
    links.append(
        local_link(
            context,
            DETAIL_RULE,
            "original_declaration",
            row["label"],
            support,
            "Original generator declaration",
            result.location("rows", key, "item"),
        )
    )
    return _payload(
        access,
        DETAIL_RULE,
        result.location("rows", key, "item", "component_bindings", index),
        links,
    )


def _context(access):
    from .card_ligand_site_history_v1 import _Context

    return _Context(access)


def _payload(access, rule, location, links):
    return {
        "rule": rule,
        "inputs": sorted(access._captures),
        "focal": access._focal_key,
        "source_location": location,
        "links": links,
    }


def assembly_related(item):
    result = item._view._selection._scientific
    return _emit(
        item._view.explorer,
        assembly_payload(item._view.explorer.access, result, item._entry.key),
        item._view,
        f"Original context for {item.label}",
    )


def _emit(explorer, payload, origin, title):
    from .card_context_navigation import _link_view

    return _link_view(
        explorer,
        payload["links"],
        origin,
        title,
        source_location=payload["source_location"],
        rule=payload["rule"],
        reason=SCOPE,
    )


def follow(item):
    explorer = item._view.explorer
    link = item._entry.value
    request = link["component_request"]
    origin = {
        "rule": "assembly_component_origin@1",
        "link_location": deepcopy(item._entry.location),
        "request": deepcopy(request),
    }
    if explorer.mode == "saved":
        for view in list(explorer._session["views"].values()):
            if (
                view._saved_state is not None
                and view._display_request is None
                and equal(view._component_navigation, origin)
            ):
                return replace(view, _explorer=explorer, _origin=item._view)
        from .card_exploration_storage import not_saved

        return not_saved(
            explorer,
            "This exact component destination was not retained; original captured inputs remain inspectable.",
            item._view,
        )
    require(
        set(request) == {"rule", "result_ref", "row_key", "component_index", "reason"}
        and request["rule"] == REQUEST_RULE,
        "Unsupported original component request.",
    )
    result = _result(explorer.access, request["result_ref"], request["row_key"])
    if request["component_index"] is None:
        require(
            link["rule"] == ASSEMBLY_RULE and link["role"] == "components",
            "Component list has no original assembly origin.",
        )
        payload = list_payload(explorer.access, result, request["row_key"])
        title = "Declared component positions"
    else:
        require(
            link["rule"] == LIST_RULE and link["role"] == "component",
            "Component detail has no original list origin.",
        )
        row, binding = _position(result, request["row_key"], request["component_index"])
        registry, _ = _registry(result, row, binding)
        title = _label(request["component_index"], binding, registry)
        payload = detail_payload(
            explorer.access, result, request["row_key"], request["component_index"]
        )
    base = _emit(explorer, payload, item._view, title)
    explorer._session["views"].pop(id(base), None)
    return replace(base, _component_navigation=origin)


def register_bundle(bundle):
    if not any(
        record["flags"]["_link_panel"]
        and isinstance(record["native_payload"], dict)
        and record["native_payload"].get("rule") in NAVIGATION_RULES
        for record in bundle["views"].values()
    ):
        return
    from .card_exploration_assembly_v2 import ADAPTERS

    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    bundle.setdefault("scientific_results", {})


def verify_links(view):
    """Check original component decisions, typed positions and actual origins."""
    access, native = view.explorer.access, view.native_payload
    source = access._resolve(native["source_location"])[1]
    segments = source["segments"]
    require(
        source["kind"] == "result"
        and len(segments) >= 2
        and segments[0] == {"type": "Key", "value": "rows"}
        and segments[1].get("type") == "Key",
        "Component links have no original assembly anchor.",
    )
    ref, key = source["result_ref"], segments[1]["value"]
    result = _result(access, ref, key)
    rule = native["rule"]
    if rule == ASSEMBLY_RULE:
        require(
            view._component_navigation is None,
            "Assembly context has an unexpected component request.",
        )
        require(len(segments) == 2, "Assembly links have a different original row.")
        expected = assembly_payload(access, result, key)
    elif rule == LIST_RULE:
        require(
            segments[2:] == [{"type": "Key", "value": "item"}],
            "Component list has a different original generator.",
        )
        expected = list_payload(access, result, key)
    else:
        require(
            rule == DETAIL_RULE
            and len(segments) == 5
            and segments[2:4]
            == [
                {"type": "Key", "value": "item"},
                {"type": "Key", "value": "component_bindings"},
            ]
            and segments[4].get("type") == "Index",
            "Component detail has no original declared position.",
        )
        index = segments[4]["value"]
        _position(result, key, index)
        expected = detail_payload(access, result, key, index)
    require(
        equal(native, expected),
        "Original component navigation, source support or typed positions differ.",
    )
    anchor = view
    while (
        anchor._origin is not None
        and anchor._origin._link_panel
        and anchor._origin.result_ref == view.result_ref
    ):
        anchor = anchor._origin
    require(anchor._reason == SCOPE, "Original component interpretation scope differs.")
    origin = anchor._origin
    if rule == ASSEMBLY_RULE:
        require(
            origin is not None
            and origin._record_panel == "assembly_generation"
            and origin.result_ref == ref
            and any(
                equal(entry.location, result.location("rows", key))
                for entry in origin._selection._entries
            ),
            "Assembly links lost their actual original row.",
        )
    else:
        parent_rule = ASSEMBLY_RULE if rule == LIST_RULE else LIST_RULE
        parent_location = (
            result.location("rows", key)
            if rule == LIST_RULE
            else result.location("rows", key, "item")
        )
        require(
            origin is not None
            and origin._link_panel
            and origin.native_payload.get("rule") == parent_rule
            and equal(origin.native_payload["source_location"], parent_location),
            "Component destination lost its actual originating question.",
        )
        wanted_index = None if rule == LIST_RULE else index
        actual = view._component_navigation
        require(
            isinstance(actual, dict)
            and set(actual) == {"rule", "link_location", "request"}
            and actual["rule"] == "assembly_component_origin@1",
            "Missing original component request binding.",
        )
        selected = [
            entry
            for entry in origin._selection._entries
            if equal(entry.location, actual["link_location"])
        ]
        require(
            len(selected) == 1
            and equal(actual["request"], selected[0].value.get("component_request")),
            "Component destination lost its exact original clicked link.",
        )
        require(
            any(
                entry.value.get("component_request", {}).get("rule") == REQUEST_RULE
                and entry.value["component_request"]["result_ref"] == ref
                and entry.value["component_request"]["row_key"] == key
                and equal(
                    entry.value["component_request"]["component_index"], wanted_index
                )
                for entry in selected
            ),
            "Component destination differs from its original requested position.",
        )
