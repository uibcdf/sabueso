"""Shared original support for generic retained navigation, never source merging.

The @7 navigation policy retains every source destination. Its support membership
points to one complete metadata object instead of repeating that object per link.
Earlier navigation policies and original saved formats keep their own meanings.
"""

from copy import deepcopy

from .card_exploration_verification import _historical_resolution, equal, require

RULE = "retained_context_links@7"
SUPPORT_RULE = "retained_link_support@1"
FORMAT = "sabueso.card_exploration@11"
VERIFIER = "shared_link_support_binding@1"


def _statements(support):
    return [
        statement
        for basis in support
        for statement in [
            *basis.get("statements", basis.get("source_assertions", [])),
            *basis.get("derivation_input_statements", []),
        ]
    ]


def _endpoints(explorer, source):
    access = explorer.access
    segments = source["segments"]
    relationship = statement = None
    if (
        source["kind"] == "result"
        and len(segments) == 2
        and segments[0] == {"type": "Key", "value": "items"}
    ):
        wire = access._objects[source["result_ref"]]
        if wire.get("context", {}).get("adapter") == "structure_exploration@1":
            relationship = next(
                row
                for row in access._focal.data["relationship_store"]
                if row["id"] == segments[1]["value"]
            )
    if source["kind"] == "card" and len(segments) >= 2:
        if segments[0] == {"type": "Key", "value": "relationship_store"}:
            relationship = access._resolve({**source, "segments": segments[:2]})[0]
        if segments[0] == {"type": "Key", "value": "source_assertion_store"}:
            statement = access._resolve({**source, "segments": segments[:2]})[0]
    endpoints = []
    if (
        source["kind"] == "card"
        and len(segments) == 2
        and segments[0] == {"type": "Key", "value": "entities"}
    ):
        endpoints.append(("entity", segments[1]["value"]))
    if relationship is not None:
        endpoints.extend(
            (role, relationship[f"{role}_ref"]) for role in ("subject", "object")
        )
    if statement is not None and isinstance(statement.get("subject_ref"), str):
        endpoints.append(("subject", statement["subject_ref"]))
    return endpoints


def _membership(location, statement_id):
    return [
        {
            "basis": "retained_support_membership",
            "rule": SUPPORT_RULE,
            "support_location": deepcopy(location),
            "statement_id": statement_id,
        }
    ]


def compact_related(item, origin, support):
    """Apply only to multiple distinct references; retain all rows and full basis."""
    statements = _statements(support)
    if len(statements) < 2 or len({s["id"] for s in statements}) != len(statements):
        return None
    from .card_context_navigation import _link, _link_view

    explorer = item._view._explorer
    source = item.payload_location
    support_location = explorer.access._object_location(
        {"rule": SUPPORT_RULE, "source_location": source, "support": support}
    )
    _, support_location = explorer.access._resolve(support_location)
    links = []
    for statement in statements:
        ref = statement["id"]
        membership = _membership(support_location, ref)
        if statement["state"] == "present":
            row = _link(
                explorer, "source", ref, membership, location=statement["location"]
            )
        else:
            row = {
                "role": "source",
                "label": f"Source · {ref}",
                "target_ref": ref,
                "support": membership,
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
                "availability": "missing_prerequisite",
            }
        links.append({**row, "rule": RULE})
    for role, target in _endpoints(explorer, source):
        row = _link(explorer, role, target, _membership(support_location, None))
        links.append({**row, "rule": RULE})
    return _link_view(
        explorer,
        links,
        origin,
        f"Related to {item.label}",
        source_location=source,
        support_location=support_location,
        rule=RULE,
    )


def verify_links(view):
    """Frozen @7 predicates; never call the live producer or replace stored output."""
    payload, access = view.native_payload, view._explorer.access
    require(
        set(payload)
        == {"rule", "inputs", "focal", "source_location", "links", "support_location"}
        and payload["rule"] == RULE,
        "Unsupported shared-support navigation shape.",
    )
    require(
        payload["inputs"] == view._explorer.context["captures"]
        and payload["focal"] == access._focal_key,
        "Shared support belongs to a different capture context.",
    )
    _, source = access._resolve(payload["source_location"])
    support = view._explorer._support(source)
    segments = source["segments"]
    if (
        source["kind"] == "result"
        and len(segments) == 2
        and segments[0] == {"type": "Key", "value": "items"}
    ):
        wire = access._objects[source["result_ref"]]
        if wire.get("context", {}).get("adapter") == "structure_exploration@1":
            native = (
                view._origin._selection._scientific
                if view._origin is not None
                else None
            )
            require(
                source["result_ref"] not in access._metadata_refs
                and native is not None
                and native.result_ref == source["result_ref"]
                and wire["context"]["card_ref"] == access._focal.pin
                and wire["context"]["snapshot_id"] == access._focal.snapshot,
                "Shared support has no complete original verified scientific source view.",
            )
            support = [wire["support"][segments[1]["value"]]]
    original, location = access._resolve(payload["support_location"])
    require(
        location["kind"] == "result"
        and not location["segments"]
        and equal(
            original,
            {"rule": SUPPORT_RULE, "source_location": source, "support": support},
        ),
        "Shared support differs from its complete original field/record basis.",
    )
    statements = _statements(support)
    require(
        len(statements) >= 2 and len({s["id"] for s in statements}) == len(statements),
        "Shared support requires multiple distinct original references.",
    )
    expected = [("source", s["id"]) for s in statements] + _endpoints(
        view._explorer, source
    )
    require(
        [(row["role"], row["target_ref"]) for row in payload["links"]] == expected,
        "Shared-support link membership/order differs from original references.",
    )
    for row, (role, target) in zip(payload["links"], expected):
        require(
            set(row)
            == {
                "role",
                "label",
                "target_ref",
                "support",
                "rule",
                "candidates",
                "paths",
                "blocked_paths",
                "availability",
            }
            and isinstance(row["label"], str)
            and row["rule"] == RULE
            and equal(
                row["support"],
                _membership(location, target if role == "source" else None),
            ),
            "Shared-support link membership/binding differs.",
        )
        if role == "source":
            statement = next(s for s in statements if s["id"] == target)
            resolution = {
                "candidates": [
                    {
                        "location": statement["location"],
                        "capture": access._focal_key,
                        "basis": "exact_retained_node",
                    }
                ]
                if statement["state"] == "present"
                else [],
                "paths": [],
                "blocked_paths": [],
                "availability": "available"
                if statement["state"] == "present"
                else "missing_prerequisite",
            }
        else:
            resolution = _historical_resolution(access, target)
        require(
            all(equal(row[key], value) for key, value in resolution.items()),
            "Shared-support destination differs from its original source/identity basis.",
        )


def register_bundle(bundle):
    if not any(
        record["flags"]["_link_panel"]
        and isinstance(record["native_payload"], dict)
        and record["native_payload"].get("rule") == RULE
        for record in bundle["views"].values()
    ):
        return
    from .card_exploration_assembly_v2 import ADAPTERS

    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER
    bundle["capabilities"]["scientific_saved_adapters"] = list(ADAPTERS)
    bundle.setdefault("scientific_results", {})
