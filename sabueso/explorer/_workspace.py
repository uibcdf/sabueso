"""Portable original application context over independently verified native files.

Version 1 contains Card/Deck readings, exact application trails and literal source
query reports. It contains no executable actions, pending jobs, model, camera,
provider tokens or layout. Reading never constructs Cards or reacquires sources.
"""

from __future__ import annotations

import io
import json
import os
import secrets
import tempfile
from copy import deepcopy
from pathlib import Path

from sabueso.core import exploration_transport as transport
from sabueso.core.card_exploration_storage import _restore as restore_card
from sabueso.core.card_exploration_storage import _unique, save_exploration
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import SNAPSHOT_ID, canonical_json, digest

from ._deck_session import _DeckSession
from ._session import HISTORY_LIMIT, PAGE_SIZE, TEXT_SIZE, _Session

FORMAT = "sabueso.explorer_workspace@1"
LIMIT = transport.BYTE_LIMIT
LOGICAL_LIMIT = 268435456


def _require(condition, message):
    if not condition:
        raise StorageError(message)


def _keys(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def _seal(bundle):
    return {**bundle, "bundle_digest": digest(canonical_json(bundle))}


def _decode(raw):
    decoded, _ = transport.read(
        io.BytesIO(raw),
        encoded_limit=LIMIT,
        decoded_limit=LIMIT,
        window_limit=transport.WINDOW_LIMIT,
    )
    return json.loads(decoded.decode("utf-8"), object_pairs_hook=_unique)


def _resolution(resolution):
    if resolution is None:
        return None
    panel = {key: value for key, value in resolution.panel().items() if key != "mode"}
    return {
        "panel": panel,
        "choices": [
            {"ref": key, "value": value} for key, value in resolution.choices.items()
        ],
    }


class _OriginalResolution:
    """A literal retained query report; it is not a newly resolved source answer."""

    def __init__(self, record):
        _require(
            _keys(record, {"panel", "choices"}), "Malformed original query report."
        )
        panel = record["panel"]
        _require(
            _keys(
                panel,
                {
                    "format",
                    "revision",
                    "kind",
                    "query",
                    "status",
                    "entity_ref",
                    "has_card",
                    "choices",
                    "original_text",
                },
            )
            and panel["format"] == "sabueso.explorer_resolution@1"
            and panel["kind"] in ("uniprot", "pdb", "smiles", "disease", "pubchem")
            and isinstance(panel["query"], str)
            and 0 < len(panel["query"]) <= 8300
            and isinstance(panel["revision"], str)
            and type(panel["has_card"]) is bool
            and isinstance(panel["status"], str)
            and bool(panel["status"])
            and (panel["entity_ref"] is None or isinstance(panel["entity_ref"], str))
            and isinstance(panel["original_text"], str),
            "Invalid original source report.",
        )
        original = json.loads(panel["original_text"], object_pairs_hook=_unique)
        _require(
            _keys(original, {"resolution", "acquisition_trace"})
            and isinstance(original["resolution"], dict)
            and original["resolution"].get("status") == panel["status"]
            and original["resolution"].get("entity_ref") == panel["entity_ref"],
            "Query report differs from its retained native answer.",
        )
        self.choices = {}
        from ._source_choices import declared_choices

        declared = declared_choices(panel["kind"], original["resolution"])
        cursor = 0
        _require(
            isinstance(record["choices"], list), "Invalid original source choices."
        )
        for row in record["choices"]:
            _require(
                _keys(row, {"ref", "value"})
                and isinstance(row["ref"], str)
                and row["ref"]
                and row["ref"] not in self.choices,
                "Invalid source choice reference.",
            )
            value = row["value"]
            matches = [
                i
                for i in range(cursor, len(declared))
                if canonical_json(declared[i]) == canonical_json(value)
            ]
            _require(
                matches,
                "A saved choice lacks its original source-declared basis or occurrence order.",
            )
            cursor = matches[0] + 1
            self.choices[row["ref"]] = deepcopy(value)
        _require(
            panel["choices"]
            == [
                {"ref": ref, "entity_ref": value["entity_ref"]}
                for ref, value in self.choices.items()
            ],
            "Source choice order or membership changed.",
        )
        self.kind, self.query = panel["kind"], panel["query"]
        self.original, self.acquisition = (
            original["resolution"],
            original["acquisition_trace"],
        )
        self.revision = secrets.token_hex(16)
        self._panel = deepcopy(panel)

    def panel(self):
        return {**deepcopy(self._panel), "revision": self.revision, "mode": "saved"}


class _Composer:
    def __init__(self, directory):
        self.directory = directory
        self.cards, self.decks, self.native = {}, {}, {}
        self.physical = 0

    def _retain(self, target, bundle):
        key = digest(canonical_json(bundle))
        if key not in target:
            self.physical += len(canonical_json(bundle).encode("utf-8"))
            transport._check("max_decoded_bytes", self.physical, LIMIT)
            target[key] = bundle
        return key

    def card_state(self, view, offset, text_offset):
        session = view._explorer._session
        group = id(session)
        if group not in self.native:
            path = self.directory / "card.json"
            references = {}
            save_exploration(view, path, overwrite=True, _navigation_refs=references)
            bundle = json.loads(path.read_bytes(), object_pairs_hook=_unique)
            key = self._retain(self.cards, bundle)
            self.native[group] = key, references
        key, references = self.native[group]
        _require(
            id(view) in references,
            "A reading in the application trail lacks original persistence. Save its supported native reading separately.",
        )
        return {
            "component": key,
            "navigation_ref": references[id(view)],
            "view_ref": view.view_ref,
            "offset": offset,
            "text_offset": text_offset,
        }

    def card_session(self, session):
        return {
            "kind": "card",
            "current": self.card_state(
                session.current, session.offset, session.text_offset
            ),
            "history": [
                self.card_state(view, offset, text_offset)
                for view, offset, text_offset in session.history
            ],
        }

    def session(self, session):
        if session is None:
            return None
        if isinstance(session, _Session):
            return self.card_session(session)
        _require(isinstance(session, _DeckSession), "Unsupported application context.")
        path = self.directory / "deck.json.gz"
        session._save(path)
        key = self._retain(self.decks, _decode(path.read_bytes()))
        return {
            "kind": "deck",
            "component": key,
            "entry_position": session.entry_position,
            "card": self.card_session(session.card_session)
            if session.card_session
            else None,
        }

    def context(self, session, resolution):
        return {"session": self.session(session), "resolution": _resolution(resolution)}


def save_workspace(service, path, *, overwrite=False, compression="gzip"):
    """Internal application saving; original Card/Deck formats stay unchanged."""
    if (
        not isinstance(path, (str, os.PathLike))
        or not str(path)
        or type(overwrite) is not bool
    ):
        raise ArgumentError("Use a nonempty workspace path and boolean overwrite.")
    codec, backend = transport.encoder(compression)
    with tempfile.TemporaryDirectory(
        prefix="sabueso-workspace-components-"
    ) as directory:
        composer = _Composer(Path(directory))
        current = composer.context(service.session, service.resolution)
        history = [
            composer.context(session, resolution)
            for session, resolution in service.resolution_history
        ]
        bundle = _seal(
            {
                "format": FORMAT,
                "cards": composer.cards,
                "decks": composer.decks,
                "current": current,
                "history": history,
            }
        )
    raw = canonical_json(bundle).encode("utf-8")
    transport._check("max_decoded_bytes", len(raw), LIMIT)
    _restore(bundle, service.output_directory, bundle["bundle_digest"])
    destination, temporary = Path(path), None
    try:
        fd, temporary = tempfile.mkstemp(
            dir=destination.parent, prefix=".sabueso-workspace-"
        )
        with os.fdopen(fd, "wb") as stream:
            receipt = transport.write(stream, raw, compression, codec, backend, LIMIT)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)
    except OSError as error:
        raise StorageError(f"Cannot save original workspace: {error}") from error
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return {
        "path": str(destination),
        "bundle_digest": bundle["bundle_digest"],
        "transport": receipt,
    }


