"""Versioned sharing for explicit variant tissue exploration @29, independent of identity.

The representation keeps every logical value and list occurrence. Its Merkle
records share storage only; equal records never establish molecular identity.
Original exploration verifiers receive the complete logical views unchanged.
"""

import math

from .errors import ArgumentError, StorageError
from .snapshot import canonical_json, digest

FORMAT = "sabueso.card_exploration@30"
RULE = "shared_exploration_values@9"
VERIFIER = "shared_exploration_values_binding@9"
LOGICAL_LIMIT = 256 * 1024**2
PACK_THRESHOLD = 16 * 1024**2
MIN_SAVING = 1024**2
TEXT_THRESHOLD = 256
MEMO_LIMIT = 4096
BASE_FORMATS = {"sabueso.card_exploration@29"}
BASE_MEMBERS = {
    "format",
    "producer",
    "root_view_ref",
    "root_navigation_ref",
    "cards",
    "inputs",
    "objects",
    "locations",
    "views",
    "navigation",
    "capabilities",
    "presentation_metadata",
    "molecule_activity_crossings",
    "molecule_activity_operations",
    "molecule_activity_root_returns",
}
HEADER_NAVIGATIONS = {
    "variant_context_links@1",
    "clinical_context_links@1",
    "disease_association_context_links@1",
    "molecule_activity_context_links@1",
    "literature_context_links@1",
    "bioactivity_context_links@1",
    "structure_declaration_context_links@3",
    "assembly_generation_links@3",
    "assembly_component_list_links@1",
    "assembly_component_detail_links@1",
    "retained_context_links@5",
    "retained_context_links@6",
    "retained_context_links@7",
    "retained_context_links@8",
}


def _require(condition, message):
    if not condition:
        raise StorageError(message)


def _check_size(size, limit):
    if limit is not None and size > limit:
        raise ArgumentError(
            f"Exploration requires at least {size} logical JSON bytes, exceeding "
            f"max_logical_bytes={limit}; increase max_logical_bytes explicitly "
            "or pass max_logical_bytes=None deliberately. No partial result is returned."
        )


def _scalar_size(value):
    if isinstance(value, float):
        _require(math.isfinite(value), "Nonfinite shared exploration value.")
    _require(
        value is None or isinstance(value, (str, bool, int, float)),
        "Unsupported shared exploration scalar.",
    )
    return len(canonical_json(value).encode("utf-8"))


def measure(value, limit=LOGICAL_LIMIT):
    """Count canonical logical bytes without constructing the expanded JSON text."""
    memo, active, scalars = {}, set(), {}

    def visit(node):
        if not isinstance(node, (dict, list, tuple)):
            _require(
                node is None or isinstance(node, (str, bool, int, float)),
                "Unsupported shared exploration scalar.",
            )
            key = (type(node), float(node).hex() if isinstance(node, float) else node)
            if key not in scalars:
                scalars[key] = _scalar_size(node)
            return scalars[key]
        identity = id(node)
        if identity in memo:
            return memo[identity]
        _require(identity not in active, "Cyclic logical exploration value.")
        active.add(identity)
        if isinstance(node, dict):
            _require(
                all(isinstance(key, str) for key in node),
                "Shared exploration mappings require string keys.",
            )
            size = 2 + max(0, len(node) - 1)
            for key, child in node.items():
                size += visit(key) + 1 + visit(child)
                _check_size(size, limit)
        else:
            size = 2 + max(0, len(node) - 1)
            for child in node:
                size += visit(child)
                _check_size(size, limit)
        active.remove(identity)
        memo[identity] = size
        return size

    try:
        size = visit(value)
        _check_size(size, limit)
        return size
    finally:
        memo.clear()
        active.clear()
        scalars.clear()


