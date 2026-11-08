"""Explicit @23 header and exact-origin checks over unchanged frozen science.

The @21 verifier receives a private header projection, never modified scientific
or view values. @23 integrity is checked first; its additional originating-node
manifest is then checked against the complete restored graph.
"""

from . import card_exploration_molecule_activity_v2 as molecule
from . import card_exploration_verification_v21 as original
from .card_exploration_molecule_activity import require
from .snapshot import canonical_json, digest


def _projection(bundle):
    return {
        **{
            key: value
            for key, value in bundle.items()
            if key not in ("digests", "bundle_digest", molecule.MEMBER)
        },
        "format": molecule.original.FORMAT,
        "producer": {
            **bundle["producer"],
            "verifier": molecule.original.VERIFIER,
        },
    }


def verify_bundle(bundle, expected_digest):
    from .card_exploration_storage import _seal

    require(
        type(bundle) is dict
        and bundle.get("format") == molecule.FORMAT
        and type(bundle.get("producer")) is dict
        and bundle["producer"].get("verifier") == molecule.VERIFIER,
        "Unsupported exact-origin exploration binding.",
    )
    actual = digest(
        canonical_json(
            {key: value for key, value in bundle.items() if key != "bundle_digest"}
        )
    )
    members = {
        key: digest(canonical_json(value))
        for key, value in bundle.items()
        if key not in ("digests", "bundle_digest")
    }
    require(
        actual == bundle.get("bundle_digest")
        and (expected_digest is None or actual == expected_digest)
        and members == bundle.get("digests"),
        "Exact-origin exploration integrity binding differs.",
    )
    roots = bundle.get(molecule.MEMBER)
    require(
        type(roots) is dict
        and set(roots) == {"rule", "origins"}
        and roots["rule"] == molecule.ROOT_RETURN_POLICY
        and type(roots["origins"]) is dict
        and all(
            type(key) is str and type(value) is str
            for key, value in roots["origins"].items()
        ),
        "Unsupported exact originating-root policy or manifest.",
    )
    original.verify_bundle(_seal(_projection(bundle)), None)


def verify_views(bundle, nodes):
    original.verify_views(_projection(bundle), nodes)
    molecule.verify_roots(bundle, nodes)
