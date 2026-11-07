"""Inert captured inputs for original expectations without constructing a Card."""

from copy import deepcopy

from ..card_exploration_coverage_v1 import _v1_knowledge_state
from ..card_exploration_history import _HistoricalInput
from .rules import make_derivation


def acquisition_of(assertion):
    return dict(assertion.get("acquisition") or {"method": "not_recorded"})


class _CapturedCard(_HistoricalInput):
    def literature(self):
        from .literature import literature_view

        return literature_view(self)

    def explain_literature(self, publication_ref):
        from .literature_explanation import explain_literature

        return explain_literature(self, publication_ref)

    def knowledge_state(self):
        result = _v1_knowledge_state(self)
        rule = result["rule"]
        result["rule"] = make_derivation(
            rule["rule"], rule["inputs"], rule["parameters"]
        )
        return result


class _FrozenAccess:
    """Only the SDK202 builder's capture/context/cache surface, no live facade."""

    def __init__(self, access):
        self._captures = access._captures
        self._inputs = tuple(access._inputs)
        self._focal_key = access._focal_key
        self._objects, self._scientific_cache, self._scientific_items = {}, {}, {}

    @property
    def mode(self):
        return "live"

    @property
    def _focal(self):
        return self._captures[self._focal_key]

    @property
    def profile(self):
        nature = self._focal.data["meta"].get("entity_type")
        return (
            nature if nature in ("protein", "small_molecule", "disease") else "generic"
        )

    @property
    def context(self):
        return {
            "card_ref": self._focal.pin,
            "snapshot_id": self._focal.snapshot,
            "inputs": list(self._inputs),
            "captures": sorted(self._captures),
            "profile": self.profile,
            "mode": self.mode,
            "adapter": "literal_access@1",
        }

    def _card_location(self, *, segments=None):
        return {
            "format": "card_access_location@1",
            "kind": "card",
            "card_ref": self._focal.pin,
            "snapshot_id": self._focal.snapshot,
            "segments": deepcopy(segments or []),
        }
