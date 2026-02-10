"""Persistence helpers for Deck objects."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def _unwrap_value(node: Any) -> Any:
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def save_deck_jsonl(deck: Any, path: str | Path) -> None:
    """Save a Deck to JSONL (one card per line)."""
    out = Path(path)
    with out.open("w", encoding="utf-8") as f:
        for card in deck.cards:
            f.write(json.dumps(card.to_dict()))
            f.write("\n")


def save_deck_sqlite(
    deck: Any,
    path: str | Path,
    table: str = "cards",
    id_field: str | None = None,
) -> None:
    """Save a Deck into a SQLite table as JSON (one row per card)."""
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
        for card in deck.cards:
            card_json = json.dumps(card.to_dict())
            card_id = None
            if id_field:
                node = card.get(id_field)
                card_id = _unwrap_value(node)
            cur.execute(
                f"INSERT INTO {table} (card_id, card_json) VALUES (?, ?)",
                (card_id, card_json),
            )
        conn.commit()
