"""Original generated labels, only at explicitly generated tissue-rule paths."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+234.g87537f5"
_PRODUCER = ContextVar("original_sequence_change_producer", default=DEFAULT_PRODUCER)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule != "sequence_change_projection@1":
        raise StorageError("Unsupported original sequence-change rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
