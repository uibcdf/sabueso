"""Deck core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from sabueso._private.argdigest import arg_digest


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

    def in_lineage(self, taxon: str) -> "Deck":
        """Cards whose organism is ``taxon`` or descends from it (#54).

        ``taxon`` is a name as UniProt states lineages (``"Trypanosomatida"``,
        ``"Metazoa"``). Cards whose lineage is not stated are left out, and listed in
        the new deck's ``meta["lineage_not_stated"]``: not stated is not "outside".
        """

        def value(card: Any, path: str) -> Any:
            node = card.get(path)
            return node.get("value") if isinstance(node, dict) else node

        kept, unknown = [], []
        for card in self.cards:
            lineage = value(card, "annotations.lineage")
            if lineage is None:
                unknown.append(card.id)
            elif taxon in lineage or value(card, "annotations.organism") == taxon:
                kept.append(card)
        meta = {**self.meta, "lineage_filter": taxon}
        if unknown:
            meta["lineage_not_stated"] = unknown
        return Deck(kept, meta=meta)

    def group_by(self, key: str) -> Dict[Any, "Deck"]:
        """Decks of the cards that share the resolved value at field path ``key``, e.g.
        ``"annotations.organism"`` or ``"annotations.taxon_id"``. Cards without a value
        are grouped under None."""
        groups: Dict[Any, Deck] = {}
        for card in self.cards:
            node = card.get(key)
            value = node.get("value") if isinstance(node, dict) else node
            if isinstance(value, list):
                value = tuple(value)
            groups.setdefault(value, Deck(meta={**self.meta, "group": {key: value}}))
            groups[value].add(card)
        return groups

    def identity_audit(self) -> Dict[str, Any]:
        """Redundant entries, strain variants and paralogs among the deck's protein
        cards (rule ``protein_identity_audit@1``, #55). Nothing is merged: each finding
        states its basis, and ``possibly_same_as`` is a flag for review."""
        from .identity_audit import audit, basis_of_card, derivation

        proteins = [c for c in self.cards if c.meta.get("entity_type") == "protein"]
        return {
            "findings": audit(basis_of_card(c) for c in proteins),
            "derivation": derivation(),
        }

    def ids(self) -> List[str]:
        return [c.id for c in self.cards]

    def intersect(self, other: "Deck") -> "Deck":
        """Cards of this deck whose id is also in ``other`` (same entity, same anchor)."""
        wanted = set(other.ids())
        return Deck([c for c in self.cards if c.id in wanted], meta=self.meta.copy())

    def difference(self, other: "Deck") -> "Deck":
        """Cards of this deck whose id is not in ``other``."""
        unwanted = set(other.ids())
        return Deck(
            [c for c in self.cards if c.id not in unwanted], meta=self.meta.copy()
        )

    def map(self, fn: Callable[[Any], Any]) -> List[Any]:
        return [fn(c) for c in self.cards]

    def compare(self, other: "Deck", key_fields: List[str]) -> Dict[str, Any]:
        """Each deck's cards reduced to ``key_fields`` (digested by ``Card.extract``)."""
        return {
            "self": self.map(lambda c: c.extract(key_fields)),
            "other": other.map(lambda c: c.extract(key_fields)),
        }

    @arg_digest()
    def summarize(
        self, fields: List[str], skip_digestion: bool = False
    ) -> List[Dict[str, Any]]:
        return [c.extract(fields, skip_digestion=True) for c in self.cards]

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
        from sabueso.tools.deck.storage import _read_deck_jsonl

        from .card import Card

        meta, cards = _read_deck_jsonl(path)
        return cls([Card.from_dict(data) for data in cards], meta=meta)

    @classmethod
    def from_sqlite(cls, path: str, table: str = "cards") -> "Deck":
        from sabueso.tools.deck.storage import _read_deck_sqlite

        from .card import Card

        meta, cards = _read_deck_sqlite(path, table=table)
        return cls([Card.from_dict(data) for data in cards], meta=meta)
