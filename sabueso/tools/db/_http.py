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
"""

from __future__ import annotations

import time
from typing import Any, Dict
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
