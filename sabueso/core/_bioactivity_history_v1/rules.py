"""Original generated-rule metadata for private comparison, never source rewriting."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+200.g2eb6114"
_PRODUCERS = ContextVar(
    "original_bioactivity_producers", default=({}, DEFAULT_PRODUCER)
)
_REQUEST = ContextVar("original_bioactivity_native_request", default=None)
RULES = frozenset(
    {
        "bioactivity_class@3",
        "bioactivity_class@4",
        "pchembl_consistency@1",
        "unit_scale_discrepancy@1",
        "measurement_identity@1",
        "measurement_identity@2",
        "bioactivity_target_scope@2",
        "measurement_group_explanation@1",
        "measurement_group_explanation@2",
        "bioactivity_explanation@1",
        "bioactivity_explanation@2",
        "bioactivity_explanation@3",
        "bioactivity_explanation@4",
        "literature_explanation@1",
        "knowledge_state@5",
    }
)


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
        raise StorageError("Unsupported original bioactivity derivation rule.")
    versions, default = _PRODUCERS.get()
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": versions.get((_REQUEST.get(), rule), default),
    }