class _Receiver:
    def __init__(self, bundle, output_directory):
        self.output_directory = output_directory
        self.cards, self.decks = {}, {}
        logical = len(canonical_json(bundle).encode("utf-8"))
        for key, component in bundle["cards"].items():
            _require(
                key == digest(canonical_json(component)),
                "Workspace Card component changed.",
            )
            remaining = LOGICAL_LIMIT - logical
            transport._check("max_logical_bytes", logical + 1, LOGICAL_LIMIT)
            nodes = {}
            root = restore_card(
                component, None, max_logical_bytes=remaining, _navigation_nodes=nodes
            )
            self.cards[key] = nodes
            logical += root._explorer._session["validation"].get(
                "logical_bytes", len(canonical_json(component).encode("utf-8"))
            )
            transport._check("max_logical_bytes", logical, LOGICAL_LIMIT)
        from sabueso.core.deck_exploration_storage import _restore as restore_deck

        for key, component in bundle["decks"].items():
            _require(
                key == digest(canonical_json(component)),
                "Workspace Deck component changed.",
            )
            remaining = LOGICAL_LIMIT - logical
            transport._check("max_logical_bytes", logical + 1, LOGICAL_LIMIT)
            view = restore_deck(component, None, remaining)
            logical += view._owner._logical_receiving_bytes
            transport._check("max_logical_bytes", logical, LOGICAL_LIMIT)
            self.decks[key] = view

    def card_state(self, state):
        _require(
            _keys(
                state,
                {"component", "navigation_ref", "view_ref", "offset", "text_offset"},
            )
            and isinstance(state["component"], str)
            and state["component"] in self.cards
            and isinstance(state["navigation_ref"], str)
            and state["navigation_ref"] in self.cards[state["component"]],
            "Unknown original Card navigation point.",
        )
        view = self.cards[state["component"]][state["navigation_ref"]]
        _require(
            view.view_ref == state["view_ref"],
            "Application reading differs from its original node.",
        )
        offset, text = state["offset"], state["text_offset"]
        _require(
            type(offset) is int
            and offset >= 0
            and offset % PAGE_SIZE == 0
            and offset < max(1, len(view.items()))
            and type(text) is int
            and text >= 0
            and text % TEXT_SIZE == 0,
            "Invalid original application page.",
        )
        if text:
            value = view.native_payload
            _require(
                isinstance(value, str) and text < len(value),
                "Invalid original application text page.",
            )
        return view, offset, text

    def card_session(self, record):
        _require(
            _keys(record, {"kind", "current", "history"})
            and record["kind"] == "card"
            and isinstance(record["history"], list)
            and len(record["history"]) <= HISTORY_LIMIT,
            "Malformed original Card application trail.",
        )
        view, offset, text = self.card_state(record["current"])
        session = _Session(view, self.output_directory)
        session.offset, session.text_offset = offset, text
        session.history = [self.card_state(state) for state in record["history"]]
        return session

    def session(self, record):
        if record is None:
            return None
        _require(isinstance(record, dict), "Malformed workspace reading.")
        if record.get("kind") == "card":
            return self.card_session(record)
        _require(
            _keys(record, {"kind", "component", "entry_position", "card"})
            and record["kind"] == "deck"
            and isinstance(record["component"], str)
            and record["component"] in self.decks,
            "Unknown original Deck workspace component.",
        )
        # The already verified native view owns metadata/history/page admission.
        # Each application context has its own operational state.
        session = _DeckSession._from_view(
            self.decks[record["component"]], self.output_directory
        )
        position = record["entry_position"]
        if record["card"] is None:
            _require(position is None, "A Deck entry requires its original Card trail.")
            return session
        _require(
            type(position) is int
            and position in session.current._positions
            and not session.metadata_open,
            "Foreign original Deck entry occurrence.",
        )
        card = self.card_session(record["card"])
        owner, access = session.explorer, card.current._explorer.access
        _require(
            tuple(access._inputs) == owner._inputs
            and set(access._captures) == set(owner._captures)
            and all(
                canonical_json(access._captures[k].data)
                == canonical_json(owner._captures[k].data)
                for k in owner._captures
            ),
            "The Card trail belongs to a different Deck capture.",
        )
        member = session.current.items()[session.current._positions.index(position)]
        session.visit, session.card_session, session.entry_position = (
            member.open(),
            card,
            position,
        )
        return session

    def context(self, record):
        _require(
            _keys(record, {"session", "resolution"}),
            "Malformed original query context.",
        )
        session = self.session(record["session"])
        resolution = (
            _OriginalResolution(record["resolution"])
            if record["resolution"] is not None
            else None
        )
        return session, resolution


