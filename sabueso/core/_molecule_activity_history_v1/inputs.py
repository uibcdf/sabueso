"""Inert SDK205 input and Deck surfaces, without Card or mutable profiles."""

from copy import copy, deepcopy

from .._bioactivity_history_v1.inputs import _FrozenAccess as _OriginalAccess
from .._bioactivity_history_v2.inputs import _CapturedCard as _OriginalCard
from ..card_access import _handle
from ..errors import StorageError
from ..snapshot import deck_snapshot_id
from .rules import DEFAULT_PRODUCER, producers


def assertion_value(assertion):
    if "normalized_value" in assertion:
        return assertion["normalized_value"]
    return assertion.get("asserted_value")


class _CapturedCard(_OriginalCard):
    """The unchanged original scientific and SDK202 bibliography inputs."""


class _InputDeck:
    """Only the empty-metadata Deck constructed by the SDK205 native crossing."""

    def __init__(self, cards):
        self.cards = list(cards)
        self.meta = {}

    def snapshot_id(self):
        return deck_snapshot_id(self.meta, [card.pinned_ref() for card in self.cards])

    def explain(self, card_id, skip_digestion=False):
        return {
            "card_id": card_id,
            "in_deck": any(card.id == card_id for card in self.cards),
            "basis": None,
            "excluded": None,
            "deck": {},
            "operations": [],
        }


class _FrozenAccess(_OriginalAccess):
    """Separate expected objects/caches shared across exact captured focal pins."""

    def __init__(self, access, versions=None, primary=DEFAULT_PRODUCER):
        super().__init__(access)
        self._nonce = getattr(access, "_nonce", "original-molecule-expectation")
        self._locations, self._metadata_refs = {}, set()
        self._versions, self._primary = dict(versions or {}), primary

    def producers(self):
        return producers(self._versions, self._primary)

    def _for_capture(self, key):
        if key not in self._captures:
            raise StorageError("Original focal pin is outside supplied captures.")
        other = copy(self)
        other._focal_key, other._scientific_items = key, {}
        return other

    def _location(self, full):
        key = _handle("XL_", {"session": self._nonce, "location": full})
        self._locations.setdefault(key, deepcopy(full))
        return {
            "format": "card_access_location@1",
            "kind": "lookup",
            "location_ref": key,
        }

    def _object_location(self, value):
        key = _handle("XR_", {"adapter": "literal_metadata@1", "value": value})
        self._objects.setdefault(key, deepcopy(value))
        self._metadata_refs.add(key)
        return self._location(
            {
                "format": "card_access_location@1",
                "kind": "result",
                "result_ref": key,
                "segments": [],
            }
        )

    def _resolve(self, location):
        # Native crossing only resolves its own freshly registered whole wrapper.
        # General saved location validation belongs to the exploration verifier.
        if (
            not isinstance(location, dict)
            or set(location) != {"format", "kind", "location_ref"}
            or location["format"] != "card_access_location@1"
            or location["kind"] != "lookup"
            or location["location_ref"] not in self._locations
        ):
            raise StorageError("Unsupported original expected-object location.")
        full = deepcopy(self._locations[location["location_ref"]])
        if full["kind"] != "result" or full["segments"]:
            raise StorageError("Expected a complete original registered object.")
        return self._objects[full["result_ref"]], full
