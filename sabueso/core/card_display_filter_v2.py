"""Explicit retained-cell filtering, with original display-history verification.

The outer format changes display selection only. Its payload retains the exact
original scientific/storage format; it is not a standalone legacy display bundle.
"""

from contextlib import contextmanager
from contextvars import ContextVar

from .errors import StorageError
from .snapshot import canonical_json, digest

RULE = "retained_cell_filter@2"
FORMAT = "sabueso.card_exploration@14"
VERIFIER = "retained_cell_filter_binding@1"
SCOPE = "Versioned retained-cell display selection; original science and source bindings unchanged."
_VERIFICATION = ContextVar("sabueso_display_filter_verification", default=None)
PAYLOAD_FORMATS = {f"sabueso.card_exploration@{i}" for i in range(1, 14)}


def _require(condition, message):
    if not condition:
        raise StorageError(message)


def legacy_verification():
    return _VERIFICATION.get() == "legacy"


@contextmanager
def verification(policy):
    """Scope frozen predicates without changing user navigation or other tasks."""
    token = _VERIFICATION.set(policy or "legacy")
    try:
        yield
    finally:
        _VERIFICATION.reset(token)


def marked(operation):
    return isinstance(operation, dict) and operation.get("filter_policy") == RULE


def validate_records(bundle, enabled):
    """Reject policy smuggling and ambiguous display requests before restoration."""
    found = False
    for record in bundle["views"].values():
        operation = record["flags"]["_display_request"]
        if not isinstance(operation, dict):
            continue
        if "filter_policy" in operation:
            _require(
                enabled
                and operation["filter_policy"] == RULE
                and operation.get("operation") == "filter"
                and set(operation) - {"equals_encoding"}
                == {"operation", "column", "equals", "filter_policy"},
                "Unsupported or unbound retained display-filter policy.",
            )
            previous = bundle["views"].get(record["origin"])
            _require(
                previous is not None, "Retained display filter lost its original view."
            )
            flags, original = record["flags"], previous["flags"]
            _require(
                original["_status"] not in ("ok", "empty")
                and not (original["_link_panel"] and original["_status"] == "ambiguous")
                and flags["_status"] == original["_status"]
                and flags["_reason"] == original["_reason"],
                "Retained display filtering changed the underlying scientific outcome.",
            )
            found = True
        elif enabled and operation.get("operation") == "filter":
            previous = bundle["views"].get(record["origin"])
            if previous is not None:
                flags = previous["flags"]
                _require(
                    flags["_status"] in ("ok", "empty")
                    or (flags["_link_panel"] and flags["_status"] == "ambiguous"),
                    "A retained-cell filter requires its explicit policy.",
                )
    _require(not enabled or found, "Missing retained-cell filter operation.")
    return found


def needed(bundle):
    """Only operations using the new semantics need an outer version boundary."""
    found = any(
        isinstance(operation := record["flags"]["_display_request"], dict)
        and "filter_policy" in operation
        for record in bundle["views"].values()
    )
    validate_records(bundle, found)
    return found


def wrap(payload):
    return {
        "format": FORMAT,
        "producer": {
            "sabueso_version": payload["producer"]["sabueso_version"],
            "verifier": VERIFIER,
            "scope": SCOPE,
        },
        "filter_policy": RULE,
        "payload": payload,
    }


def unwrap(bundle, expected_digest):
    """Verify one physical envelope; recursive policy wrappers are unsupported."""
    _require(
        type(bundle) is dict
        and set(bundle)
        == {
            "format",
            "producer",
            "filter_policy",
            "payload",
            "digests",
            "bundle_digest",
        }
        and bundle["format"] == FORMAT
        and bundle["filter_policy"] == RULE,
        "Unsupported retained display-filter envelope.",
    )
    producer = bundle["producer"]
    _require(
        type(producer) is dict
        and set(producer) == {"sabueso_version", "verifier", "scope"}
        and type(producer["sabueso_version"]) is str
        and bool(producer["sabueso_version"])
        and producer["verifier"] == VERIFIER
        and producer["scope"] == SCOPE,
        "Unsupported retained display-filter verifier.",
    )
    members = {
        key: digest(canonical_json(value))
        for key, value in bundle.items()
        if key not in ("digests", "bundle_digest")
    }
    actual = digest(
        canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
    )
    _require(
        members == bundle["digests"]
        and actual == bundle["bundle_digest"]
        and (expected_digest is None or actual == expected_digest),
        "Retained display-filter envelope digest differs.",
    )
    payload = bundle["payload"]
    _require(
        type(payload) is dict
        and payload.get("format") in PAYLOAD_FORMATS
        and isinstance(payload.get("producer"), dict)
        and payload["producer"].get("sabueso_version") == producer["sabueso_version"],
        "Unsupported or recursively wrapped display-filter payload.",
    )
    return payload, {
        "display_filter_policy": RULE,
        "display_filter_verifier": VERIFIER,
        "storage_format": FORMAT,
        "payload_storage_format": payload["format"],
        "physical_bundle_digest": actual,
        "payload_bundle_digest": payload.get("bundle_digest"),
        "independent_expected_digest": expected_digest is not None,
    }
