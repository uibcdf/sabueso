"""Exact literal request admission for original scientific explanations (#176).

This transport check precedes frozen scientific verification. It preserves each
historical rule's meaning and reads only retained locations and capture context.
"""

from .card_access import _handle
from .card_exploration_history import _require_matches
from .errors import StorageError

RULE = "scientific_explanation_request_binding@1"
ADAPTERS = {
    "ligand_site_exploration@1",
    "quaternary_exploration@1",
    "assembly_generation_exploration@1",
}


def require(condition, message):
    if not condition:
        raise StorageError(message)


def verify(view):
    access, selection = view._explorer.access, view._selection
    if selection._scientific is not None:
        return
    native, full = access._resolve(selection._target["location"])
    if full["kind"] != "result":
        return
    wire = access._objects[full["result_ref"]]
    path = full["segments"]
    if not (
        isinstance(wire, dict)
        and wire.get("context", {}).get("adapter") in ADAPTERS
        and len(path) == 2
        and path[0] == {"type": "Key", "value": "explanations"}
    ):
        return
    require(
        path[1]["type"] == "Key" and path[1]["value"] in wire["explanations"],
        "Scientific explanation has no original typed item.",
    )
    context = access._resolve(selection._context_location)[0]
    require(set(context) == {"context", "request"}, "Unknown explanation context.")
    request = context["request"]
    require(
        set(request) == {"operation", "location", "text_slice"}
        and request["operation"] == selection._operation == "read"
        and request["text_slice"] is selection._slice is None
        and not selection._fields
        and selection._outcome_override is None,
        "Scientific explanation differs from its original literal read request.",
    )
    require(
        access._resolve(request["location"])[1] == full,
        "Scientific explanation request targets another original node.",
    )
    require(
        context["context"]["mode"] in ("live", "saved"),
        "Invalid original explanation request mode.",
    )
    _require_matches(
        {**context["context"], "mode": "live"},
        {**access.context, "mode": "live"},
        "scientific explanation original capture context",
    )
    ref = _handle(
        "XR_",
        {
            "format": "literal_access_result@1",
            "inputs": sorted(access._captures),
            "request": request,
        },
    )
    require(
        selection.result_ref == ref
        and selection.selection_ref
        == _handle(
            "XA_",
            {
                "format": "card_access_selection@1",
                "result_ref": ref,
                "request": request,
            },
        ),
        "Scientific explanation selection identity differs from its request.",
    )
    _require_matches(
        selection._target,
        {
            "node_type": "object",
            "size": len(native),
            "location": selection._target["location"],
            "owner": {"result_ref": full["result_ref"]},
        },
        "scientific explanation original node scope",
    )
