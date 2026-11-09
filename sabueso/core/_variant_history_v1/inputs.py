"""Inert retained fields and records; no Card construction or source access."""

from .._literature_history_v1.inputs import _FrozenAccess as _FrozenAccess
from ..card_exploration_history import _HistoricalInput, _Records


class _SourceRecords(_Records):
    def find_by_field(self, field):
        return [row for row in self._rows if row.get("field_path") == field]


class _CapturedCard(_HistoricalInput):
    def __init__(self, capture):
        super().__init__(capture)
        self.source_assertion_store = _SourceRecords(
            capture.data["source_assertion_store"]
        )
