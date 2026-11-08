"""Inert clinical input and generated-rule labels from declared output paths."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from .._literature_history_v1.inputs import _FrozenAccess as _FrozenAccess
from ..card_exploration_coverage_v1 import _v1_knowledge_state
from ..card_exploration_history import _HistoricalInput
from .clinical import clinical_view

DEFAULT_PRODUCER = "0.14.0+224.g66989a4"
_PRODUCER = ContextVar("original_clinical_rule_producer", default=DEFAULT_PRODUCER)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


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
