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

Nothing is archived unless the user asks: ``with archive.recording():`` (or
``sabueso.RetrievalArchive(path)``). A card built inside lists the records its build
made (``quality.retrievals``). Replaying from the archive, and reusing fresh answers,
come next (#100).

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List

from sabueso.core.errors import StorageError

PREFIX = "sabueso:retrieval:"
#: Headers clients read; the rest of a response's headers are not kept.
KEPT_HEADERS = (
    "Content-Type",
    "Last-Modified",
    "InterPro-Version",
    "X-Total-Results",
    "X-UniProt-Release",
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
    content_hash TEXT NOT NULL REFERENCES contents (content_hash)
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
    ) -> Dict[str, Any]:
        """Keep one answer; return its record (``ref``, ``content_hash``, …)."""
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
                "status, headers, retrieved_at, content_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ref,
                    method,
                    url,
                    record["request_hash"],
                    record["status"],
                    json.dumps(record["headers"], sort_keys=True),
                    record["retrieved_at"],
                    record["content_hash"],
                ),
            )
        return {"ref": ref, "size": len(content), **record}

    @contextmanager
    def recording(self) -> Iterator["RetrievalArchive"]:
        """Within the block, every answer a source client receives is archived."""
        token = _ACTIVE.set(self)
        try:
            yield self
        finally:
            _ACTIVE.reset(token)

    # --- reading -----------------------------------------------------------------------

    def get(self, ref: str) -> Dict[str, Any]:
        """A record, with its stored response (``content``, bytes), checked against its
        content hash."""
        with self._session() as conn:
            row = conn.execute(
                "SELECT r.method, r.url, r.request_hash, r.status, r.headers, "
                "r.retrieved_at, r.content_hash, c.body FROM retrievals r "
                "JOIN contents c ON c.content_hash = r.content_hash WHERE r.ref = ?",
                (ref,),
            ).fetchone()
        if row is None:
            raise StorageError(f"No retrieval {ref} in {self.path}.")
        method, url, request_hash, status, headers, when, content_hash, body = row
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
            "content": content,
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


def active() -> RetrievalArchive | None:
    """The archive answers are recorded in, in this context, or None."""
    return _ACTIVE.get()


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


def manifest(archive: RetrievalArchive, made: List[Dict[str, Any]]) -> Dict[str, Any]:
    """What a card records of its build's retrievals (``quality.retrievals``)."""
    seen: Dict[str, Dict[str, Any]] = {}
    for r in made:
        seen.setdefault(
            r["ref"],
            {
                "ref": r["ref"],
                "method": r["method"],
                "url": r["url"],
                "status": r["status"],
                "retrieved_at": r["retrieved_at"],
                "content_hash": r["content_hash"],
                "size": r["size"],
            },
        )
    return {"archive": archive.path.name, "records": list(seen.values())}
