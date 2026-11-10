"""Original generated labels, only at explicitly generated tissue-rule paths."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+239.g738a422"
_PRODUCER = ContextVar("original_protein_context_producer", default=DEFAULT_PRODUCER)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule not in (
        "protein_context_projection@1",
        "captured_sequence_comparison@1",
        "equal_length_positions@1",
    ):
        raise StorageError("Unsupported original protein-context rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