def pack(
    bundle, limit=LOGICAL_LIMIT, *, threshold=PACK_THRESHOLD, min_saving=MIN_SAVING
):
    """Encode a large unsealed original bundle; smaller bundles keep their format."""
    _require(bundle.get("format") in BASE_FORMATS, "Unsupported original format.")
    _require(
        not ({"digests", "bundle_digest"} & set(bundle)),
        "Shared packing requires an unsealed original bundle.",
    )
    logical_bytes = measure(bundle, limit)
    if logical_bytes <= threshold:
        return bundle
    values, memo = {}, {}
    pool_fields_size = 0

    def encode(value):
        nonlocal pool_fields_size
        if not isinstance(value, (dict, list, tuple)):
            if not isinstance(value, str) or _scalar_size(value) < TEXT_THRESHOLD:
                return value
            record = {"kind": "text", "value": value}
        else:
            if len(memo) >= MEMO_LIMIT:
                memo.clear()
            identity = id(value)
            if identity in memo:
                return memo[identity]
            record = (
                {
                    "kind": "mapping",
                    "items": [[key, encode(value[key])] for key in sorted(value)],
                }
                if isinstance(value, dict)
                else {"kind": "array", "items": [encode(v) for v in value]}
            )
        encoded_record = canonical_json(record)
        ref = "SV_" + digest(encoded_record)
        if ref in values:
            _require(values[ref] == record, "Shared value digest collision.")
        else:
            values[ref] = record
            pool_fields_size += (
                _scalar_size(ref) + 1 + len(encoded_record.encode("utf-8"))
            )
        token = {"value_ref": ref}
        if isinstance(value, (dict, list, tuple)):
            memo[id(value)] = token
        return token

    root = encode(bundle)
    memo.clear()
    packed = {
        "format": FORMAT,
        "producer": {
            "sabueso_version": bundle["producer"]["sabueso_version"],
            "verifier": VERIFIER,
            "scope": "Exact shared JSON representation; original scientific and navigation bindings retain their own verifiers.",
        },
        "representation": RULE,
        "logical_bytes": logical_bytes,
        "root": root,
        "values": values,
    }
    pool_size = 2 + max(0, len(values) - 1) + pool_fields_size
    physical_size = (
        measure({key: value for key, value in packed.items() if key != "values"}, None)
        + _scalar_size("values")
        + 2
        + pool_size
    )
    return packed if logical_bytes - physical_size >= min_saving else bundle


def sealed_size(bundle):
    """Exact canonical size including integrity fields, before allocating that text."""
    placeholder = digest("")
    digests = {key: placeholder for key in bundle}
    return (
        measure(bundle, None)
        + _scalar_size("digests")
        + 1
        + measure(digests, None)
        + 1
        + _scalar_size("bundle_digest")
        + 1
        + _scalar_size(placeholder)
        + 1
    )


