"""The knowledge store: versioned cards in normalized SQLite (uibcdf/sabueso#7, #27).

JSON and JSONL stay Sabueso's exchange formats (diffable, readable, easy to share). The
store is where cards are kept and worked with:

- **Snapshots.** Saving a card stores its exact state under its content address
  (``sabueso.core.snapshot``) and returns a pinned reference,
  ``<card_id>@sha256:<hex>``. A snapshot is immutable: the same content is stored once,
  and a pinned read returns exactly what was saved or fails. It never returns another
  state of the card, the latest one included.
- **Revisions.** Each card keeps its history: the snapshots it was saved as, in order,
  with the time and an optional note. An unpinned reference, the bare ``card_id``, means
  the latest revision. Saving the state a card already has adds nothing.
- **Normalized rows.** SourceAssertions and relationships are rows, stored once per
  distinct content and shared by every snapshot and card that holds them. An id alone
  is not the key: a SourceAssertion id names what was stated, so the same id observed in
  another source release is another row. Relationships are indexed by subject, object
  and predicate, so "which cards point at this molecule?" is a query, not a scan.
- **Decks** are versioned like cards (#58): a deck revision is its ``meta`` and the
  pinned states of its cards, content-addressed, and a deck is referenced as
  ``sabueso:deck:<name>`` (latest) or ``sabueso:deck:<name>@sha256:…`` (exact).
- **Knowledge packets** (#71) are versioned like decks: a packet revision is its
  document, content-addressed, and every card state it cites must be in the store. A
  packet is referenced as ``sabueso:packet:<name>`` (latest) or
  ``sabueso:packet:<name>@sha256:…`` (exact). Each revision also records the packet's
  content-equivalence id, so that a history shows when the knowledge last changed.
- **Unchanged knowledge is stored once** (format 2, #99). A SourceAssertion's row is
  its content without ``retrieved_at``, which is kept where the row joins each
  snapshot. A card rebuilt from sources that did not change shares every row with its
  previous revision, and each revision still knows when each statement was read.
- **Compressed** (format 2): documents and rows are stored zlib-compressed. Ids and
  checks are computed on the canonical JSON, never on the stored bytes.
- **Every read verifies.** A snapshot is rebuilt from its rows, hashed again and
  checked against its id; then ``Card.from_dict`` checks its schema version and its
  quantities seal. A store changed outside Sabueso is refused with ``StorageError``.

The file states its format (``store_meta``). Format 2 reads a format-1 store and
upgrades it in place: its rows stay as they were (``retrieved_at`` inside, uncompressed)
and new ones are written in format 2. A Sabueso that reads only format 1 refuses it. Its tables are Sabueso's
implementation, not a contract: other MOLI components reference cards through the
reference forms (uibcdf/moli#3), not by reading these tables.
"""

from __future__ import annotations

import json
import os
import sqlite3
import zlib
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

from sabueso._private.argdigest import arg_digest

from .errors import StorageError
from .snapshot import (
    DECK_NAME,
    DECK_PREFIX,
    canonical_json,
    deck_snapshot_id,
    digest,
    parse_ref,
    pinned_ref,
    snapshot_id,
)

FORMAT = 2
#: Formats this Sabueso opens; an older one is upgraded in place.
UPGRADABLE = {"1"}
#: The two stores of a card that become rows; the rest of the card is one document.
ROWS = ("source_assertion_store", "relationship_store")

