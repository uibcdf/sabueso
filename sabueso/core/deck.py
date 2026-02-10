"""Deck core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class Deck:
    """Collection of Cards with consistent operations."""

    def __init__(self, cards: List[Any] | None = None, meta: Dict[str, Any] | None = None) -> None:
        self.cards = cards or []
        self.meta = meta or {}

    def add(self, card: Any) -> None:
        self.cards.append(card)

    def extend(self, cards: List[Any]) -> None:
        self.cards.extend(cards)

    def filter(self, predicate: Callable[[Any], bool]) -> "Deck":
        return Deck([c for c in self.cards if predicate(c)], meta=self.meta.copy())

    def sort(self, key: str) -> "Deck":
        return Deck(sorted(self.cards, key=lambda c: c.get(key)), meta=self.meta.copy())

    def map(self, fn: Callable[[Any], Any]) -> List[Any]:
        return [fn(c) for c in self.cards]

    def compare(self, other: "Deck", key_fields: List[str]) -> Dict[str, Any]:
        return {"self": self.map(lambda c: c.extract(key_fields)), "other": other.map(lambda c: c.extract(key_fields))}

    def summarize(self, fields: List[str]) -> List[Dict[str, Any]]:
        return [c.extract(fields) for c in self.cards]

    def to_list(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.cards]

    def to_jsonl(self, path: str) -> None:
        from sabueso.tools.deck.storage import save_deck_jsonl

        save_deck_jsonl(self, path)

    def to_sqlite(self, path: str, table: str = "cards", id_field: str | None = None) -> None:
        from sabueso.tools.deck.storage import save_deck_sqlite

        save_deck_sqlite(self, path, table=table, id_field=id_field)
