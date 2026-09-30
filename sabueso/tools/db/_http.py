"""The one way source clients reach the network (#82, #83, #86).

- **A named client.** Some servers refuse Python's default user agent (DISEASES's
  downloads, Reactome's Content Service answer 403). Every request carries Sabueso's
  name and version.
- **Retries for transient failures.** HTTP 429, 502, 503 and 504, and a refused or
  reset connection, are retried up to ``RETRIES`` times, waiting longer each time
  (``Retry-After`` is honoured, up to ``MAX_WAIT`` seconds). Every Sabueso request is a
  read (GraphQL posts too), so a retry changes nothing on the source.
- **What is not retried.** A timeout: the source has already had its time, and asking
  again would multiply it. Any other error reaches the client unchanged, which keeps
  its own reading: a 404 is "not found", never a failure.

Clients import ``urlopen`` from here instead of ``urllib.request``.

- **Many requests to one service** (``gather``, #98). A source answered one record per
  request (UniChem, one compound at a time) is asked by a few threads at once, never
  faster than the pace the service asks for or Sabueso chooses to keep (``Pace``).
  Results come back in the order asked; a failure of one request is that request's
  answer, never the others'.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request
from urllib.request import urlopen as _urlopen

RETRIES = 2
BACKOFF = 1.5  # seconds, doubled on each retry
MAX_WAIT = 20.0
TRANSIENT = {429, 502, 503, 504}


def user_agent() -> str:
    from sabueso import __version__

    return f"Sabueso/{__version__} (+https://github.com/uibcdf/sabueso)"


def request(
    url: str, data: bytes | None = None, headers: Dict[str, str] | None = None
) -> Request:
    """A ``Request`` carrying Sabueso's user agent (and any other headers)."""
    return Request(
        url, data=data, headers={"User-Agent": user_agent(), **(headers or {})}
    )


def _named(target: Any) -> Request:
    if isinstance(target, Request):
        if not target.has_header("User-agent"):
            target.add_header("User-Agent", user_agent())
        return target
    return request(str(target))


def _wait(attempt: int, error: Exception) -> float:
    retry_after = getattr(error, "headers", None) and error.headers.get("Retry-After")
    if retry_after and str(retry_after).isdigit():
        return min(float(retry_after), MAX_WAIT)
    return min(BACKOFF * (2**attempt), MAX_WAIT)


def _timed_out(error: URLError) -> bool:
    return isinstance(error.reason, TimeoutError) or "timed out" in str(error.reason)


def urlopen(target: Any, timeout: float = 30.0, sleep=time.sleep):
    """``urllib.request.urlopen`` with Sabueso's user agent and retries for transient
    failures; see the module docstring."""
    named = _named(target)
    for attempt in range(RETRIES + 1):
        try:
            return _urlopen(named, timeout=timeout)
        except HTTPError as exc:
            if exc.code not in TRANSIENT or attempt == RETRIES:
                raise
            sleep(_wait(attempt, exc))
        except URLError as exc:
            if _timed_out(exc) or attempt == RETRIES:
                raise
            sleep(_wait(attempt, exc))
    raise AssertionError("unreachable")  # pragma: no cover


class Pace:
    """At most ``per_second`` requests start per second, across threads."""

    def __init__(
        self, per_second: float, sleep=time.sleep, clock=time.monotonic
    ) -> None:
        self.interval = 1.0 / per_second
        self._lock = threading.Lock()
        self._next = 0.0
        self._sleep, self._clock = sleep, clock

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            start = max(now, self._next)
            self._next = start + self.interval
        if start > now:
            self._sleep(start - now)


def gather(
    call: Callable[[Any], Any],
    items: Iterable[Any],
    workers: int = 4,
    per_second: float | None = None,
    expected: Tuple[type, ...] = (),
) -> List[Tuple[Any, Any]]:
    """``[(item, answer)]`` in the order of ``items``: ``call(item)``'s result, or the
    exception it raised when that exception is ``expected`` (a source's not found or
    failure). Any other exception is a fault, and is raised.

    ``workers`` threads ask at once, and no more than ``per_second`` requests start per
    second (unpaced when None).
    """
    items = list(items)
    pace = Pace(per_second) if per_second else None

    def one(item: Any) -> Any:
        if pace is not None:
            pace.wait()
        try:
            return call(item)
        except expected as exc:
            return exc

    if workers <= 1 or len(items) <= 1:
        return [(item, one(item)) for item in items]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(zip(items, pool.map(one, items)))
