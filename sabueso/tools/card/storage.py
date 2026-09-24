"""Persistence helpers for Card objects."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict


def _unwrap_value(node: Any) -> Any:
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def save_card_json(card: Any, path: str | Path) -> None:
    """Save a single Card to JSON."""
    out = Path(path)
    out.write_text(json.dumps(card.to_dict(), indent=2), encoding="utf-8")


def save_card_sqlite(
    card: Any,
    path: str | Path,
    table: str = "cards",
    id_field: str | None = None,
) -> None:
    """Save a single Card into a SQLite table as JSON."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    card_json = json.dumps(card.to_dict())
    card_id = card.meta.get("card_id")
    if id_field:
        node = card.get(id_field)
        card_id = _unwrap_value(node)

    with sqlite3.connect(out) as conn:
        cur = conn.cursor()
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "card_id TEXT, "
            "card_json TEXT NOT NULL)"
        )
        cur.execute(
            f"INSERT INTO {table} (card_id, card_json) VALUES (?, ?)",
            (card_id, card_json),
        )
        conn.commit()


def _read_card_json(path: str | Path) -> Dict[str, Any]:
    """The stored payload, unverified. Only ``Card.from_dict`` may consume it."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_card_json(path: str | Path) -> Any:
    """Load a Card from JSON. Its quantities seal is verified (#32); a card changed
    outside Sabueso is refused with StorageError."""
    from sabueso.core.card import Card

    return Card.from_dict(_read_card_json(path))


def load_card_sqlite(
    path: str | Path, table: str = "cards", card_id: str | None = None
) -> Any:
    """Load a Card from SQLite (latest row by default), verified as ``load_card_json``."""
    from sabueso.core.card import Card

    data = _read_card_sqlite(path, table=table, card_id=card_id)
    return None if data is None else Card.from_dict(data)


def _read_card_sqlite(
    path: str | Path, table: str = "cards", card_id: str | None = None
) -> Dict[str, Any] | None:
    """The stored payload, unverified. Only ``Card.from_dict`` may consume it."""
    out = Path(path)
    with sqlite3.connect(out) as conn:
        cur = conn.cursor()
        if card_id is None:
            cur.execute(f"SELECT card_json FROM {table} ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
        else:
            cur.execute(
                f"SELECT card_json FROM {table} WHERE card_id = ? ORDER BY id DESC LIMIT 1",
                (card_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])
