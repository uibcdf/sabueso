"""Frozen construction of explicit local links and original endpoint decisions.

These helpers describe captured destinations. They never infer entity identity,
acquire records or choose a revision. Caller policies own source admission.
"""

from copy import deepcopy


def local_link(explorer, rule, role, target, support, label, location):
    return {
        "rule": rule,
        "role": role,
        "target_ref": target,
        "label": label,
        "support": deepcopy(support),
        "candidates": [
            {
                "capture": explorer.access._focal_key,
                "location": deepcopy(location),
                "basis": "exact_retained_node",
            }
        ]
        if location is not None
        else [],
        "paths": [],
        "blocked_paths": [],
        "availability": "available" if location is not None else "missing_prerequisite",
    }


def endpoint_link(explorer, rule, role, target, support):
    from .card_exploration_verification import _historical_resolution

    key = ("original_endpoint_resolution@1", target)
    if key not in explorer._navigation_cache:
        explorer._navigation_cache[key] = _historical_resolution(
            explorer.access, target
        )
    return {
        "rule": rule,
        "role": role,
        "target_ref": target,
        "label": f"{role.capitalize()} · {target}",
        "support": deepcopy(support),
        **deepcopy(explorer._navigation_cache[key]),
    }


def source_links(explorer, rule, support):
    result, seen = [], set()
    for basis in support:
        for statement in [
            *basis.get("statements", basis.get("source_assertions", [])),
            *basis.get("derivation_input_statements", []),
        ]:
            ref = statement["id"]
            if ref in seen:
                continue
            seen.add(ref)
            result.append(
                local_link(
                    explorer,
                    rule,
                    "source",
                    ref,
                    [basis],
                    "Source · " + ref,
                    statement["location"] if statement["state"] == "present" else None,
                )
            )
    return result
