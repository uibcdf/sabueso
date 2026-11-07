"""Original generated labels in both frozen scientific and literature contexts."""

from contextlib import contextmanager

from .._bioactivity_history_v1 import rules as _scientific
from .._literature_history_v1 import rules as _literature

DEFAULT_PRODUCER = "0.14.0+202.g1145ea3"


@contextmanager
def producers(versions, default=DEFAULT_PRODUCER):
    with (
        _scientific.producers(versions, default),
        _literature.producers(versions, default),
    ):
        yield


@contextmanager
def native_request(method):
    with _scientific.native_request(method), _literature.native_request(method):
        yield
