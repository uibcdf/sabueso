"""Inert captured inputs and exact typed traversal; no Card or source client."""

from copy import deepcopy

from .._literature_history_v1.inputs import _FrozenAccess as _OriginalAccess
from ..errors import ArgumentError, StorageError
from ..snapshot import snapshot_id


class _FrozenAccess(_OriginalAccess):
    def __init__(self, access):
        super().__init__(access)
        for capture in self._captures.values():
            if snapshot_id(capture.data) != capture.snapshot:
                raise StorageError(
                    "Original knowledge-comparison input snapshot differs."
                )

    def _resolve(self, location):
        if location.get("kind") != "card":
            raise ArgumentError(
                "Original knowledge-comparison inputs require a captured Card."
            )
        matches = [
            capture
            for capture in self._captures.values()
            if capture.pin == location["card_ref"]
            and capture.snapshot == location["snapshot_id"]
        ]
        if len(matches) != 1:
            raise ArgumentError("Unknown original knowledge-comparison capture.")
        value = matches[0].data
        try:
            for segment in location["segments"]:
                kind, key = segment["type"], segment["value"]
                if kind == "Record":
                    rows = [row for row in value if row.get("id") == key]
                    if len(rows) != 1:
                        raise ArgumentError("Unknown original source record.")
                    value = rows[0]
                elif kind == "Key" and isinstance(value, dict):
                    value = value[key]
                elif kind == "Index" and type(key) is int and key >= 0:
                    value = value[key]
                else:
                    raise ArgumentError("Unknown original typed location.")
        except (KeyError, IndexError, TypeError) as exc:
            raise ArgumentError(
                "Original knowledge-comparison location is absent."
            ) from exc
        return value, deepcopy(location)
