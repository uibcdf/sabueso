"""Original producer labels at named generated derivation constructors only."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+243.gf6d8e4a"
_PRODUCER = ContextVar(
    "original_knowledge_comparison_producer", default=DEFAULT_PRODUCER
)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule not in (
        "card_knowledge_diff@2",
        "knowledge_state@5",
        "protein_knowledge_projection@1",
    ):
        raise StorageError("Unsupported original knowledge-comparison rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