SCHEMA = """
CREATE TABLE IF NOT EXISTS store_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL,
    entity_type TEXT,
    schema_version TEXT NOT NULL,
    document TEXT NOT NULL,
    quantities TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revisions (
    revision INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    stored_at TEXT NOT NULL,
    note TEXT
);
CREATE INDEX IF NOT EXISTS revisions_by_card ON revisions (card_id, revision);
CREATE TABLE IF NOT EXISTS snapshot_numbers (
    sno INTEGER PRIMARY KEY,
    snapshot_id TEXT NOT NULL UNIQUE REFERENCES snapshots (snapshot_id)
);
CREATE TABLE IF NOT EXISTS retrieval_times (
    tid INTEGER PRIMARY KEY,
    value TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS sa_rows (
    rid INTEGER PRIMARY KEY,
    body_hash TEXT NOT NULL UNIQUE,
    sa_id TEXT NOT NULL,
    subject_ref TEXT,
    field_path TEXT,
    source_name TEXT,
    source_version TEXT,
    body BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS sa_rows_by_id ON sa_rows (sa_id);
CREATE INDEX IF NOT EXISTS sa_rows_by_subject ON sa_rows (subject_ref, field_path);
CREATE TABLE IF NOT EXISTS card_sa (
    sno INTEGER NOT NULL REFERENCES snapshot_numbers (sno),
    position INTEGER NOT NULL,
    rid INTEGER NOT NULL REFERENCES sa_rows (rid),
    tid INTEGER REFERENCES retrieval_times (tid),
    PRIMARY KEY (sno, position)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS card_sa_by_row ON card_sa (rid);
CREATE TABLE IF NOT EXISTS rel_rows (
    rid INTEGER PRIMARY KEY,
    body_hash TEXT NOT NULL UNIQUE,
    rel_id TEXT NOT NULL,
    subject_ref TEXT,
    predicate TEXT,
    object_ref TEXT,
    body BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS rel_rows_by_id ON rel_rows (rel_id);
CREATE INDEX IF NOT EXISTS rel_rows_by_object ON rel_rows (object_ref, predicate);
CREATE INDEX IF NOT EXISTS rel_rows_by_subject ON rel_rows (subject_ref, predicate);
CREATE TABLE IF NOT EXISTS card_rel (
    sno INTEGER NOT NULL REFERENCES snapshot_numbers (sno),
    position INTEGER NOT NULL,
    rid INTEGER NOT NULL REFERENCES rel_rows (rid),
    PRIMARY KEY (sno, position)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS card_rel_by_row ON card_rel (rid);
CREATE TABLE IF NOT EXISTS deck_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    meta TEXT NOT NULL,
    members TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deck_revisions (
    revision INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES deck_snapshots (snapshot_id),
    stored_at TEXT NOT NULL,
    note TEXT
);
CREATE INDEX IF NOT EXISTS deck_revisions_by_name ON deck_revisions (name, revision);
CREATE TABLE IF NOT EXISTS packet_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    document TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS packet_revisions (
    revision INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES packet_snapshots (snapshot_id),
    stored_at TEXT NOT NULL,
    note TEXT
);
CREATE INDEX IF NOT EXISTS packet_revisions_by_name ON packet_revisions (name, revision);
"""

#: The latest revision of every card.
HEADS = """
SELECT r.card_id, r.snapshot_id FROM revisions r
JOIN (SELECT card_id, MAX(revision) AS last FROM revisions GROUP BY card_id) m
  ON r.card_id = m.card_id AND r.revision = m.last
"""
#: (table of rows, membership table, id column, columns taken from each row)
ROW_TABLES = {
    "source_assertion_store": (
        "sa_rows",
        "card_sa",
        "sa_id",
        ("subject_ref", "field_path", "source_name", "source_version"),
    ),
    "relationship_store": (
        "rel_rows",
        "card_rel",
        "rel_id",
        ("subject_ref", "predicate", "object_ref"),
    ),
}
#: Format 1's tables, copied into format 2's by ``_upgrade`` and then dropped:
#: (rows, members, the new rows and members).
FORMAT_1_TABLES = (
    ("source_assertions", "snapshot_source_assertions", "sa_rows", "card_sa"),
    ("relationships", "snapshot_relationships", "rel_rows", "card_rel"),
)


def _pack(text: str) -> bytes:
    """What a document or row is stored as (format 2): its text, compressed."""
    return zlib.compress(text.encode("utf-8"), 6)


def _unpack(value: Any) -> str:
    """The text of a stored document or row; format-1 values are text already."""
    if isinstance(value, bytes):
        return zlib.decompress(value).decode("utf-8")
    return value


#: What a SourceAssertion row leaves out, kept per snapshot instead (#99).
PER_SNAPSHOT = "retrieved_at"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _columns(key: str, row: Dict[str, Any]) -> tuple:
    if key == "source_assertion_store":
        source = row.get("source") or {}
        version = source.get("version")
        return (
            row.get("subject_ref"),
            row.get("field_path"),
            source.get("name"),
            None if version is None else str(version),
        )
    return (row.get("subject_ref"), row.get("predicate"), row.get("object_ref"))


