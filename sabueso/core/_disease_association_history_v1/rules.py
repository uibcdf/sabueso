"""Original generated labels at declared disease/knowledge rule paths only."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+227.g0e17f85"
_PRODUCER = ContextVar(
    "original_disease_association_producer", default=DEFAULT_PRODUCER
)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule != "disease_association_context@1":
        raise StorageError("Unsupported original disease association rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
