"""Frozen original ligand-instance parent navigation, without identity joins.

The exact typed instance occurrence owns its parent declaration. Shared component,
instance or PDB labels never select another relationship or establish assembly,
contact or molecular identity. Keep v1 stable for independent saved reading.
"""

from copy import deepcopy

from .card_ligand_instances_v1 import context, entries

RULE = "ligand_instance_context_links@1"


def links(explorer, entry):
    """Preserve sources/endpoints and add the exact original parent declaration."""
    from .card_exploration_verification import _historical_resolution

    support = explorer._support(entry.location)
    result, seen = [], set()

    def add(role, target, basis, label, *, location=None, missing=False):
        if location is not None:
            resolution = {
                "candidates": [
                    {
                        "location": deepcopy(location),
                        "capture": explorer.access._focal_key,
                        "basis": "exact_retained_node",
                    }
                ],
                "paths": [],
                "blocked_paths": [],
                "availability": "available",
            }
        elif missing:
            resolution = {
                "candidates": [],
                "paths": [],
                "blocked_paths": [],
                "availability": "missing_prerequisite",
            }
        else:
            key = (RULE, target)
            cache = explorer._navigation_cache
            if key not in cache:
                cache[key] = _historical_resolution(explorer.access, target)
            resolution = deepcopy(cache[key])
        result.append(
            {
                "role": role,
                "label": label,
                "target_ref": target,
                "support": deepcopy(basis),
                "rule": RULE,
                **resolution,
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
            add(
                "source",
                statement["id"],
                [basis],
                "Source · " + statement["id"],
                location=statement["location"]
                if statement["state"] == "present"
                else None,
                missing=statement["state"] != "present",
            )
    parent, _ = context(explorer, entry)
    for role in ("subject", "object"):
        target = parent[f"{role}_ref"]
        add(role, target, support, f"{role.capitalize()} · {target}")
    add(
        "structure_context",
        parent["object_ref"],
        support,
        "Original structure declaration · " + parent["object_ref"],
        location={**entry.location, "segments": entry.location["segments"][:2]},
    )
    return result


def related(item):
    from .card_context_navigation import _link_view

    explorer = item._view.explorer
    return _link_view(
        explorer,
        links(explorer, item._entry),
        item.open(),
        "Original ligand-instance context · " + item.label,
        source_location=item.payload_location,
        rule=RULE,
    )


def verify_links(view):
    """Verify source occurrence, exact parent, endpoints and actual detail origin."""
    from .card_exploration_verification import equal, require

    explorer, payload = view.explorer, view.native_payload
    source = payload.get("source_location")
    original, _ = entries(explorer)
    found = [entry for entry in original if equal(entry.location, source)]
    require(len(found) == 1, "Ligand links have no exact original instance.")
    require(
        payload.get("focal") == explorer.access._focal_key
        and payload.get("inputs") == sorted(explorer.access._captures),
        "Ligand links have a foreign capture context.",
    )
    require(
        equal(payload["links"], links(explorer, found[0])),
        "Original ligand source/endpoint/parent destinations differ.",
    )
    origin = view._origin
    while origin is not None and origin._link_panel:
        origin = origin._origin
    require(
        origin is not None
        and equal(
            explorer.access._resolve(origin._selection._target["location"])[1], source
        ),
        "Ligand navigation has a different originating instance detail.",
    )
