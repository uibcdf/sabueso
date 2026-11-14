"""Original Deck readings composed from unchanged native Card bundles.

Version 1 binds literal presentation operations to captured occurrences. It does
not interpret scientific values or rebuild Cards. Card bundles deliberately keep
their existing independent verifiers; multiple focal bundles can repeat capture
data. Byte/logical ceilings are not whole-process memory guarantees.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from sabueso._private.argdigest import arg_digest

from . import exploration_transport as transport
from .card_exploration_storage import _restore as _restore_card
from .card_exploration_storage import _unique
from .deck_exploration import DeckExplorer, DeckView
from .errors import ArgumentError, StorageError
from .snapshot import SNAPSHOT_ID, canonical_json, digest

FORMAT = "sabueso.deck_exploration@1"
VIEW_LIMIT = 1024


def _require(condition, message):
    if not condition:
        raise StorageError(message)


def _keys(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def _seal(bundle):
    return {**bundle, "bundle_digest": digest(canonical_json(bundle))}


def _views(view, additional):
    records = {}

    def retain(item):
        _require(item._owner is view._owner, "Foreign Deck view in saved context.")
        trail = []
        while item is not None and item.view_ref not in records:
            trail.append(item)
            _require(len(trail) + len(records) <= VIEW_LIMIT, "Too many Deck views.")
            item = item._origin
        for item in reversed(trail):
            records[item.view_ref] = {
                "view_ref": item.view_ref,
                "positions": list(item._positions),
                "request": item.request,
                "origin": item._origin.view_ref if item._origin is not None else None,
            }

    for item in (*additional, view):
        retain(item)
    return list(records.values())


def save_deck_exploration(
    view,
    path,
    *,
    overwrite=False,
    compression="none",
    max_encoded_bytes=transport.BYTE_LIMIT,
    max_decoded_bytes=transport.BYTE_LIMIT,
    max_logical_bytes=268435456,
    application=None,
    additional=(),
):
    if (
        not isinstance(path, (str, os.PathLike))
        or not str(path)
        or type(overwrite) is not bool
    ):
        raise ArgumentError("Use a nonempty file path and boolean overwrite.")
    for name, value in (
        ("max_encoded_bytes", max_encoded_bytes),
        ("max_decoded_bytes", max_decoded_bytes),
        ("max_logical_bytes", max_logical_bytes),
    ):
        transport.byte_budget(name, value)
    codec, backend = transport.encoder(compression)
    owner = view._owner
    cards = {}
    if owner._saved_bundles is not None:
        cards = owner._saved_bundles
    else:
        # Public Card saving owns preparation/verification. Only disposable local
        # components are written; no alternate Card wire codec is introduced.
        with tempfile.TemporaryDirectory(
            prefix="sabueso-deck-components-"
        ) as directory:
            total = 0
            for position, key in enumerate(owner._inputs):
                if key in cards:
                    continue
                component = Path(directory) / "card.json"
                owner._open(position, owner.overview()).overview().save(
                    component,
                    overwrite=True,
                    max_encoded_bytes=max_decoded_bytes,
                    max_decoded_bytes=max_decoded_bytes,
                    max_logical_bytes=max_logical_bytes,
                )
                total += component.stat().st_size
                transport._check("max_decoded_bytes", total, max_decoded_bytes)
                cards[key] = json.loads(
                    component.read_bytes(), object_pairs_hook=_unique
                )
    bundle = _seal(
        {
            "format": FORMAT,
            "metadata": owner.metadata,
            "inputs": list(owner._inputs),
            "capture_ref": owner._capture_ref,
            "cards": cards,
            "views": _views(view, additional),
            "root_view_ref": view.view_ref,
            "application": application,
        }
    )
    raw = canonical_json(bundle).encode("utf-8")
    transport._check("max_decoded_bytes", len(raw), max_decoded_bytes)
    _restore(bundle, bundle["bundle_digest"], max_logical_bytes, max_decoded_bytes)
    destination, temporary = Path(path), None
    try:
        fd, temporary = tempfile.mkstemp(
            dir=destination.parent, prefix=".sabueso-deck-reading-"
        )
        with os.fdopen(fd, "wb") as stream:
            receipt = transport.write(
                stream, raw, compression, codec, backend, max_encoded_bytes
            )
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)
    except OSError as exc:
        raise StorageError(f"Cannot save Deck reading: {exc}") from exc
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return {
        "path": str(destination),
        "bundle_digest": bundle["bundle_digest"],
        "root_view_ref": view.view_ref,
        "transport": receipt,
    }


def _positions(owner, request, origin):
    """Frozen v1 literal operations; never call current Deck/scientific readers."""
    _require(isinstance(request, dict), "Malformed original Deck request.")
    operation = request.get("operation")
    if operation == "overview":
        _require(_keys(request, {"operation"}) and origin is None, "Invalid Deck root.")
        return tuple(range(len(owner._inputs)))
    _require(origin is not None, "A selected Deck view requires its original parent.")
    positions = origin._positions
    if operation == "select":
        _require(
            _keys(request, {"operation", "member_refs"}), "Invalid Deck selection."
        )
        refs = request["member_refs"]
        _require(
            isinstance(refs, list) and all(isinstance(r, str) for r in refs),
            "Invalid member references.",
        )
        available = {owner._member_refs[p]: p for p in positions}
        _require(
            len(set(refs)) == len(refs) and all(r in available for r in refs),
            "Foreign or repeated selection.",
        )
        return tuple(available[r] for r in refs)
    if operation == "filter":
        _require(
            _keys(request, {"operation", "text", "scope"})
            and isinstance(request["text"], str)
            and request["scope"] == "literal identifier/nature",
            "Invalid Deck filter.",
        )
        needle = request["text"].casefold()
        return tuple(
            p
            for p in positions
            if needle in _label(owner, p).casefold()
            or needle in (_kind(owner, p) or "").casefold()
        )
    _require(
        operation == "sort"
        and _keys(request, {"operation", "column", "descending"})
        and request["column"] in ("label", "kind")
        and type(request["descending"]) is bool,
        "Unknown Deck operation or sort scope.",
    )
    get = _label if request["column"] == "label" else _kind
    present = [p for p in positions if get(owner, p) is not None]
    missing = [p for p in positions if get(owner, p) is None]
    return tuple(
        sorted(present, key=lambda p: get(owner, p), reverse=request["descending"])
        + missing
    )


def _label(owner, position):
    capture = owner._captures[owner._inputs[position]]
    return capture.pin or capture.snapshot


def _kind(owner, position):
    value = owner._captures[owner._inputs[position]].data["meta"].get("entity_type")
    return value if isinstance(value, str) else None


def _application(value, views):
    if value is None:
        return
    _require(
        _keys(value, {"format", "metadata_open", "current", "history"})
        and value["format"] == "sabueso.deck_application@1"
        and type(value["metadata_open"]) is bool
        and isinstance(value["history"], list)
        and len(value["history"]) <= 256,
        "Unknown or malformed Deck application context.",
    )
    for state in [value["current"], *value["history"]]:
        _require(
            _keys(state, {"view_ref", "offset"})
            and isinstance(state["view_ref"], str)
            and state["view_ref"] in views
            and type(state["offset"]) is int
            and 0 <= state["offset"] < max(1, len(views[state["view_ref"]]._positions)),
            "Foreign Deck application selection or page.",
        )
        # Receive the exact finite page, including shortened oversized-row pages.
        view, cursor = views[state["view_ref"]], None
        while True:
            page = view.page(limit=40, max_bytes=1048576, cursor=cursor)
            if page["offset"] == state["offset"]:
                break
            _require(
                page["offset"] < state["offset"] and page["next_cursor"] is not None,
                "Unknown Deck application page.",
            )
            cursor = page["next_cursor"]


def _restore(
    bundle, expected_digest, max_logical_bytes, component_limit=transport.BYTE_LIMIT
):
    _require(
        _keys(
            bundle,
            {
                "format",
                "metadata",
                "inputs",
                "capture_ref",
                "cards",
                "views",
                "root_view_ref",
                "application",
                "bundle_digest",
            },
        )
        and bundle["format"] == FORMAT,
        "Unknown or malformed Deck reading format.",
    )
    actual = digest(
        canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
    )
    _require(
        bundle["bundle_digest"] == actual
        and (expected_digest is None or expected_digest == actual),
        "Deck reading digest mismatch.",
    )
    _require(
        isinstance(bundle["metadata"], dict)
        and isinstance(bundle["inputs"], list)
        and all(isinstance(k, str) for k in bundle["inputs"])
        and isinstance(bundle["cards"], dict)
        and set(bundle["cards"]) == set(bundle["inputs"]),
        "Invalid original Deck inputs.",
    )
    readers, overviews, captures = {}, {}, {}
    logical = len(canonical_json(bundle).encode("utf-8"))
    transport._check("max_logical_bytes", logical, max_logical_bytes)
    fingerprints = None
    for key, component in bundle["cards"].items():
        remaining = None if max_logical_bytes is None else max_logical_bytes - logical
        transport._check("max_logical_bytes", logical + 1, max_logical_bytes)
        root = _restore_card(
            component,
            None,
            max_logical_bytes=remaining,
            component_limit=component_limit,
        )
        access = root.explorer.access
        _require(
            access._focal_key == key and list(access._inputs) == bundle["inputs"],
            "A Card component belongs to different original inputs or focal scope.",
        )
        _require(
            root.title == "Card overview"
            and root._origin is None
            and (
                root._route_catalog
                and not root._question_catalog
                or root.native_payload == access._captures[key].data
            ),
            "A Deck member requires its original overview.",
        )
        current = {
            k: digest(canonical_json(c.data)) for k, c in access._captures.items()
        }
        _require(
            set(current) == set(bundle["inputs"])
            and (fingerprints is None or fingerprints == current),
            "Card components disagree on the original capture pool.",
        )
        fingerprints, captures = current, access._captures
        readers[key] = root.explorer
        overviews[key] = root
        logical += root.explorer._session["validation"].get(
            "logical_bytes", len(canonical_json(component).encode("utf-8"))
        )
        transport._check("max_logical_bytes", logical, max_logical_bytes)
    owner = object.__new__(DeckExplorer)
    owner._initialize_capture(bundle["metadata"], captures, bundle["inputs"])
    _require(
        owner._capture_ref == bundle["capture_ref"],
        "Deck metadata/member capture binding changed.",
    )
    owner.mode, owner._readers = "saved", readers
    owner._saved_overviews = overviews
    owner._saved_bundles = bundle["cards"]
    _require(
        isinstance(bundle["views"], list) and 1 <= len(bundle["views"]) <= VIEW_LIMIT,
        "Invalid original Deck view collection.",
    )
    views = {}
    for record in bundle["views"]:
        _require(
            _keys(record, {"view_ref", "positions", "request", "origin"})
            and isinstance(record["view_ref"], str)
            and record["view_ref"] not in views
            and (
                record["origin"] is None
                or isinstance(record["origin"], str)
                and record["origin"] in views
            ),
            "Invalid or forward Deck return binding.",
        )
        origin = views.get(record["origin"])
        positions = _positions(owner, record["request"], origin)
        _require(
            isinstance(record["positions"], list)
            and all(type(p) is int for p in record["positions"])
            and tuple(record["positions"]) == positions,
            "Deck selection disagrees with its original request.",
        )
        view = DeckView(owner, positions, origin, record["request"])
        _require(
            view.view_ref == record["view_ref"], "Original Deck view binding changed."
        )
        views[view.view_ref] = view
        if origin is None:
            owner._root = view
    _require(
        isinstance(bundle["root_view_ref"], str) and bundle["root_view_ref"] in views,
        "Missing Deck root view.",
    )
    _application(bundle["application"], views)
    if bundle["application"] is not None:
        _require(
            bundle["application"]["current"]["view_ref"] == bundle["root_view_ref"],
            "Application root differs from the saved selection.",
        )
    owner._saved_application, owner._saved_views = bundle["application"], views
    owner._logical_receiving_bytes = logical
    return views[bundle["root_view_ref"]]


@arg_digest()
def read_deck_exploration(
    path,
    expected_digest=None,
    skip_digestion=False,
    *,
    max_encoded_bytes=transport.BYTE_LIMIT,
    max_decoded_bytes=transport.BYTE_LIMIT,
    max_window_bytes=transport.WINDOW_LIMIT,
    max_logical_bytes=268435456,
):
    """Reopen original Deck context without constructing Cards or running science."""
    if not isinstance(path, (str, os.PathLike)) or not str(path):
        raise ArgumentError("path requires a nonempty file path.")
    if expected_digest is not None and (
        not isinstance(expected_digest, str)
        or not SNAPSHOT_ID.fullmatch(expected_digest)
    ):
        raise ArgumentError("expected_digest requires sha256:<64 hex> or None.")
    for name, value in (
        ("max_encoded_bytes", max_encoded_bytes),
        ("max_decoded_bytes", max_decoded_bytes),
        ("max_window_bytes", max_window_bytes),
        ("max_logical_bytes", max_logical_bytes),
    ):
        transport.byte_budget(name, value)
    try:
        with Path(path).open("rb") as stream:
            transport._check(
                "max_encoded_bytes",
                os.fstat(stream.fileno()).st_size,
                max_encoded_bytes,
            )
            raw, _ = transport.read(
                stream,
                encoded_limit=max_encoded_bytes,
                decoded_limit=max_decoded_bytes,
                window_limit=max_window_bytes,
            )
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
        return _restore(bundle, expected_digest, max_logical_bytes, max_decoded_bytes)
    except (ArgumentError, StorageError):
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        RecursionError,
        AttributeError,
    ) as exc:
        raise StorageError(f"Cannot read original Deck reading: {exc}") from exc
