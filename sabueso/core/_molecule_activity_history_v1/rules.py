"""Declared SDK205 generated labels; opaque source records stay literal."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy

from .._bioactivity_history_v2.rules import producers as native_producers
from ..errors import StorageError

DEFAULT_PRODUCER = "0.14.0+205.gddc1fc8"
_PRODUCER = ContextVar("original_molecule_activity_producer", default=DEFAULT_PRODUCER)
RULES = frozenset(
    {
        "molecule_activity_context@1",
        "ligand_measurement_count@1",
        "ligand_measurement_count@2",
        "ligand_site_explanation@1",
        "annotated_site_overlap@3",
        "ligand_deck_explanation@2",
        "ligand_deck_explanation@3",
        "ligand_deck_explanation@4",
        "ligand_deck_explanation@5",
    }
)


@contextmanager
def producers(versions=None, primary=DEFAULT_PRODUCER):
    token = _PRODUCER.set(primary)
    try:
        with native_producers(versions or {}, primary):
            yield
    finally:
        _PRODUCER.reset(token)


def make_derivation(rule, inputs=None, parameters=None):
    if rule not in RULES:
        raise StorageError("Unsupported original molecule activity derivation rule.")
    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": deepcopy(parameters or {}),
        "sabueso_version": _PRODUCER.get(),
    }