class KnowledgeStore:
    """Versioned cards, their SourceAssertions and relationships, and decks, in SQLite."""

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._session() as conn:
            conn.executescript(SCHEMA)
            row = conn.execute(
                "SELECT value FROM store_meta WHERE key = 'format'"
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO store_meta (key, value) VALUES ('format', ?)",
                    (str(FORMAT),),
                )
            elif row[0] in UPGRADABLE:
                self._upgrade(conn)
            elif row[0] != str(FORMAT):
                raise StorageError(
                    f"{self.path} is a knowledge store of format {row[0]}; this Sabueso "
                    f"reads format {FORMAT}."
                )

    @staticmethod
    def _upgrade(conn: sqlite3.Connection) -> None:
        """Format 1 to 2, in place (#99). Rows are copied as they were written (text,
        ``retrieved_at`` inside), numbered, and their old tables dropped."""
        tables = {name for (name,) in conn.execute("SELECT name FROM sqlite_master")}
        conn.execute(
            "INSERT OR IGNORE INTO snapshot_numbers (snapshot_id) "
            "SELECT snapshot_id FROM snapshots ORDER BY rowid"
        )
        for (old_rows, old_members, rows, members), (_, _, id_column, columns) in zip(
            FORMAT_1_TABLES, ROW_TABLES.values()
        ):
            if old_rows not in tables:
                continue
            listed = ", ".join(columns)
            conn.execute(
                f"INSERT OR IGNORE INTO {rows} (body_hash, {id_column}, {listed}, body) "
                f"SELECT body_hash, {id_column}, {listed}, body FROM {old_rows}"
            )
            conn.execute(
                f"INSERT INTO {members} (sno, position, rid) "
                "SELECT n.sno, m.position, r.rid FROM {old} m "
                "JOIN snapshot_numbers n ON n.snapshot_id = m.snapshot_id "
                "JOIN {rows} r ON r.body_hash = m.body_hash".format(
                    old=old_members, rows=rows
                )
            )
            conn.execute(f"DROP TABLE {old_members}")
            conn.execute(f"DROP TABLE {old_rows}")
        conn.execute(
            "UPDATE store_meta SET value = ? WHERE key = 'format'", (str(FORMAT),)
        )

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        """One transaction: committed if the block succeeds, rolled back otherwise."""
        try:
            conn = sqlite3.connect(self.path)
        except sqlite3.Error as exc:
            raise StorageError(f"Cannot open {self.path}: {exc}") from exc
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            with conn:
                yield conn
        except sqlite3.DatabaseError as exc:
            raise StorageError(
                f"{self.path} is not a usable knowledge store: {exc}"
            ) from exc
        finally:
            conn.close()

    # --- cards ---------------------------------------------------------------------------

    @arg_digest()
    def save(
        self, card: Any, note: str | None = None, skip_digestion: bool = False
    ) -> str:
        """Store the card's current state; return its pinned reference.

        A new revision is recorded unless that state is already the card's latest.
        """
        with self._session() as conn:
            return self._save(conn, card, note)

    def _save(self, conn: sqlite3.Connection, card: Any, note: str | None) -> str:
        if not card.id:
            raise StorageError("A card without meta.card_id cannot be versioned.")
        stored = card.to_dict()
        sid = snapshot_id(stored)
        known = conn.execute(
            "SELECT 1 FROM snapshots WHERE snapshot_id = ?", (sid,)
        ).fetchone()
        if known is None:
            document = {
                k: v for k, v in stored.items() if k not in (*ROWS, "quantities")
            }
            conn.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (
                    sid,
                    card.id,
                    card.meta.get("entity_type"),
                    card.meta["schema_version"],
                    _pack(canonical_json(document)),
                    _pack(canonical_json(stored["quantities"])),
                ),
            )
            sno = conn.execute(
                "INSERT INTO snapshot_numbers (snapshot_id) VALUES (?)", (sid,)
            ).lastrowid
            times: Dict[str, int] = {}
            for key, (table, members, id_column, columns) in ROW_TABLES.items():
                per_snapshot = key == "source_assertion_store"
                for position, row in enumerate(stored.get(key) or []):
                    # When a statement was read belongs to the snapshot, not the row:
                    # the same statement read again is the same row (#99).
                    kept, tid = row, None
                    if per_snapshot and PER_SNAPSHOT in row:
                        kept = {k: v for k, v in row.items() if k != PER_SNAPSHOT}
                        tid = self._time(conn, json.dumps(row[PER_SNAPSHOT]), times)
                    body = canonical_json(kept)
                    body_hash = digest(body)
                    conn.execute(
                        f"INSERT OR IGNORE INTO {table} "
                        f"(body_hash, {id_column}, {', '.join(columns)}, body) "
                        f"VALUES (?, ?, {', '.join('?' for _ in columns)}, ?)",
                        (body_hash, row.get("id"), *_columns(key, row), _pack(body)),
                    )
                    (rid,) = conn.execute(
                        f"SELECT rid FROM {table} WHERE body_hash = ?", (body_hash,)
                    ).fetchone()
                    if per_snapshot:
                        conn.execute(
                            f"INSERT INTO {members} VALUES (?, ?, ?, ?)",
                            (sno, position, rid, tid),
                        )
                    else:
                        conn.execute(
                            f"INSERT INTO {members} VALUES (?, ?, ?)",
                            (sno, position, rid),
                        )
        head = self._head(conn, card.id)
        if head != sid:
            conn.execute(
                "INSERT INTO revisions (card_id, snapshot_id, stored_at, note) "
                "VALUES (?, ?, ?, ?)",
                (card.id, sid, _now(), note),
            )
        return pinned_ref(card.id, sid)

    @staticmethod
    def _time(conn: sqlite3.Connection, value: str, known: Dict[str, int]) -> int:
        """The number of a retrieval time: a card holds few distinct ones."""
        if value not in known:
            conn.execute(
                "INSERT OR IGNORE INTO retrieval_times (value) VALUES (?)", (value,)
            )
            (known[value],) = conn.execute(
                "SELECT tid FROM retrieval_times WHERE value = ?", (value,)
            ).fetchone()
        return known[value]

    @staticmethod
    def _head(conn: sqlite3.Connection, card_id: str) -> str | None:
        row = conn.execute(
            "SELECT snapshot_id FROM revisions WHERE card_id = ? "
            "ORDER BY revision DESC LIMIT 1",
            (card_id,),
        ).fetchone()
        return None if row is None else row[0]

    def _resolve(self, conn: sqlite3.Connection, ref: str) -> tuple:
        """``(card_id, snapshot_id, item_id)`` of a reference that exists in this store."""
        card_id, sid, item = parse_ref(ref)
        if sid is None:
            sid = self._head(conn, card_id)
            if sid is None:
                raise StorageError(f"No card {card_id} in {self.path}.")
            return card_id, sid, item
        row = conn.execute(
            "SELECT card_id FROM snapshots WHERE snapshot_id = ?", (sid,)
        ).fetchone()
        if row is None or row[0] != card_id:
            raise StorageError(
                f"No snapshot {sid} of {card_id} in {self.path}. A pinned reference "
                "resolves to that exact state or fails; another state of the card is "
                "never returned in its place."
            )
        return card_id, sid, item

    def _assemble(self, conn: sqlite3.Connection, sid: str) -> Dict[str, Any]:
        document, quantities = conn.execute(
            "SELECT document, quantities FROM snapshots WHERE snapshot_id = ?", (sid,)
        ).fetchone()
        data = json.loads(_unpack(document))
        for key, (table, members, _, _) in ROW_TABLES.items():
            if key == "source_assertion_store":
                when, times = (
                    "rt.value",
                    ("LEFT JOIN retrieval_times rt ON rt.tid = m.tid "),
                )
            else:
                when, times = "NULL", ""
            rows = []
            for body, retrieved_at in conn.execute(
                f"SELECT t.body, {when} FROM snapshot_numbers n "
                f"JOIN {members} m ON m.sno = n.sno "
                f"JOIN {table} t ON t.rid = m.rid {times}"
                "WHERE n.snapshot_id = ? ORDER BY m.position",
                (sid,),
            ):
                row = json.loads(_unpack(body))
                if retrieved_at is not None:
                    row[PER_SNAPSHOT] = json.loads(retrieved_at)
                rows.append(row)
            data[key] = rows
        if snapshot_id(data) != sid:
            raise StorageError(
                f"Snapshot {sid} in {self.path} no longer matches its content; the "
                "store was changed outside Sabueso."
            )
        data["quantities"] = json.loads(_unpack(quantities))
        return data

    @arg_digest()
    def load(self, ref: str, skip_digestion: bool = False) -> Any:
        """The card a reference names: the exact state if pinned, else the latest one."""
        from .card import Card

        with self._session() as conn:
            _, sid, item = self._resolve(conn, ref)
            if item:
                raise StorageError(
                    f"{ref!r} names an item, not a card; use source_assertion() or "
                    "relationship()."
                )
            data = self._assemble(conn, sid)
        return Card.from_dict(data)

    def __contains__(self, ref: str) -> bool:
        try:
            with self._session() as conn:
                self._resolve(conn, ref)
        except StorageError:
            return False
        return True

    @arg_digest()
    def history(
        self, card_id: str, skip_digestion: bool = False
    ) -> List[Dict[str, Any]]:
        """Every revision of a card, oldest first, each with its pinned reference."""
        if card_id is None:
            raise StorageError("history() needs the id of a card.")
        with self._session() as conn:
            rows = conn.execute(
                "SELECT r.revision, r.snapshot_id, r.stored_at, r.note, s.schema_version "
                "FROM revisions r JOIN snapshots s ON s.snapshot_id = r.snapshot_id "
                "WHERE r.card_id = ? ORDER BY r.revision",
                (card_id,),
            ).fetchall()
        return [
            {
                "revision": revision,
                "ref": pinned_ref(card_id, sid),
                "snapshot_id": sid,
                "stored_at": stored_at,
                "note": note,
                "schema_version": schema_version,
            }
            for revision, sid, stored_at, note, schema_version in rows
        ]

    # --- knowledge as of a date (#91) --------------------------------------------------

    def _revisions(self, ref: str) -> Tuple[str, List[Dict[str, Any]]]:
        """``(kind, revisions)`` of a card id, a deck or a packet (by name or prefix)."""
        from .packets import PACKET_PREFIX

        if ref.startswith(PACKET_PREFIX) or ref in self.packet_names():
            return "packet", self.packet_history(ref)
        if ref.startswith(DECK_PREFIX) or ref in self.deck_names():
            return "deck", self.deck_history(ref)
        if ref in self.card_ids():
            return "card", self.history(ref)
        raise StorageError(f"{ref} is not a card, deck or packet of this store.")

    @staticmethod
    def _cutoff(when: Any) -> str:
        """The latest ``stored_at`` a revision may have to count as known on ``when``:
        the end of that day for a date, the instant itself for a datetime (UTC)."""
        from datetime import date as _date

        if isinstance(when, datetime):
            moment = when if when.tzinfo else when.replace(tzinfo=timezone.utc)
            return moment.astimezone(timezone.utc).isoformat(timespec="seconds")
        if isinstance(when, _date):
            return f"{when.isoformat()}T23:59:59+00:00"
        raise StorageError(f"{when!r} is not a date or a datetime.")

    @arg_digest()
    def revision_as_of(
        self, ref: str, when: Any, skip_digestion: bool = False
    ) -> Dict[str, Any] | None:
        """The revision of a card, deck or packet that was the latest one stored on
        ``when`` (a date: by the end of that day, UTC), or None when nothing had been
        stored by then."""
        _, revisions = self._revisions(ref)
        cutoff = self._cutoff(when)
        known = [r for r in revisions if r["stored_at"] <= cutoff]
        return known[-1] if known else None

    @arg_digest()
    def as_of(self, ref: str, when: Any, skip_digestion: bool = False) -> Any:
        """What this store knew about a card, deck or packet on ``when``: its latest
        revision stored by then, loaded, or None when nothing had been stored yet.

        Sabueso answers only from what it stored. It never reconstructs a source's
        past state: a revision is the knowledge as it was built and saved.
        """
        kind, _ = self._revisions(ref)
        revision = self.revision_as_of(ref, when)
        if revision is None:
            return None
        if kind == "packet":
            return self.load_packet(revision["ref"])
        if kind == "deck":
            return self.load_deck(revision["ref"])
        return self.load(revision["ref"])

    @arg_digest()
    def changed_since(
        self, ref: str, when: Any, skip_digestion: bool = False
    ) -> Dict[str, Any]:
        """Whether the knowledge of a card or a packet changed after ``when``: its
        revision then and its latest one, compared without retrieval times
        (content-equivalence ids). ``changed`` is None when nothing was stored by then.
        """
        from .packets import card_content_id

        kind, revisions = self._revisions(ref)
        then = self.revision_as_of(ref, when)
        latest = revisions[-1] if revisions else None
        out: Dict[str, Any] = {
            "ref": ref,
            "when": str(when),
            "then": then["ref"] if then else None,
            "latest": latest["ref"] if latest else None,
        }
        if then is None:
            return {**out, "changed": None, "reason": "nothing_stored_by_then"}
        if kind == "deck":
            raise StorageError(
                "changed_since() compares cards and packets; for a deck, compare "
                "its cards."
            )
        if kind == "packet":
            if then["format"] != latest["format"]:
                return {**out, "changed": None, "reason": "format_changed"}
            ids = [then["content_id"], latest["content_id"]]
        else:
            ids = [
                card_content_id(self.load(then["ref"])),
                card_content_id(self.load(latest["ref"])),
            ]
        return {**out, "changed": ids[0] != ids[1], "content_ids": ids}

    def card_ids(self) -> List[str]:
        """Every card in the store."""
        with self._session() as conn:
            return [
                card_id
                for (card_id,) in conn.execute(
                    "SELECT DISTINCT card_id FROM revisions ORDER BY card_id"
                )
            ]

    # --- items of a pinned card ------------------------------------------------------------

    def _item(self, ref: str, key: str) -> Dict[str, Any]:
        """An item of a pinned card, as the verified snapshot holds it (#79).

        The whole snapshot is rebuilt and its content address checked, as ``load``
        does, and the item is taken from that verified state. A row changed outside
        Sabueso therefore fails the read, instead of being returned under the pin.
        """
        with self._session() as conn:
            card_id, sid, item = self._resolve(conn, ref)
            if item is None:
                raise StorageError(f"{ref!r} names a card, not one of its items.")
            data = self._assemble(conn, sid)
        found = [entry for entry in data[key] if entry.get("id") == item]
        if not found:
            raise StorageError(f"Snapshot {sid} of {card_id} holds no {item}.")
        return found[0]

    @arg_digest()
    def source_assertion(
        self, ref: str, skip_digestion: bool = False
    ) -> Dict[str, Any]:
        """The SourceAssertion ``<card_id>@<snapshot_id>#SA_...`` names, as stored."""
        return self._item(ref, "source_assertion_store")

    @arg_digest()
    def relationship(self, ref: str, skip_digestion: bool = False) -> Dict[str, Any]:
        """The relationship ``<card_id>@<snapshot_id>#REL_...`` names, as stored."""
        return self._item(ref, "relationship_store")

    @arg_digest()
    def relationships(
        self,
        object_ref: str | None = None,
        predicate: str | None = None,
        subject_ref: str | None = None,
        all_revisions: bool = False,
        skip_digestion: bool = False,
    ) -> List[Dict[str, Any]]:
        """Relationships across the stored cards, by object, predicate or subject.

        Each result is ``{"card": <pinned ref>, "relationship": {...}}``. The latest
        revision of each card is searched, or every stored state with
        ``all_revisions=True``. References match as written: an entity another card
        knows under another record (``card.entities()``) is not found through it.
        """
        where, args = [], []
        for column, value in (
            ("object_ref", object_ref),
            ("predicate", predicate),
            ("subject_ref", subject_ref),
        ):
            if value is not None:
                where.append(f"t.{column} = ?")
                args.append(value)
        if not where:
            raise StorageError(
                "Name an object_ref, a predicate or a subject_ref to search for."
            )
        states = (
            "SELECT DISTINCT card_id, snapshot_id FROM revisions"
            if all_revisions
            else HEADS
        )
        with self._session() as conn:
            rows = conn.execute(
                f"WITH states AS ({states}) "
                "SELECT s.card_id, s.snapshot_id, t.body FROM states s "
                "JOIN snapshot_numbers n ON n.snapshot_id = s.snapshot_id "
                "JOIN card_rel m ON m.sno = n.sno "
                "JOIN rel_rows t ON t.rid = m.rid "
                f"WHERE {' AND '.join(where)} "
                "ORDER BY s.card_id, s.snapshot_id, m.position",
                args,
            ).fetchall()
            # Every state a result cites is verified first, in the same transaction:
            # a result is a pinned reference, so it must hold what the pin names (#79).
            for sid in sorted({sid for _, sid, _ in rows}):
                self._assemble(conn, sid)
        return [
            {
                "card": pinned_ref(card_id, sid),
                "relationship": json.loads(_unpack(body)),
            }
            for card_id, sid, body in rows
        ]

    # --- decks ---------------------------------------------------------------------------

    @arg_digest()
    def save_deck(
        self,
        deck: Any,
        deck_name: str,
        note: str | None = None,
        skip_digestion: bool = False,
    ) -> str:
        """Store every card of the deck, then the deck: its meta and the pinned state of
        each card. Returns the deck's pinned reference, ``sabueso:deck:<name>@sha256:…``.

        One transaction: a failure stores nothing. Saving a deck again under its name
        adds a revision, unless its content is the latest one; earlier revisions keep
        resolving (#58).

        Disease decks with portable support also store their original input and
        native-assertion revision. The latter may advance the disease's head; both
        pinned revisions remain available.
        """
        name, pinned = self._deck_name(deck_name)
        if pinned:
            raise StorageError("A deck is saved under its name, not under a pin.")
        deck_name = name
        with self._session() as conn:
            from .disease_deck_support import support_cards

            for card in support_cards(deck.meta).values():
                self._save(conn, card, note)
            members = [self._save(conn, card, note) for card in deck.cards]
            sid = deck_snapshot_id(deck.meta, members)
            conn.execute(
                "INSERT OR IGNORE INTO deck_snapshots VALUES (?, ?, ?)",
                (sid, _pack(canonical_json(deck.meta)), _pack(canonical_json(members))),
            )
            if self._deck_head(conn, deck_name) != sid:
                conn.execute(
                    "INSERT INTO deck_revisions (name, snapshot_id, stored_at, note) "
                    "VALUES (?, ?, ?, ?)",
                    (deck_name, sid, _now(), note),
                )
        return pinned_ref(DECK_PREFIX + deck_name, sid)

    @staticmethod
    def _deck_head(conn: sqlite3.Connection, name: str) -> str | None:
        row = conn.execute(
            "SELECT snapshot_id FROM deck_revisions WHERE name = ? "
            "ORDER BY revision DESC LIMIT 1",
            (name,),
        ).fetchone()
        return None if row is None else row[0]

    @staticmethod
    def _deck_name(ref: str) -> Tuple[str, str | None]:
        """``(name, snapshot_id)`` of ``<name>``, ``sabueso:deck:<name>`` or a pin."""
        if not ref.startswith(DECK_PREFIX):
            ref = DECK_PREFIX + ref
        card_id, sid, item = parse_ref(ref)
        name = card_id[len(DECK_PREFIX) :]
        if item or not DECK_NAME.fullmatch(name):
            raise StorageError(f"{ref!r} is not a deck reference.")
        return name, sid

    @arg_digest()
    def load_deck(self, deck_name: str, skip_digestion: bool = False) -> Any:
        """The deck a name or reference names: the exact revision if pinned, else the
        latest. Each card comes back in the exact state it was saved in. An absent pin
        fails; another revision is never returned in its place."""
        from .deck import Deck

        name, sid = self._deck_name(deck_name)
        with self._session() as conn:
            if sid is None:
                sid = self._deck_head(conn, name)
                if sid is None:
                    raise StorageError(f"No deck {name!r} in {self.path}.")
            elif (
                conn.execute(
                    "SELECT 1 FROM deck_revisions WHERE name = ? AND snapshot_id = ?",
                    (name, sid),
                ).fetchone()
                is None
            ):
                raise StorageError(
                    f"No revision {sid} of deck {name!r} in {self.path}. A pinned deck "
                    "resolves to that exact revision or fails."
                )
            meta, members = conn.execute(
                "SELECT meta, members FROM deck_snapshots WHERE snapshot_id = ?", (sid,)
            ).fetchone()
        meta, members = json.loads(_unpack(meta)), json.loads(_unpack(members))
        if deck_snapshot_id(meta, members) != sid:
            raise StorageError(
                f"Deck revision {sid} in {self.path} no longer matches its content."
            )
        return Deck([self.load(ref) for ref in members], meta=meta)

    @arg_digest()
    def deck_history(
        self, deck_name: str, skip_digestion: bool = False
    ) -> List[Dict[str, Any]]:
        """Every revision of a deck, oldest first, each with its pinned reference."""
        name, _ = self._deck_name(deck_name)
        with self._session() as conn:
            rows = conn.execute(
                "SELECT revision, snapshot_id, stored_at, note FROM deck_revisions "
                "WHERE name = ? ORDER BY revision",
                (name,),
            ).fetchall()
        return [
            {
                "revision": revision,
                "ref": pinned_ref(DECK_PREFIX + name, sid),
                "snapshot_id": sid,
                "stored_at": stored_at,
                "note": note,
            }
            for revision, sid, stored_at, note in rows
        ]

    def deck_names(self) -> List[str]:
        with self._session() as conn:
            return [
                name
                for (name,) in conn.execute(
                    "SELECT DISTINCT name FROM deck_revisions ORDER BY name"
                )
            ]

    # --- knowledge packets (#71) ----------------------------------------------------------

    @staticmethod
    def _packet_name(ref: str) -> Tuple[str, str | None]:
        """``(name, snapshot_id)`` of ``<name>``, ``sabueso:packet:<name>`` or a pin."""
        from .packets import PACKET_PREFIX

        if not ref.startswith(PACKET_PREFIX):
            ref = PACKET_PREFIX + ref
        card_id, sid, item = parse_ref(ref)
        name = card_id[len(PACKET_PREFIX) :]
        if item or not DECK_NAME.fullmatch(name):
            raise StorageError(f"{ref!r} is not a packet reference.")
        return name, sid

    @staticmethod
    def _packet_head(conn: sqlite3.Connection, name: str) -> str | None:
        row = conn.execute(
            "SELECT snapshot_id FROM packet_revisions WHERE name = ? "
            "ORDER BY revision DESC LIMIT 1",
            (name,),
        ).fetchone()
        return None if row is None else row[0]

    @arg_digest()
    def save_packet(
        self,
        packet: Any,
        packet_name: str,
        note: str | None = None,
        skip_digestion: bool = False,
    ) -> str:
        """Store a packet under its name; return ``sabueso:packet:<name>@sha256:…``.

        Every card state the packet cites must already be in this store, verified, so
        that the packet reads back whole; otherwise nothing is stored. Saving the latest
        state again adds no revision.
        """
        from .packets import PACKET_PREFIX

        if packet_name is None:
            raise StorageError("A packet is saved under a name.")
        name, pinned = self._packet_name(packet_name)
        if pinned:
            raise StorageError("A packet is saved under its name, not under a pin.")
        document = packet.to_dict()
        sid = packet.snapshot_id()
        with self._session() as conn:
            for entity in document["entities"].values():
                _, card_sid, _ = self._resolve(conn, entity["ref"])
                self._assemble(conn, card_sid)
            conn.execute(
                "INSERT OR IGNORE INTO packet_snapshots VALUES (?, ?, ?)",
                (sid, packet.content_id(), _pack(canonical_json(document))),
            )
            if self._packet_head(conn, name) != sid:
                conn.execute(
                    "INSERT INTO packet_revisions (name, snapshot_id, stored_at, note) "
                    "VALUES (?, ?, ?, ?)",
                    (name, sid, _now(), note),
                )
        ref = pinned_ref(PACKET_PREFIX + name, sid)
        packet.ref = ref
        return ref

    @arg_digest()
    def load_packet(self, packet_name: str, skip_digestion: bool = False) -> Any:
        """The packet a name or reference names: the exact revision if pinned, else the
        latest. Its content and every card state it cites are verified; an absent pin
        fails, and another revision is never returned in its place."""
        from .packets import PACKET_PREFIX, KnowledgePacket

        name, sid = self._packet_name(packet_name)
        with self._session() as conn:
            if sid is None:
                sid = self._packet_head(conn, name)
                if sid is None:
                    raise StorageError(f"No packet {name!r} in {self.path}.")
            elif (
                conn.execute(
                    "SELECT 1 FROM packet_revisions WHERE name = ? AND snapshot_id = ?",
                    (name, sid),
                ).fetchone()
                is None
            ):
                raise StorageError(
                    f"No revision {sid} of packet {name!r} in {self.path}. A pinned "
                    "packet resolves to that exact revision or fails."
                )
            content_id, document = conn.execute(
                "SELECT content_id, document FROM packet_snapshots WHERE snapshot_id = ?",
                (sid,),
            ).fetchone()
            packet = KnowledgePacket(json.loads(_unpack(document)))
            if packet.snapshot_id() != sid or packet.content_id() != content_id:
                raise StorageError(
                    f"Packet revision {sid} in {self.path} no longer matches its "
                    "content; the store was changed outside Sabueso."
                )
            for entity in packet.entities.values():
                _, card_sid, _ = self._resolve(conn, entity["ref"])
                self._assemble(conn, card_sid)
        packet.ref = pinned_ref(PACKET_PREFIX + name, sid)
        return packet

    @arg_digest()
    def packet_history(
        self, packet_name: str, skip_digestion: bool = False
    ) -> List[Dict[str, Any]]:
        """Every revision of a packet, oldest first, each with its pinned reference,
        its format, its content-equivalence id, and whether its knowledge changed from
        the previous revision (``knowledge_changed``: None for the first, and when the
        two are in different formats, aspect mappings or detail levels, whose ids
        cannot be compared)."""
        from .packets import PACKET_PREFIX, _comparison_scope

        name, _ = self._packet_name(packet_name)
        with self._session() as conn:
            rows = conn.execute(
                "SELECT r.revision, r.snapshot_id, r.stored_at, r.note, s.content_id, "
                "s.document FROM packet_revisions r JOIN packet_snapshots s "
                "ON s.snapshot_id = r.snapshot_id WHERE r.name = ? ORDER BY r.revision",
                (name,),
            ).fetchall()
        history, previous = [], None
        for revision, sid, stored_at, note, content_id, document in rows:
            data = json.loads(_unpack(document))
            packet_format = data.get("format")
            scope = _comparison_scope(data)
            comparable = previous is not None and previous[1] == scope
            history.append(
                {
                    "revision": revision,
                    "ref": pinned_ref(PACKET_PREFIX + name, sid),
                    "snapshot_id": sid,
                    "format": packet_format,
                    "content_id": content_id,
                    "knowledge_changed": content_id != previous[0]
                    if comparable
                    else None,
                    "stored_at": stored_at,
                    "note": note,
                }
            )
            previous = (content_id, scope)
        return history

    def packet_names(self) -> List[str]:
        with self._session() as conn:
            return [
                name
                for (name,) in conn.execute(
                    "SELECT DISTINCT name FROM packet_revisions ORDER BY name"
                )
            ]

    # --- migration -----------------------------------------------------------------------

    @arg_digest()
    def import_card_table(
        self,
        path: str | os.PathLike,
        table: str = "cards",
        skip_digestion: bool = False,
    ) -> List[str]:
        """Import every row of a ``save_card_sqlite`` table, oldest first, as revisions.

        Each row is verified as ``load_card_sqlite`` would. Rows of the same card become
        its history; a row equal to the previous state adds nothing. One transaction.
        """
        from .card import Card

        source = Path(path)
        if not source.is_file():
            raise StorageError(f"No SQLite file {source}.")
        with closing(sqlite3.connect(source)) as legacy:
            try:
                rows = legacy.execute(
                    f"SELECT id, card_json FROM {table} ORDER BY id"
                ).fetchall()
            except sqlite3.Error as exc:
                raise StorageError(
                    f"{source} has no card table {table!r}: {exc}"
                ) from exc
        with self._session() as conn:
            return [
                self._save(
                    conn,
                    Card.from_dict(json.loads(card_json)),
                    f"imported from {source.name}, table {table}, row {row_id}",
                )
                for row_id, card_json in rows
            ]
