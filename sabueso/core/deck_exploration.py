"""Captured Deck navigation; original Card readers retain scientific authority.

Member pages are byte/record bounded. Capturing a Deck still materializes all
supplied Cards and metadata; a small page is not a capture-memory guarantee.
"""

from __future__ import annotations

import json
import secrets
from copy import deepcopy
from dataclasses import dataclass

from sabueso._private.argdigest import arg_digest

from .card_capture import _capture_cards
from .errors import ArgumentError, StorageError
from .snapshot import canonical_json, deck_snapshot_id, digest


def _ref(prefix, value):
    return prefix + digest(canonical_json(value)).split(":", 1)[1]


@dataclass(frozen=True)
class DeckCardContext:
    """An original Card reader plus its explicit captured Deck return point.

    CardView.back() retains its existing within-Card meaning. Use this context's
    back() to return to the exact Deck selection/order from which it was opened.
    """

    explorer: object
    member_ref: str
    _origin: object

    @property
    def context(self):
        return {
            "deck": self._origin.context,
            "member_ref": self.member_ref,
            "card": self.explorer.context,
        }

    @property
    def access(self):
        return self.explorer.access

    def overview(self):
        return self.explorer.overview()

    def back(self):
        return self._origin


@dataclass(frozen=True)
class DeckMember:
    """One input occurrence; equal identifiers do not merge occurrences."""

    _view: object
    _position: int

    @property
    def member_ref(self):
        return self._view._owner._member_refs[self._position]

    @property
    def position(self):
        return self._position

    @property
    def context(self):
        return self._view._owner._member(self._position)

    @property
    def label(self):
        return self.context["card_ref"] or self.context["snapshot_id"]

    @property
    def kind(self):
        value = self.context["nature"]
        return value if isinstance(value, str) else None

    @property
    def basis(self):
        return deepcopy(self.context["membership"]["value"])

    def open(self):
        return self._view._owner._open(self._position, self._view)

    def inspect(self):
        """Complete original stored Card, without interpreting an unknown nature."""
        key = self._view._owner._inputs[self._position]
        return deepcopy(self._view._owner._captures[key].data)

    def back(self):
        return self._view


@dataclass(frozen=True)
class DeckView:
    """An immutable presentation selection over one captured Deck."""

    _owner: object
    _positions: tuple
    _origin: object = None
    _request: object = None

    @property
    def capabilities(self):
        return {
            "page": True,
            "member": True,
            "select": True,
            "filter": "literal identifier/nature",
            "sort": ["label", "kind"],
            "inspect": True,
            "save": False,
            "saved_deck_reading": False,
        }

    @property
    def request(self):
        return (
            deepcopy(self._request)
            if self._request is not None
            else {"operation": "overview"}
        )

    @property
    def view_ref(self):
        return _ref(
            "DV_",
            {
                "format": "deck_member_selection@1",
                "capture_ref": self._owner._capture_ref,
                "positions": self._positions,
                "request": self.request,
                "origin": self._origin.view_ref if self._origin is not None else None,
            },
        )

    @property
    def context(self):
        return {
            **self._owner.context,
            "view_ref": self.view_ref,
            "selected_count": len(self._positions),
        }

    def items(self):
        return tuple(DeckMember(self, position) for position in self._positions)

    @arg_digest()
    def member(self, member_ref, skip_digestion=False):
        for position in self._positions:
            if self._owner._member_refs[position] == member_ref:
                return DeckMember(self, position)
        raise ArgumentError("That member does not belong to this captured selection.")

    @arg_digest()
    def select(self, member_refs, skip_digestion=False):
        if len(set(member_refs)) != len(member_refs):
            raise ArgumentError(
                "Select each occurrence once; repeated inputs have distinct member references."
            )
        positions = tuple(self.member(ref)._position for ref in member_refs)
        return DeckView(
            self._owner,
            positions,
            self,
            {"operation": "select", "member_refs": list(member_refs)},
        )

    @arg_digest()
    def filter(self, text, skip_digestion=False):
        """Literal identifier/nature filter, not a scientific similarity query."""
        needle = text.casefold()
        positions = tuple(
            item.position
            for item in self.items()
            if needle in item.label.casefold() or needle in (item.kind or "").casefold()
        )
        return DeckView(
            self._owner,
            positions,
            self,
            {"operation": "filter", "text": text, "scope": "literal identifier/nature"},
        )

    @arg_digest()
    def sort(self, column="label", *, descending=False, skip_digestion=False):
        """Order declared identifiers/natures; never compare molecular quantities."""
        if column not in {"label", "kind"} or type(descending) is not bool:
            raise ArgumentError(
                "Deck presentation sorting uses label or kind and a boolean direction."
            )
        items = self.items()
        present = [item for item in items if getattr(item, column) is not None]
        missing = [item for item in items if getattr(item, column) is None]
        ordered = (
            sorted(present, key=lambda item: getattr(item, column), reverse=descending)
            + missing
        )
        return DeckView(
            self._owner,
            tuple(item.position for item in ordered),
            self,
            {"operation": "sort", "column": column, "descending": descending},
        )

    @arg_digest()
    def page(self, *, limit=32, max_bytes=65536, cursor=None, skip_digestion=False):
        """Typed canonical-JSON member page, bound to capture and selection."""
        if (
            type(limit) is not int
            or not 1 <= limit <= 1000
            or type(max_bytes) is not int
            or not 1024 <= max_bytes <= 1048576
        ):
            raise ArgumentError(
                "Use 1–1000 members and a 1024–1048576 byte page budget."
            )
        start = 0
        if cursor is not None:
            try:
                owner, start = self._owner._cursors[cursor]
            except (KeyError, TypeError) as exc:
                raise ArgumentError("Unknown or foreign Deck cursor.") from exc
            if owner != self.view_ref:
                raise ArgumentError("The cursor belongs to another Deck selection.")
        end, items = start, []

        def frame():
            next_cursor = None
            if end < len(self._positions):
                next_cursor = "0" * 32  # Budget only; replaced before returning.
            return {
                "format": "sabueso.deck_members@1",
                "context": self.context,
                "offset": start,
                "items": items,
                "complete": end == len(self._positions),
                "next_cursor": next_cursor,
            }

        for position in self._positions[start : start + limit]:
            item = self._owner._member(position)
            items.append(item)
            end += 1
            if len(canonical_json(frame()).encode("utf-8")) > max_bytes:
                items.pop()
                end -= 1
                if items:
                    break
                items.append(
                    {
                        "member_ref": self._owner._member_refs[position],
                        "position": position,
                        "status": "deferred",
                        "reason": "Member metadata exceeds the page byte budget; inspect the exact member.",
                    }
                )
                end += 1
                break
        result = frame()
        if len(canonical_json(result).encode("utf-8")) > max_bytes:
            raise ArgumentError(
                "The page budget cannot hold the mandatory Deck context."
            )
        if result["next_cursor"] is not None:
            key = (self.view_ref, end)
            token = self._owner._tokens.setdefault(key, secrets.token_urlsafe(24))
            self._owner._cursors[token] = key
            result["next_cursor"] = token
        return result

    def inspect(self):
        """Complete captured Deck metadata, including extensions and exclusions."""
        return self._owner.metadata

    def back(self):
        return self._origin if self._origin is not None else self

    def __str__(self):
        return f"Captured Deck: {len(self._positions)} selected / {len(self._owner._inputs)} input occurrences. Use items() or page() to inspect members; inspect() retains all Deck metadata."


