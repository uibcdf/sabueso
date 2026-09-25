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
- **Every read verifies.** A snapshot is rebuilt from its rows, hashed again and
  checked against its id; then ``Card.from_dict`` checks its schema version and its
  quantities seal. A store changed outside Sabueso is refused with ``StorageError``.

The file states its format (``store_meta``, format 1). Its tables are Sabueso's
implementation, not a contract: other MOLI components reference cards through the
reference forms (uibcdf/moli#3), not by reading these tables.
"""

from __future__ import annotations

import json
import os
import sqlite3
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

FORMAT = 1
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
CREATE TABLE IF NOT EXISTS source_assertions (
    body_hash TEXT PRIMARY KEY,
    sa_id TEXT NOT NULL,
    subject_ref TEXT,
    field_path TEXT,
    source_name TEXT,
    source_version TEXT,
    body TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS source_assertions_by_id ON source_assertions (sa_id);
CREATE INDEX IF NOT EXISTS source_assertions_by_subject
    ON source_assertions (subject_ref, field_path);
CREATE TABLE IF NOT EXISTS snapshot_source_assertions (
    snapshot_id TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    position INTEGER NOT NULL,
    body_hash TEXT NOT NULL REFERENCES source_assertions (body_hash),
    PRIMARY KEY (snapshot_id, position)
);
CREATE INDEX IF NOT EXISTS snapshot_source_assertions_by_row
    ON snapshot_source_assertions (body_hash);
CREATE TABLE IF NOT EXISTS relationships (
    body_hash TEXT PRIMARY KEY,
    rel_id TEXT NOT NULL,
    subject_ref TEXT,
    predicate TEXT,
    object_ref TEXT,
    body TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS relationships_by_id ON relationships (rel_id);
CREATE INDEX IF NOT EXISTS relationships_by_object ON relationships (object_ref, predicate);
CREATE INDEX IF NOT EXISTS relationships_by_subject
    ON relationships (subject_ref, predicate);
CREATE TABLE IF NOT EXISTS snapshot_relationships (
    snapshot_id TEXT NOT NULL REFERENCES snapshots (snapshot_id),
    position INTEGER NOT NULL,
    body_hash TEXT NOT NULL REFERENCES relationships (body_hash),
    PRIMARY KEY (snapshot_id, position)
);
CREATE INDEX IF NOT EXISTS snapshot_relationships_by_row
    ON snapshot_relationships (body_hash);
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
        "source_assertions",
        "snapshot_source_assertions",
        "sa_id",
        ("subject_ref", "field_path", "source_name", "source_version"),
    ),
    "relationship_store": (
        "relationships",
        "snapshot_relationships",
        "rel_id",
        ("subject_ref", "predicate", "object_ref"),
    ),
}


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
            elif row[0] != str(FORMAT):
                raise StorageError(
                    f"{self.path} is a knowledge store of format {row[0]}; this Sabueso "
                    f"reads format {FORMAT}."
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
                    canonical_json(document),
                    canonical_json(stored["quantities"]),
                ),
            )
            for key, (table, members, id_column, columns) in ROW_TABLES.items():
                for position, row in enumerate(stored.get(key) or []):
                    body = canonical_json(row)
                    body_hash = digest(body)
                    conn.execute(
                        f"INSERT OR IGNORE INTO {table} "
                        f"(body_hash, {id_column}, {', '.join(columns)}, body) "
                        f"VALUES (?, ?, {', '.join('?' for _ in columns)}, ?)",
                        (body_hash, row.get("id"), *_columns(key, row), body),
                    )
                    conn.execute(
                        f"INSERT INTO {members} VALUES (?, ?, ?)",
                        (sid, position, body_hash),
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
        data = json.loads(document)
        for key, (table, members, _, _) in ROW_TABLES.items():
            data[key] = [
                json.loads(body)
                for (body,) in conn.execute(
                    f"SELECT t.body FROM {members} m JOIN {table} t "
                    "ON t.body_hash = m.body_hash WHERE m.snapshot_id = ? "
                    "ORDER BY m.position",
                    (sid,),
                )
            ]
        if snapshot_id(data) != sid:
            raise StorageError(
                f"Snapshot {sid} in {self.path} no longer matches its content; the "
                "store was changed outside Sabueso."
            )
        data["quantities"] = json.loads(quantities)
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
        table, members, id_column, _ = ROW_TABLES[key]
        with self._session() as conn:
            card_id, sid, item = self._resolve(conn, ref)
            if item is None:
                raise StorageError(f"{ref!r} names a card, not one of its items.")
            row = conn.execute(
                f"SELECT t.body FROM {members} m JOIN {table} t "
                f"ON t.body_hash = m.body_hash WHERE m.snapshot_id = ? AND t.{id_column} = ?",
                (sid, item),
            ).fetchone()
        if row is None:
            raise StorageError(f"Snapshot {sid} of {card_id} holds no {item}.")
        return json.loads(row[0])

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
                "JOIN snapshot_relationships m ON m.snapshot_id = s.snapshot_id "
                "JOIN relationships t ON t.body_hash = m.body_hash "
                f"WHERE {' AND '.join(where)} "
                "ORDER BY s.card_id, s.snapshot_id, m.position",
                args,
            ).fetchall()
        return [
            {"card": pinned_ref(card_id, sid), "relationship": json.loads(body)}
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
        """
        name, pinned = self._deck_name(deck_name)
        if pinned:
            raise StorageError("A deck is saved under its name, not under a pin.")
        deck_name = name
        with self._session() as conn:
            members = [self._save(conn, card, note) for card in deck.cards]
            sid = deck_snapshot_id(deck.meta, members)
            conn.execute(
                "INSERT OR IGNORE INTO deck_snapshots VALUES (?, ?, ?)",
                (sid, canonical_json(deck.meta), canonical_json(members)),
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
        meta, members = json.loads(meta), json.loads(members)
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
