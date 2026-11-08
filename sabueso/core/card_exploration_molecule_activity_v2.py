"""Exact-origin molecule navigation over the unchanged original scientific wire.

Logical exploration @23 adds an explicit originating-node manifest and typed
return predicates. Original @21 predicates remain unchanged and supply the
scientific, source, quantity and earlier navigation checks.
"""

from copy import copy
from dataclasses import replace

from . import card_exploration_molecule_activity as original
from .snapshot import canonical_json

FORMAT = "sabueso.card_exploration@23"
VERIFIER = "molecule_activity_exploration_binding@2"
ROOT_RETURN_POLICY = "molecule_activity_root_selection_exact_origin@1"
MEMBER = "molecule_activity_root_returns"


def descriptor():
    result = original.descriptor()
    result["root_return_policy"] = ROOT_RETURN_POLICY
    return result


def _originating_root(view):
    parent = view._origin
    if not (
        original.is_view(view)
        and parent is not None
        and parent._link_panel
        and original.is_context(parent)
    ):
        return None
    root = original._root_view(parent)
    original.require(root is not None, "Molecule return lost its originating root.")
    for candidate in (view, root):
        original.require(
            candidate._explorer.access._focal_key == parent._explorer.access._focal_key
            and candidate._explorer.access._inputs == parent._explorer.access._inputs
            and candidate._explorer._origin is parent._explorer._origin,
            "Molecule return crossed its originating explorer scope.",
        )
    navigation = parent._context_override["molecule_activity_navigation"]
    original.same(
        original._selection_binding(root),
        navigation["molecule_root_selection"],
        "typed originating root request",
    )
    original.same(
        original._selection_binding(view),
        original._selection_binding(root),
        "typed originating root return",
    )
    return root


def verify_view(view, record):
    """Retain all original predicates and additionally bind typed root returns."""
    original.verify_view(view, record)
    _originating_root(view)


def root_manifest(nodes):
    identities = {id(view): key for key, view in nodes.items()}
    roots = {}
    for key, view in nodes.items():
        root = _originating_root(view)
        if root is None:
            continue
        original.require(
            id(root) in identities,
            "Molecule return has an unretained originating root instance.",
        )
        roots[key] = identities[id(root)]
    return {"rule": ROOT_RETURN_POLICY, "origins": roots}


def register_roots(bundle, nodes):
    bundle[MEMBER] = root_manifest(nodes)


def verify_roots(bundle, nodes):
    original.same(
        bundle[MEMBER], root_manifest(nodes), "exact originating root instances"
    )


def register_bundle(bundle, objects, access):
    """Choose a new binding only for the new interpretation, never for old resaves."""
    session = access._exploration_session or {}
    if (
        session.get("format") == original.FORMAT
        or session.get("molecule_activity_root_policy") == original.ROOT_RETURN_EQUALITY
    ):
        return original.register_bundle(bundle, objects, access)
    # The unchanged original writer authenticates scientific membership/order.
    # Only its old-format eligibility check needs an explicit private projection.
    projected = copy(access)
    projected._exploration_session = {**session, "format": original.FORMAT}
    original.register_bundle(bundle, objects, projected)
    if bundle["format"] != original.FORMAT:
        return
    bundle["format"] = FORMAT
    bundle["producer"]["verifier"] = VERIFIER


def verification_report(bundle):
    report = original.verification_report(bundle)
    report.update(
        verifier=VERIFIER,
        verified_navigation_policies=[ROOT_RETURN_POLICY],
        originating_root_instances="verified_against_exact_retained_origin_chain",
    )
    return report


def saved_declared_destination(explorer, candidate, origin):
    """Reuse original destination predicates with explicit @23 eligibility."""
    from .card_exploration import CardExplorer

    session, access = explorer._session, explorer.access
    if (
        explorer.mode != "saved"
        or session.get("format") != FORMAT
        or access.profile != "protein"
        or origin is None
        or not origin._link_panel
        or origin.native_payload.get("rule")
        not in ("retained_context_links@2", "retained_context_links@7")
    ):
        return None
    _, full = access._resolve(candidate["location"])
    captured = access._captures[candidate["capture"]]
    if (
        full["kind"] != "card"
        or full["segments"]
        or full["card_ref"] != captured.pin
        or full["snapshot_id"] != captured.snapshot
        or not any(
            canonical_json(candidate) == canonical_json(value)
            for entry in origin._selected
            for value in entry.value["candidates"]
        )
    ):
        return None
    choices = [
        view
        for view in session.get("original_nodes", {}).values()
        if view._route_catalog
        and view.title == "Card overview"
        and view.presentation == "summary"
        and view.request is None
        and view._display_request is None
        and view._explorer.access._focal_key == candidate["capture"]
        and view._explorer.access._inputs == access._inputs
        and view._explorer.access.profile == "small_molecule"
        and original._same_original_history(view._origin, origin)
    ]
    if not choices:
        return None
    first = choices[0]
    original.require(
        all(
            canonical_json(original._selection_binding(view))
            == canonical_json(original._selection_binding(first))
            and canonical_json(view.native_payload)
            == canonical_json(first.native_payload)
            for view in choices
        ),
        "Recorded molecule destination overviews disagree under the same history.",
    )
    destination = object.__new__(CardExplorer)
    destination._access = access._for_capture(candidate["capture"])
    destination._coverage_result = None
    destination._origin = origin
    destination._navigation_cache = explorer._navigation_cache
    destination._session = session
    return replace(first, _explorer=destination, _origin=origin)
