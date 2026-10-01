"""The retrieval archive: what Sabueso downloaded, kept to be audited (#100, phase 1).

Every request a source client makes goes through ``_http.urlopen``. While an archive is
active, each answer is kept there as a ``RetrievalRecord``:

- what was asked: method, URL and the hash of the request body;
- what came back: HTTP status, the headers clients read, and the response, stored once
  per distinct content (zlib-compressed, addressed by its SHA-256);
- when it was read.

A record is referenced as ``sabueso:retrieval:sha256:<hex>``, a hash of all of the
above, so the same answer read at another time is another record over the same stored
content.

Nothing is archived unless the user asks. Three modes, each a context:

- ``archive.recording()``: every answer is received from the source and kept;
- ``archive.reusing(max_age)``: an answer kept within ``max_age`` is used instead of
  asking again; anything else is asked and kept;
- ``archive.replaying(of=card)``: answers come from the archive only, never from the
  network. With ``of`` (a card, or its ``quality.retrievals``), a request is answered
  with the records that card's build received, in the order it received them, so a
  request made twice gets its two answers; otherwise with the latest record. A request
  the archive does not hold raises ``NotArchivedError``, and a card records that source
  as ``not_queried`` (``not_in_archive``), never as absent or failed.

An answer taken from the archive keeps the time it was read. A card built inside lists
the records its build used, and the mode (``quality.retrievals``).

The archive is a local SQLite file, the user's. Whether a source's terms allow keeping
or sharing its responses is recorded per source in the registry (#100, next step).
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import sqlite3
import threading
import zlib
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List

from sabueso.core.errors import StorageError
from sabueso.core.terms import retention

PREFIX = "sabueso:retrieval:"
#: Headers clients read; the rest of a response's headers are not kept.
KEPT_HEADERS = (
    "Content-Type",
    "Last-Modified",
    "InterPro-Version",
    "X-Total-Results",
    "X-UniProt-Release",
    "Link",
    "x-throttling-control",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS archive_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contents (
    content_hash TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    body BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS retrievals (
    rid INTEGER PRIMARY KEY,
    ref TEXT NOT NULL UNIQUE,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    request_hash TEXT,
    status INTEGER NOT NULL,
    headers TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    content_hash TEXT NOT NULL REFERENCES contents (content_hash),
    source TEXT
);
CREATE INDEX IF NOT EXISTS retrievals_by_request
    ON retrievals (method, url, request_hash, retrieved_at);
"""
FORMAT = "1"