def _restore(bundle, output_directory, expected_digest=None):
    _require(
        _keys(
            bundle, {"format", "cards", "decks", "current", "history", "bundle_digest"}
        )
        and bundle["format"] == FORMAT,
        "Unknown or malformed original workspace format.",
    )
    actual = digest(
        canonical_json({k: v for k, v in bundle.items() if k != "bundle_digest"})
    )
    _require(
        bundle["bundle_digest"] == actual
        and (expected_digest is None or expected_digest == actual),
        "Workspace digest mismatch.",
    )
    _require(
        isinstance(bundle["cards"], dict)
        and isinstance(bundle["decks"], dict)
        and len(bundle["cards"]) + len(bundle["decks"]) <= 1024
        and isinstance(bundle["history"], list)
        and len(bundle["history"]) <= 32,
        "Invalid workspace component/history collection.",
    )
    receiver = _Receiver(bundle, output_directory)
    session, resolution = receiver.context(bundle["current"])
    history = [receiver.context(context) for context in bundle["history"]]
    return session, resolution, history


def read_workspace(path, output_directory, expected_digest=None):
    """Inert internal reopening; no GUI or provider runtime is imported."""
    if not isinstance(path, (str, os.PathLike)) or not str(path):
        raise ArgumentError("Use a nonempty original workspace path.")
    if expected_digest is not None and (
        not isinstance(expected_digest, str)
        or not SNAPSHOT_ID.fullmatch(expected_digest)
    ):
        raise ArgumentError("expected_digest requires sha256:<64 hex> or None.")
    try:
        with Path(path).open("rb") as stream:
            transport._check(
                "max_encoded_bytes", os.fstat(stream.fileno()).st_size, LIMIT
            )
            raw, _ = transport.read(
                stream,
                encoded_limit=LIMIT,
                decoded_limit=LIMIT,
                window_limit=transport.WINDOW_LIMIT,
            )
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
        return _restore(bundle, output_directory, expected_digest)
    except (StorageError, ArgumentError):
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        RecursionError,
    ) as error:
        raise StorageError(f"Cannot read original workspace: {error}") from error
