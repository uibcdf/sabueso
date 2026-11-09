"""Original generated labels, only at explicitly generated tissue-rule paths."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+230.gc5b573b"
_PRODUCER = ContextVar("original_variant_producer", default=DEFAULT_PRODUCER)


@contextmanager
def producer(version):
    token = _PRODUCER.set(version)
    try:
        yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule not in {
        "pext_at_variant@2",
        "isoform_exon_usage@3",
        "variant_tissue_usage_explanation@2",
        "isoform_tissue_usage_explanation@2",
        "gtex_tissue_key@1",
    }:
        raise StorageError("Unsupported original variant tissue rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