class DeckExplorer:
    """Human and machine exploration share one validated detached capture."""

    def __init__(self, deck):
        if not isinstance(deck.meta, dict):
            raise ArgumentError("Deck metadata must be a stored mapping.")
        try:
            self._metadata = json.loads(canonical_json(deck.meta))
        except (TypeError, ValueError) as exc:
            raise StorageError(
                "Deck metadata must retain its stored JSON meaning."
            ) from exc
        cards = tuple(deck.cards)
        if cards:
            self._captures, self._inputs = _capture_cards(cards[0], cards[1:])
        else:
            self._captures, self._inputs = {}, ()
        members = [
            {
                "card_ref": self._captures[key].pin,
                "snapshot_id": self._captures[key].snapshot,
            }
            for key in self._inputs
        ]
        self._capture_ref = _ref(
            "DX_",
            {"format": "deck_capture@1", "meta": self._metadata, "members": members},
        )
        pins = [member["card_ref"] for member in members]
        self._snapshot = deck_snapshot_id(self._metadata, pins) if all(pins) else None
        self._member_refs = tuple(
            _ref("DM_", {"capture_ref": self._capture_ref, "position": position})
            for position in range(len(cards))
        )
        self._tokens, self._cursors = {}, {}
        self._readers = {}
        self._root = DeckView(self, tuple(range(len(cards))))

    @property
    def context(self):
        return {
            "capture_ref": self._capture_ref,
            "deck_snapshot_id": self._snapshot,
            "input_count": len(self._inputs),
            "unidentified_members": sum(
                self._captures[key].pin is None for key in self._inputs
            ),
        }

    @property
    def metadata(self):
        return deepcopy(self._metadata)

    @property
    def access(self):
        """The same typed bounded view; no prose parsing or second capture."""
        return self._root

    def overview(self):
        return self._root

    def _member(self, position):
        capture = self._captures[self._inputs[position]]
        card_id = capture.data["meta"].get("card_id")
        membership = self._metadata.get("membership")
        stated = isinstance(membership, dict) and card_id in membership
        return {
            "member_ref": self._member_refs[position],
            "position": position,
            "card_ref": capture.pin,
            "snapshot_id": capture.snapshot,
            "nature": capture.data["meta"].get("entity_type"),
            "membership": {
                "state": "recorded" if stated else "not_stated",
                "scope": "Original metadata keyed by Card ID; no occurrence-specific support inferred",
                "value": deepcopy(membership[card_id]) if stated else None,
            },
        }

    def _open(self, position, origin):
        from .card import Card

        key = self._inputs[position]
        if key not in self._readers:
            capture = self._captures[key]
            explorer = Card.from_dict(deepcopy(capture.data)).explore()
            if explorer.context["snapshot_id"] != capture.snapshot:
                raise StorageError(
                    "Opening this member would change its captured Card state."
                )
            self._readers[key] = explorer
        return DeckCardContext(self._readers[key], self._member_refs[position], origin)
