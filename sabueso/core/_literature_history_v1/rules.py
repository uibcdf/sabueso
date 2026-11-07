"""Original generated-rule labels at declared output paths, never source rewriting."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+202.g1145ea3"
_PRODUCERS = ContextVar("original_literature_producers", default=({}, DEFAULT_PRODUCER))
_REQUEST = ContextVar("original_literature_native_request", default=None)
RULES = frozenset({"literature_explanation@1", "knowledge_state@5"})


@contextmanager
def producers(versions, default=DEFAULT_PRODUCER):
    token = _PRODUCERS.set((dict(versions), default))
    try:
        yield
    finally:
        _PRODUCERS.reset(token)


@contextmanager
def native_request(method):
    token = _REQUEST.set(method)
    try:
        yield
    finally:
        _REQUEST.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule not in RULES:
        raise StorageError("Unsupported original literature derivation rule.")
    versions, default = _PRODUCERS.get()
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": versions.get((_REQUEST.get(), rule), default),
    }
