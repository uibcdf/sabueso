"""Current presentation of exact original ligand nodes, without scientific joins.

This policy does not change literal items, filters, navigation or saved science.
Full typed locations remain usable by both human inspection and bounded access.
"""

from copy import deepcopy
from itertools import islice

from .card_protein_source_v1 import focal_subject

RULE = "structure_ligand_reading@1"
SCOPE = (
    "Original ligand declarations in this exact structure relationship. Component "
    "and instance labels do not establish identity, region overlap, assembly "
    "membership or biological relevance. Recorded contacts keep their original "
    "numbering and mapping basis; they are not revalidated here. Missing "
    "declarations are not absence."
)


def _child(location, kind, value):
    return {
        **location,
        "segments": [*location["segments"], {"type": kind, "value": value}],
    }


def _state(present, value, shape):
    if not present:
        return "not_retained"
    if value is None:
        return "retained_null"
    if not isinstance(value, shape):
        return "unrecognized_shape"
    if isinstance(value, (list, dict, str)) and not value:
        return "retained_empty"
    return "retained"


def _field(parent, location, key, shape, *, scalar=False):
    present = isinstance(parent, dict) and key in parent
    value = parent[key] if present else None
    record = {
        "state": _state(present, value, shape),
        "location": _child(location, "Key", key) if present else None,
    }
    if scalar:
        # Preserve null/false/zero, but never copy an arbitrary container merely
        # to abbreviate a malformed label. Its original location stays available.
        record["value"] = (
            deepcopy(value) if not isinstance(value, (dict, list)) else None
        )
    if shape is list:
        record["count"] = len(value) if isinstance(value, list) else None
    return record


def _component(value, location):
    return {
        "component_id": _field(value, location, "comp_id", str, scalar=True),
        "description": _field(value, location, "description", str, scalar=True),
        "investigation_flag": _field(
            value, location, "subject_of_investigation", bool, scalar=True
        ),
        "instances": _field(value, location, "instances", list),
    }


def reading(view, *, entry_limit=None):
    """Detached literal context; None outside an exact focal ligand node.

    The complete property has no entry limit. Rendering asks for a bounded prefix
    and reports its original total explicitly. No location registry is mutated.
    """
    if (
        view._selection._scientific is not None
        or view._record_panel
        or view._field_panel
        or view._route_catalog
        or view._link_panel
        or "location" not in view._selection._target
    ):
        return None
    explorer = view._explorer
    access = explorer.access
    node, location = access._resolve(view._selection._target["location"])
    segments = location["segments"]
    if not (
        location["kind"] == "card"
        and location["card_ref"] == access._focal.pin
        and location["snapshot_id"] == access._focal.snapshot
        and 4 <= len(segments) <= 7
        and segments[0] == {"type": "Key", "value": "relationship_store"}
        and segments[1].get("type") == "Record"
        and segments[2:4]
        == [
            {"type": "Key", "value": "qualifiers"},
            {"type": "Key", "value": "ligands"},
        ]
        and (len(segments) < 5 or segments[4].get("type") == "Index")
        and (len(segments) < 6 or segments[5] == {"type": "Key", "value": "instances"})
        and (len(segments) < 7 or segments[6].get("type") == "Index")
    ):
        return None
    parent_location = {**location, "segments": segments[:2]}
    parent, _ = access._resolve(parent_location)
    subject = focal_subject(explorer)
    if not (
        subject is not None
        and isinstance(parent, dict)
        and parent.get("predicate") == "has_structure"
        and parent.get("subject_ref") == subject
    ):
        return None
    level = {4: "components", 5: "component", 6: "instances", 7: "instance"}[
        len(segments)
    ]
    plural = level in ("components", "instances")
    shape = list if plural else dict
    node_count = (
        len(node) if plural and isinstance(node, list) else 1 if not plural else None
    )
    count = len(view._selected) if plural and isinstance(node, list) else node_count
    component = None
    if len(segments) >= 5:
        component_location = {**location, "segments": segments[:5]}
        component_value, _ = access._resolve(component_location)
        component = _component(component_value, component_location)
    entries = []
    source = (
        (
            (entry.location["segments"][-1]["value"], entry.value)
            for entry in view._selected
        )
        if plural and isinstance(node, list)
        else ()
    )
    if not plural:
        source = [(segments[-1]["value"], node)]
    if entry_limit is not None:
        source = islice(source, entry_limit)
    for index, value in source:
        leaf = _child(location, "Index", index) if plural else location
        entry = {
            "index": index,
            "location": deepcopy(leaf),
            "state": _state(True, value, dict),
        }
        if level in ("components", "component"):
            entry.update(_component(value, leaf))
        else:
            entry.update(
                {
                    "instance_id": _field(value, leaf, "asym_id", str, scalar=True),
                    "chains": _field(value, leaf, "chains", list),
                    "contacts": _field(value, leaf, "contacts", list),
                    "bound_flag": _field(value, leaf, "is_bound", bool, scalar=True),
                }
            )
        entries.append(entry)
    return {
        "rule": RULE,
        "scope": SCOPE,
        "level": level,
        "state": _state(True, node, shape),
        "location": deepcopy(location),
        "relationship_ref": parent["id"],
        "structure_ref": parent["object_ref"],
        "source_relationship_location": deepcopy(parent_location),
        "component": component,
        "node_entry_count": node_count,
        "entry_count": count,
        "entries": entries,
        "entries_complete": count is not None and len(entries) == count,
    }
