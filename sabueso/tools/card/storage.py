"""Persistence helpers for Card objects."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


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
    card_id = None
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


def load_card_json(path: str | Path) -> Any:
    """Load a single Card from JSON (dict)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def load_card_sqlite(path: str | Path, table: str = "cards", card_id: str | None = None) -> Any:
    """Load a single Card JSON from SQLite (latest row by default)."""
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