def unpack(
    bundle, expected_digest=None, *, limit=LOGICAL_LIMIT, component_limit=64 * 1024**2
):
    """Verify the physical DAG and its logical work budget before reconstruction."""
    _require(
        type(bundle) is dict
        and set(bundle)
        == {
            "format",
            "producer",
            "representation",
            "logical_bytes",
            "root",
            "values",
            "digests",
            "bundle_digest",
        }
        and bundle["format"] == FORMAT
        and bundle["representation"] == RULE,
        "Unsupported shared exploration representation.",
    )
    producer = bundle["producer"]
    _require(
        type(producer) is dict
        and set(producer) == {"sabueso_version", "verifier", "scope"}
        and producer["verifier"] == VERIFIER
        and type(producer["sabueso_version"]) is str
        and bool(producer["sabueso_version"])
        and type(producer["scope"]) is str,
        "Unsupported shared exploration verifier.",
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
        "Shared exploration integrity binding differs.",
    )
    values = bundle["values"]
    _require(type(values) is dict and values, "Missing shared exploration values.")

    def reference(token):
        if type(token) is dict:
            _require(
                set(token) == {"value_ref"}
                and type(token["value_ref"]) is str
                and token["value_ref"] in values,
                "Unknown or malformed shared value reference.",
            )
            return token["value_ref"]
        _scalar_size(token)
        return None

    root = reference(bundle["root"])
    _require(root is not None, "Shared exploration requires an original object root.")
    children, local_size = {}, {}
    for key, record in values.items():
        _require(
            type(record) is dict and key == "SV_" + digest(canonical_json(record)),
            "Shared exploration value digest differs.",
        )
        kind = record.get("kind")
        if kind == "text":
            _require(
                set(record) == {"kind", "value"} and type(record["value"]) is str,
                "Invalid shared text.",
            )
            size = _scalar_size(record["value"])
            _require(size >= TEXT_THRESHOLD, "Noncanonical shared text.")
            tokens = []
        elif kind in ("mapping", "array"):
            _require(
                set(record) == {"kind", "items"} and type(record["items"]) is list,
                "Invalid shared collection.",
            )
            items = record["items"]
            if kind == "mapping":
                _require(
                    all(
                        type(p) is list and len(p) == 2 and type(p[0]) is str
                        for p in items
                    ),
                    "Invalid shared mapping entries.",
                )
                keys = [p[0] for p in items]
                _require(
                    keys == sorted(set(keys)),
                    "Repeated or unordered shared mapping key.",
                )
                tokens = [p[1] for p in items]
                size = (
                    2 + max(0, len(items) - 1) + sum(_scalar_size(k) + 1 for k in keys)
                )
            else:
                tokens = items
                size = 2 + max(0, len(items) - 1)
        else:
            raise StorageError("Unsupported shared value kind.")
        refs = []
        for token in tokens:
            ref = reference(token)
            if ref is None:
                size += _scalar_size(token)
            else:
                refs.append(ref)
        children[key], local_size[key] = refs, size

    # Iterative traversal rejects cycles and computes logical bytes with repeated
    # references counted each time, before any decoded graph is instantiated.
    sizes, order, active = {}, [], set()
    pending = [(root, False)]
    while pending:
        key, leaving = pending.pop()
        if key in sizes:
            continue
        if leaving:
            size = local_size[key] + sum(sizes[ref] for ref in children[key])
            _check_size(size, limit)
            sizes[key] = size
            active.remove(key)
            order.append(key)
        else:
            _require(key not in active, "Cyclic shared exploration reference.")
            active.add(key)
            pending.append((key, True))
            pending.extend((ref, False) for ref in reversed(children[key]))
    _require(set(sizes) == set(values), "Unreachable shared exploration value.")
    _require(
        type(bundle["logical_bytes"]) is int and bundle["logical_bytes"] == sizes[root],
        "Shared logical byte count differs.",
    )
    root_record = values[root]
    _require(
        root_record["kind"] == "mapping", "Original exploration root must be an object."
    )
    header = dict(root_record["items"])
    base_format = header.get("format")
    _require(
        type(base_format) is str and base_format in BASE_FORMATS,
        "Unsupported original exploration format.",
    )
    expected_members = BASE_MEMBERS | (
        {"scientific_results"} if base_format != "sabueso.card_exploration@1" else set()
    )
    _require(
        set(header) == expected_members,
        "Missing or unsupported original bundle member.",
    )

    def token_size(token):
        return sizes[token["value_ref"]] if type(token) is dict else _scalar_size(token)

    # A small graph cannot inflate one value/header beyond the original decoded
    # ceiling. Only repetition between views gets the separate logical budget.
    from .exploration_transport import _check

    non_views = sizes[root] - token_size(header["views"]) - _scalar_size("views") - 2
    _check("max_decoded_bytes", non_views, component_limit)
    views_ref = reference(header["views"])
    _require(
        views_ref is not None and values[views_ref]["kind"] == "mapping",
        "Original views require an object.",
    )
    for _, token in values[views_ref]["items"]:
        _check("max_decoded_bytes", token_size(token), component_limit)
    decoded = {}

    def value(token):
        return decoded[token["value_ref"]] if type(token) is dict else token

    for key in order:
        record = values[key]
        decoded[key] = (
            record["value"]
            if record["kind"] == "text"
            else {k: value(v) for k, v in record["items"]}
            if record["kind"] == "mapping"
            else [value(v) for v in record["items"]]
        )
    logical = decoded[root]
    _require(
        type(logical) is dict
        and logical.get("format") in BASE_FORMATS
        and not ({"digests", "bundle_digest"} & set(logical))
        and type(logical.get("producer")) is dict
        and logical.get("producer", {}).get("sabueso_version")
        == producer["sabueso_version"],
        "Shared representation does not bind an original exploration bundle.",
    )
    return logical, {
        "representation_verifier": VERIFIER,
        "representation_rule": RULE,
        "storage_format": FORMAT,
        "logical_format": logical["format"],
        "logical_bytes": sizes[root],
        "shared_values": len(values),
        "physical_bundle_digest": actual,
    }


def verify_header(logical, original_verifier):
    """Reuse frozen original header predicates through an explicitly bounded view projection.

    Physical integrity has already bound every complete view. Original per-view
    predicates subsequently verify the complete logical data, without projection.
    No digest of a fully expanded, repetitive JSON document is needed.
    """
    from .card_exploration_storage import _seal

    # Original headers only ask whether one of these finite marker types exists.
    # Keep one representative per type, rather than hashing all display state.
    # Every complete original view is verified separately after restoration.
    headers, seen = {}, set()
    for key, record in logical["views"].items():
        payload = record["native_payload"]
        rule = payload.get("rule") if isinstance(payload, dict) else None
        if (
            record["flags"]["_link_panel"]
            and isinstance(rule, str)
            and rule in HEADER_NAVIGATIONS
            and rule not in seen
        ):
            headers[key] = {
                "flags": {"_link_panel": True},
                "native_payload": {"rule": rule},
            }
            seen.add(rule)
    projection = {**logical, "views": headers}
    original_verifier(_seal(projection), None)
