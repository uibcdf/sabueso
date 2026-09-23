"""Persistence helpers for Deck objects.

A deck is its cards plus its ``meta``: the traces that make it interpretable, such as a
resolution decision (``ambiguity_deck``) or per-source outcomes and unanchored records
(``ligand_deck``). Both are persisted (uibcdf/sabueso#26):

- JSONL: the first line is a header ``{"sabueso_deck": {"format": 1, "meta": {...}}}``,
  followed by one card per line. Files without a header still load, with empty meta.
- SQLite: the cards of a deck fill one table, and its meta is a row of ``deck_meta``
  keyed by that table. Saving a deck into a table replaces what the table held, so the
  table and its meta always describe the same deck.

``load_deck_*`` return the card payloads; ``read_deck_*`` return ``(meta, payloads)``.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECK_HEADER = "sabueso_deck"
DECK_FORMAT = 1
META_TABLE = "deck_meta"
TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _unwrap_value(node: Any) -> Any:
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def _table(name: str) -> str:
    if not TABLE_NAME.match(name or "") or name == META_TABLE:
        raise ValueError(f"Invalid deck table name: {name!r}")
    return name


def save_deck_jsonl(deck: Any, path: str | Path) -> None:
    """Save a Deck to JSONL: a header line with the deck meta, then one card per line."""
    out = Path(path)
    header = {DECK_HEADER: {"format": DECK_FORMAT, "meta": getattr(deck, "meta", {})}}
    with out.open("w", encoding="utf-8") as f:
        f.write(json.dumps(header))
        f.write("\n")
        for card in deck.cards:
            f.write(json.dumps(card.to_dict()))
            f.write("\n")


def read_deck_jsonl(path: str | Path) -> Tuple[Dict[str, Any], List[dict]]:
    """``(meta, card payloads)`` from a JSONL deck; meta is empty without a header."""
    meta: Dict[str, Any] = {}
    cards: List[dict] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if not cards and not meta and set(data) == {DECK_HEADER}:
                meta = data[DECK_HEADER].get("meta") or {}
                continue
            cards.append(data)
    return meta, cards


def load_deck_jsonl(path: str | Path) -> List[dict]:
    """Load the card payloads of a JSONL deck."""
    return read_deck_jsonl(path)[1]


def save_deck_sqlite(
    deck: Any,
    path: str | Path,
    table: str = "cards",
    id_field: str | None = None,
) -> None:
    """Save a Deck into a SQLite table (one row per card) and its meta into ``deck_meta``.

    The table's previous rows are replaced: a table holds one deck.
    """
    table = _table(table)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(out) as conn:
        cur = conn.cursor()
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "card_id TEXT, "
            "card_json TEXT NOT NULL)"
        )
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {META_TABLE} ("
            "deck_table TEXT PRIMARY KEY, "
            "format INTEGER NOT NULL, "
            "meta_json TEXT NOT NULL)"
        )
        cur.execute(f"DELETE FROM {table}")
        for card in deck.cards:
            card_json = json.dumps(card.to_dict())
            card_id = card.meta.get("card_id")
            if id_field:
                node = card.get(id_field)
                card_id = _unwrap_value(node)
            cur.execute(
                f"INSERT INTO {table} (card_id, card_json) VALUES (?, ?)",
                (card_id, card_json),
            )
        cur.execute(
            f"INSERT OR REPLACE INTO {META_TABLE} (deck_table, format, meta_json) "
            "VALUES (?, ?, ?)",
            (table, DECK_FORMAT, json.dumps(getattr(deck, "meta", {}))),
        )
        conn.commit()


def read_deck_sqlite(
    path: str | Path, table: str = "cards"
) -> Tuple[Dict[str, Any], List[dict]]:
    """``(meta, card payloads)`` of the deck stored in ``table``."""
    table = _table(table)
    with sqlite3.connect(Path(path)) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT card_json FROM {table} ORDER BY id ASC")
        cards = [json.loads(r[0]) for r in cur.fetchall()]
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (META_TABLE,),
        )
        meta: Dict[str, Any] = {}
        if cur.fetchone():
            cur.execute(
                f"SELECT meta_json FROM {META_TABLE} WHERE deck_table=?", (table,)
            )
            row = cur.fetchone()
            meta = json.loads(row[0]) if row else {}
    return meta, cards


def load_deck_sqlite(path: str | Path, table: str = "cards") -> List[dict]:
    """Load the card payloads of the deck stored in ``table``."""
    return read_deck_sqlite(path, table)[1]
