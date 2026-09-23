"""Deck core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List


class Deck:
    """Collection of Cards with consistent operations."""

    def __init__(
        self, cards: List[Any] | None = None, meta: Dict[str, Any] | None = None
    ) -> None:
        self.cards = cards or []
        self.meta = meta or {}

    def add(self, card: Any) -> None:
        self.cards.append(card)

    def extend(self, cards: List[Any]) -> None:
        self.cards.extend(cards)

    def filter(self, predicate: Callable[[Any], bool]) -> "Deck":
        return Deck([c for c in self.cards if predicate(c)], meta=self.meta.copy())

    def sort(self, key: str, reverse: bool = False) -> "Deck":
        """Sort cards by the resolved value at field path ``key``.

        Cards without a value for ``key`` keep their relative order and go last.
        """

        def value(card: Any) -> Any:
            node = card.get(key)
            if isinstance(node, dict) and "value" in node:
                return node["value"]
            return node

        present = [c for c in self.cards if value(c) is not None]
        missing = [c for c in self.cards if value(c) is None]
        ordered = sorted(present, key=value, reverse=reverse) + missing
        return Deck(ordered, meta=self.meta.copy())

    def map(self, fn: Callable[[Any], Any]) -> List[Any]:
        return [fn(c) for c in self.cards]

    def compare(self, other: "Deck", key_fields: List[str]) -> Dict[str, Any]:
        return {
            "self": self.map(lambda c: c.extract(key_fields)),
            "other": other.map(lambda c: c.extract(key_fields)),
        }

    def summarize(self, fields: List[str]) -> List[Dict[str, Any]]:
        return [c.extract(fields) for c in self.cards]

    def to_list(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.cards]

    def to_jsonl(self, path: str) -> None:
        from sabueso.tools.deck.storage import save_deck_jsonl

        save_deck_jsonl(self, path)

    def to_sqlite(
        self, path: str, table: str = "cards", id_field: str | None = None
    ) -> None:
        from sabueso.tools.deck.storage import save_deck_sqlite

        save_deck_sqlite(self, path, table=table, id_field=id_field)

    @classmethod
    def from_jsonl(cls, path: str) -> "Deck":
        from sabueso.tools.deck.storage import load_deck_jsonl

        from .card import Card

        return cls([Card.from_dict(data) for data in load_deck_jsonl(path)])

    @classmethod
    def from_sqlite(cls, path: str, table: str = "cards") -> "Deck":
        from sabueso.tools.deck.storage import load_deck_sqlite

        from .card import Card

        return cls(
            [Card.from_dict(data) for data in load_deck_sqlite(path, table=table)]
        )
