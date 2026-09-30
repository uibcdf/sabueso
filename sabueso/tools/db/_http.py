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

- **What was downloaded** (#100). While a retrieval archive is recording
  (``tools.db._archive``), every final answer, a 404 included, is kept there, and the
  client receives it as it would have.
- **When an answer was read** (``stamp``, #100). A client opens a stamp when it starts
  asking, and uses ``stamp.value`` as the retrieval time of what it returns: the time
  of its first answer when an archive is active (so that a record and the statements
  taken from it agree, and a replayed answer keeps its original time), else the time
  the client started.
- **Many requests to one service** (``gather``, #98). A source answered one record per
  request (UniChem, one compound at a time) is asked by a few threads at once, never
  faster than the pace the service asks for or Sabueso chooses to keep (``Pace``).
  Results come back in the order asked; a failure of one request is that request's
  answer, never the others'.
"""

from __future__ import annotations

import contextvars
import io
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


_STAMP: contextvars.ContextVar = contextvars.ContextVar("sabueso_stamp", default=None)


def _clock() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Stamp:
    """The retrieval time of one client call, and the source it asks; see the module
    docstring."""

    def __init__(self, source: str | None = None) -> None:
        self.started = _clock()
        self.first: str | None = None
        self.source = source

    @property
    def value(self) -> str:
        return self.first or self.started

    def __str__(self) -> str:
        return self.value


def stamp(source: str | None = None) -> Stamp:
    """Open the stamp of a client call: the answers it receives next date it, and are
    archived as ``source``'s (the name its SourceAssertions carry)."""
    opened = Stamp(source)
    _STAMP.set(opened)
    return opened


def _source() -> str | None:
    opened = _STAMP.get()
    return opened.source if opened is not None else None


def _answered_at(when: str) -> None:
    opened = _STAMP.get()
    if opened is not None and opened.first is None:
        opened.first = when


class Answer:
    """A response read whole, as a client uses it: ``read()``, ``status``, ``headers``,
    and as a context manager. What an archive keeps is what the client received."""

    def __init__(self, content: bytes, status: int, headers: Any, retrieved_at: str):
        self._content, self.status, self.headers = content, status, headers
        self.retrieved_at = retrieved_at

    def read(self, *_: Any) -> bytes:
        return self._content

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "Answer":
        return self

    def __exit__(self, *_: Any) -> None:
        return None


def _kept(headers: Any) -> Dict[str, str]:
    from sabueso.tools.db._archive import KEPT_HEADERS

    return {k: headers.get(k) for k in KEPT_HEADERS if headers and headers.get(k)}


def urlopen(target: Any, timeout: float = 30.0, sleep=time.sleep):
    """``urllib.request.urlopen`` with Sabueso's user agent and retries for transient
    failures, and the answer archived when an archive is recording; see the module
    docstring."""
    from sabueso.tools.db import _archive, _mirror

    mode = _archive.active()
    if mode is None:
        _refuse_offline(target)
        return _open(target, timeout, sleep)
    archive = mode.archive
    named = _named(target)
    method, url, body = named.get_method(), named.full_url, named.data
    if mode.name in ("replay", "reuse"):
        planned = mode.planned(method, url, body)
        kept = (
            archive.get(planned)
            if planned
            else archive.find(
                method, url, body, mode.max_age if mode.name == "reuse" else None
            )
        )
        if kept is not None:
            return _from_archive(kept)
        if mode.name == "replay":
            from sabueso.core.errors import NotArchivedError

            raise NotArchivedError(
                f"Not in the retrieval archive {archive.path.name}: {method} {url}"
            )
    if _mirror.offline():
        _refuse_offline(named)
    retrieved_at = _archive._now()
    try:
        response = _open(named, timeout, sleep)
    except HTTPError as exc:
        # An HTTP answer is an answer (a 404 is "not found"): kept, then raised again.
        content = exc.read() if exc.fp is not None else b""
        record = archive.record(
            method,
            url,
            body,
            exc.code,
            _kept(exc.headers),
            content,
            retrieved_at,
            source=_source(),
        )
        _archive.note(record)
        _answered_at(retrieved_at)
        raise HTTPError(
            exc.url, exc.code, exc.msg, exc.headers, io.BytesIO(content)
        ) from None
    with response:
        content = response.read()
        status = getattr(response, "status", 200)
        headers = response.headers
    record = archive.record(
        method, url, body, status, _kept(headers), content, retrieved_at, _source()
    )
    _archive.note(record)
    _answered_at(retrieved_at)
    return Answer(content, status, headers, retrieved_at)


OFFLINE = "Not asked: working offline"


def _refuse_offline(target: Any) -> None:
    from sabueso.tools.db import _mirror

    if _mirror.offline():
        from sabueso.core.errors import OfflineError

        url = target.full_url if isinstance(target, Request) else str(target)
        raise OfflineError(f"{OFFLINE}: {url}")


def _from_archive(kept: Dict[str, Any]):
    """An archived answer, served as the source served it, with its original time."""
    from email.message import Message

    from sabueso.tools.db import _archive

    headers = Message()
    for key, value in kept["headers"].items():
        headers[key] = value
    _archive.note(_archive.summary(kept))
    _answered_at(kept["retrieved_at"])
    if kept["status"] >= 400:
        raise HTTPError(
            kept["url"],
            kept["status"],
            "archived",
            headers,
            io.BytesIO(kept["content"]),
        )
    return Answer(kept["content"], kept["status"], headers, kept["retrieved_at"])


def _open(target: Any, timeout: float, sleep):
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
        # Each request runs in a copy of the caller's context, so an archive that is
        # recording, and the build collecting its records, see it (#100).
        futures = [
            pool.submit(contextvars.copy_context().run, one, item) for item in items
        ]
        return list(zip(items, (f.result() for f in futures)))


def download(url: str, path: Any, timeout: float = 600.0, chunk: int = 1 << 20) -> str:
    """Stream a release file to ``path`` (written next to it, then renamed) and return
    its MD5. For whole releases (mirrors, #100): not kept by a retrieval archive, since
    the file itself is kept and checked against the checksum its source publishes."""
    import hashlib
    from pathlib import Path

    target = Path(path)
    partial = target.with_name(target.name + ".part")
    md5 = hashlib.md5()  # nosec - compared with the checksum the source publishes
    with _open(url, timeout, time.sleep) as response, open(partial, "wb") as out:
        while True:
            block = response.read(chunk)
            if not block:
                break
            md5.update(block)
            out.write(block)
    partial.replace(target)
    return md5.hexdigest()
