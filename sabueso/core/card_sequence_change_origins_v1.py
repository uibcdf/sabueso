"""Actual access-instance bindings for sequence-change exploration @31.

Instance references describe runtime operations, never scientific entity identity.
Separate accesses may share captured inputs and literal byte storage while keeping
their own observed selection scope. Equal values never establish an alias.
"""

from .errors import StorageError

MEMBER = "sequence_change_access_origins"
RULE = "sequence_change_access_origins@1"


def require(condition, message):
    if not condition:
        raise StorageError(message)


def register(bundle, nodes):
    first = next(iter(nodes.values()))._explorer.access
    common = ("_captures", "_inputs", "_objects", "_locations", "_scientific_cache")
    previous = first._exploration_session.get("sequence_accesses", {})
    identities = {id(access): key for key, access in previous.items()}
    instances, views = {}, {}

    def reference(access):
        require(
            all(getattr(access, name) is getattr(first, name) for name in common),
            "Sequence-change accesses must retain their actual shared input containers.",
        )
        if id(access) not in identities:
            index = 0
            while "A" + str(index) in identities.values():
                index += 1
            identities[id(access)] = "A" + str(index)
        key = identities[id(access)]
        instances[key] = {"focal": access._focal_key}
        return key

    for key, view in nodes.items():
        views[key] = {
            "explorer": reference(view._explorer.access),
            "selection": reference(view._selection._access),
        }
    bundle[MEMBER] = {"rule": RULE, "instances": instances, "views": views}


def restore(bundle, accesses, session):
    """Restore declared instances without coalescing equal focal captures."""
    manifest = bundle[MEMBER]
    require(
        type(manifest) is dict
        and set(manifest) == {"rule", "instances", "views"}
        and manifest["rule"] == RULE,
        "Unsupported sequence-change access-origin manifest.",
    )
    instances, views = manifest["instances"], manifest["views"]
    require(
        type(instances) is dict
        and instances
        and type(views) is dict
        and set(views) == set(bundle["views"]),
        "Sequence-change access-origin closure differs.",
    )
    used = set()
    for key, row in views.items():
        require(
            type(row) is dict
            and set(row) == {"explorer", "selection"}
            and all(
                type(value) is str and value in instances for value in row.values()
            ),
            "Sequence-change view has a foreign access instance.",
        )
        for value in row.values():
            require(
                instances[value] == {"focal": bundle["views"][key]["focal"]},
                "Sequence-change access instance has a foreign focal capture.",
            )
            used.add(value)
    require(used == set(instances), "Detached sequence-change access instance.")
    first = next(iter(accesses.values()))
    restored = {}
    for key, row in instances.items():
        require(
            type(key) is str
            and key.startswith("A")
            and key[1:].isdecimal()
            and str(int(key[1:])) == key[1:]
            and row["focal"] in accesses,
            "Unknown sequence-change access instance.",
        )
        # The original _for_capture operation shares these containers and keeps
        # fresh per-instance selections/cursors. Avoid rebuilding coverage and
        # copying the complete metadata registry for every source destination.
        access = first._for_capture(row["focal"])
        access._scientific_items = dict(accesses[row["focal"]]._scientific_items)
        access._exploration_session = session
        restored[key] = access
    session["sequence_accesses"] = restored
    return restored


def verify(bundle, nodes):
    """Bind every actual node and original source-follow access boundary."""
    instances = {}
    for key, view in nodes.items():
        binding = bundle[MEMBER]["views"][key]
        for name, access in (
            ("explorer", view._explorer.access),
            ("selection", view._selection._access),
        ):
            ref = binding[name]
            require(
                instances.setdefault(ref, access) is access,
                "Sequence-change access alias differs from its recorded instance.",
            )
        parent = view._origin
        if parent is not None:
            expected_switch = (
                view._explorer._origin is parent
                and parent._link_panel
                and not view._context_only
            )
            require(
                (view._explorer.access is not parent._explorer.access)
                == expected_switch,
                "Sequence-change source operation lost its actual access boundary.",
            )
    require(
        len({id(access) for access in instances.values()}) == len(instances),
        "Distinct recorded sequence-change accesses were merged.",
    )