#: The archive requests are recorded in, and the records a build made, per context.
_ACTIVE: contextvars.ContextVar = contextvars.ContextVar(
    "sabueso_archive", default=None
)
_MADE: contextvars.ContextVar = contextvars.ContextVar(
    "sabueso_retrievals", default=None
)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RetrievalArchive:
    """A local archive of what source clients downloaded; see the module docstring."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._session() as conn:
            conn.executescript(SCHEMA)
            row = conn.execute(
                "SELECT value FROM archive_meta WHERE key = 'format'"
            ).fetchone()
            if row is None:
                conn.execute("INSERT INTO archive_meta VALUES ('format', ?)", (FORMAT,))
            elif row[0] != FORMAT:
                raise StorageError(
                    f"{self.path} is a retrieval archive of format {row[0]}; this "
                    f"Sabueso reads format {FORMAT}."
                )

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.path, timeout=30)
        except sqlite3.Error as exc:
            raise StorageError(f"Cannot open {self.path}: {exc}") from exc
        try:
            with conn:
                yield conn
        except sqlite3.DatabaseError as exc:
            raise StorageError(
                f"{self.path} is not a usable retrieval archive: {exc}"
            ) from exc
        finally:
            conn.close()

    # --- recording ---------------------------------------------------------------------

    def record(
        self,
        method: str,
        url: str,
        request_body: bytes | None,
        status: int,
        headers: Dict[str, str],
        content: bytes,
        retrieved_at: str | None = None,
        source: str | None = None,
    ) -> Dict[str, Any]:
        """Keep one answer; return its record (``ref``, ``content_hash``, …).
        ``source`` is the SourceAssertion source name of the client that asked; it is
        not part of the reference, which names what was asked and answered."""
        record = {
            "method": method,
            "url": url,
            "request_hash": _sha256(request_body) if request_body else None,
            "status": int(status),
            "headers": {k: headers[k] for k in sorted(headers)},
            "retrieved_at": retrieved_at or _now(),
            "content_hash": _sha256(content),
        }
        text = json.dumps(record, sort_keys=True, separators=(",", ":"))
        ref = PREFIX + _sha256(text.encode("utf-8"))
        with self._lock, self._session() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO contents VALUES (?, ?, ?)",
                (record["content_hash"], len(content), zlib.compress(content, 6)),
            )
            conn.execute(
                "INSERT OR IGNORE INTO retrievals (ref, method, url, request_hash, "
                "status, headers, retrieved_at, content_hash, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ref,
                    method,
                    url,
                    record["request_hash"],
                    record["status"],
                    json.dumps(record["headers"], sort_keys=True),
                    record["retrieved_at"],
                    record["content_hash"],
                    source,
                ),
            )
        return {"ref": ref, "size": len(content), "source": source, **record}

    @contextmanager
    def _mode(
        self, mode: str, max_age: timedelta | None = None, plan: Any = None
    ) -> Iterator[Any]:
        token = _ACTIVE.set(Mode(self, mode, max_age, plan))
        try:
            yield self
        finally:
            _ACTIVE.reset(token)

    def recording(self):
        """Within the block, every answer a source client receives is archived."""
        return self._mode("record")

    def reusing(self, max_age: timedelta):
        """Within the block, an answer archived within ``max_age`` is used instead of
        asking the source again; the rest is asked and archived."""
        if not isinstance(max_age, timedelta) or max_age.total_seconds() <= 0:
            raise ValueError("max_age is a positive datetime.timedelta")
        return self._mode("reuse", max_age)

    def replaying(self, of: Any = None):
        """Within the block, answers come from the archive only; the network is never
        asked. ``of``: a card (or its ``quality.retrievals``) whose build to replay, in
        the order its answers were received."""
        return self._mode("replay", plan=_plan(of))

    def find(
        self,
        method: str,
        url: str,
        request_body: bytes | None,
        max_age: timedelta | None = None,
    ) -> Dict[str, Any] | None:
        """The latest record of this request (within ``max_age`` of now), or None."""
        request_hash = _sha256(request_body) if request_body else None
        query = (
            "SELECT ref, retrieved_at FROM retrievals WHERE method = ? AND url = ? "
            "AND request_hash IS ? ORDER BY retrieved_at DESC, rid DESC LIMIT 1"
        )
        with self._session() as conn:
            row = conn.execute(query, (method, url, request_hash)).fetchone()
        if row is None:
            return None
        if max_age is not None:
            when = datetime.fromisoformat(row[1])
            if datetime.now(timezone.utc) - when > max_age:
                return None
        return self.get(row[0])

    # --- reading -----------------------------------------------------------------------

    def get(self, ref: str) -> Dict[str, Any]:
        """A record, with its stored response (``content``, bytes), checked against its
        content hash."""
        with self._session() as conn:
            row = conn.execute(
                "SELECT r.method, r.url, r.request_hash, r.status, r.headers, "
                "r.retrieved_at, r.content_hash, r.source, c.body FROM retrievals r "
                "JOIN contents c ON c.content_hash = r.content_hash WHERE r.ref = ?",
                (ref,),
            ).fetchone()
        if row is None:
            raise StorageError(f"No retrieval {ref} in {self.path}.")
        method, url, request_hash, status, headers, when, content_hash, source, body = (
            row
        )
        content = zlib.decompress(body)
        if _sha256(content) != content_hash:
            raise StorageError(
                f"Retrieval {ref} in {self.path} no longer matches its content hash; "
                "the archive was changed outside Sabueso."
            )
        return {
            "ref": ref,
            "method": method,
            "url": url,
            "request_hash": request_hash,
            "status": status,
            "headers": json.loads(headers),
            "retrieved_at": when,
            "content_hash": content_hash,
            "source": source,
            "retention": retention(source),
            "content": content,
        }

    def sources(self) -> Dict[str, Any]:
        """Per source, how many answers the archive holds, and what its licence allows
        with them (``retention_from_licence@1``)."""
        with self._session() as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*) FROM retrievals GROUP BY source ORDER BY source"
            ).fetchall()
        return {
            (source or "unattributed"): {"records": n, "retention": retention(source)}
            for source, n in rows
        }

    def stats(self) -> Dict[str, Any]:
        """How many records and distinct contents it holds, and their size."""
        with self._session() as conn:
            records = conn.execute("SELECT COUNT(*) FROM retrievals").fetchone()[0]
            contents, raw, stored = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(size), 0), "
                "COALESCE(SUM(LENGTH(body)), 0) FROM contents"
            ).fetchone()
        return {
            "records": records,
            "contents": contents,
            "bytes": raw,
            "stored_bytes": stored,
        }


# --- hooks for _http and the card tools ---------------------------------------------------


def _plan(of: Any) -> Dict[tuple, List[str]] | None:
    """Per request, the records a build received, in order (``replaying(of=...)``)."""
    if of is None:
        return None
    manifest = of.quality.get("retrievals") if hasattr(of, "quality") else of
    if not manifest or "records" not in manifest:
        raise ValueError("replaying(of=...) takes a card built with an archive")
    plan: Dict[tuple, List[str]] = {}
    for r in manifest["records"]:
        key = (r["method"], r["url"], r.get("request_hash"))
        plan.setdefault(key, []).append(r["ref"])
    return plan


class Mode:
    """An active archive, how it is used (``record``, ``reuse``, ``replay``), the
    freshness a reused answer must have, and the build a replay follows."""

    def __init__(
        self, archive: RetrievalArchive, name: str, max_age: Any, plan: Any = None
    ) -> None:
        self.archive, self.name, self.max_age = archive, name, max_age
        self.plan = plan
        self._lock = threading.Lock()

    def planned(self, method: str, url: str, request_body: bytes | None) -> str | None:
        """The next record the replayed build received for this request, or None."""
        if not self.plan:
            return None
        key = (method, url, _sha256(request_body) if request_body else None)
        with self._lock:
            refs = self.plan.get(key)
            if not refs:
                return None
            return refs.pop(0) if len(refs) > 1 else refs[0]

    @property
    def path(self) -> Path:
        return self.archive.path


def active() -> Mode | None:
    """The archive in use in this context, and its mode, or None."""
    return _ACTIVE.get()


def summary(record: Dict[str, Any]) -> Dict[str, Any]:
    """What a build notes of a record (``quality.retrievals``)."""
    return {
        k: record.get(k)
        for k in (
            "ref",
            "source",
            "method",
            "url",
            "request_hash",
            "status",
            "retrieved_at",
            "content_hash",
        )
    } | {"size": record.get("size", len(record.get("content") or b""))}


def note(record: Dict[str, Any]) -> None:
    """Add a record to the build being collected, if any."""
    made = _MADE.get()
    if made is not None:
        made.append(record)


@contextmanager
def collecting() -> Iterator[List[Dict[str, Any]]]:
    """The records made inside the block (a card's build)."""
    outer = _MADE.get()
    made: List[Dict[str, Any]] = []
    token = _MADE.set(made)
    try:
        yield made
    finally:
        _MADE.reset(token)
        if outer is not None:
            outer.extend(made)


def manifest(mode: Mode, made: List[Dict[str, Any]]) -> Dict[str, Any]:
    """What a card records of its build's retrievals (``quality.retrievals``)."""
    # In the order received; a request answered twice is listed twice.
    records = [summary(r) for r in made]
    out: Dict[str, Any] = {"archive": mode.path.name, "mode": mode.name}
    if mode.max_age is not None:
        out["max_age_seconds"] = int(mode.max_age.total_seconds())
    return {**out, "records": records}
