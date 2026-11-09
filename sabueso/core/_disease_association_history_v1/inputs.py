"""Inert original inputs without current Cards, readers or source clients."""

from copy import deepcopy

from .._literature_history_v1.inputs import _FrozenAccess as _OriginalAccess
from ..card_exploration_coverage_v1 import _v1_knowledge_state
from ..card_exploration_history import _HistoricalInput
from ..errors import StorageError
from .clinical import clinical_view
from .rules import _PRODUCER


class _FrozenAccess(_OriginalAccess):
    def _resolve(self, location):
        if not isinstance(location, dict) or location.get("kind") != "card":
            raise StorageError(
                "Original disease expectations require an exact Card location."
            )
        captures = [
            capture
            for capture in self._captures.values()
            if capture.pin == location.get("card_ref")
            and capture.snapshot == location.get("snapshot_id")
        ]
        if len(captures) != 1:
            raise StorageError("Original disease location lost its exact capture.")
        node = captures[0].data
        for part in location["segments"]:
            if part["type"] == "Key" and isinstance(node, dict):
                node = node[part["value"]]
            elif (
                part["type"] == "Index"
                and isinstance(node, list)
                and type(part["value"]) is int
            ):
                node = node[part["value"]]
            else:
                raise StorageError("Unsupported original disease native location step.")
        return node, location


class _CapturedCard(_HistoricalInput):
    def clinical(self):
        return clinical_view(self)

    def knowledge_state(self):
        result = _v1_knowledge_state(self)
        result["rule"] = {
            **deepcopy(dict(result["rule"])),
            "sabueso_version": _PRODUCER.get(),
        }
        return result
