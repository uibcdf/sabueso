"""Deck core implementation.

A deck can say why each card is in it and which candidates were left out (#58):

- ``meta["membership"]``: ``{card_id: basis}``, filled by the tools that build decks and
  by ``add(card, basis=...)``;
- ``meta["excluded"]``: ``[{candidate, reason, by?}]``, filled by ``exclude()``;
- ``meta["operations"]``: the operations that derived the deck from another one, in
  order. An operation whose parameters cannot be recorded (a Python predicate) says so,
  ``"reproducible": False``.
"""

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

    def add(self, card: Any, basis: Dict[str, Any] | None = None) -> None:
        """Add a card; ``basis`` records why it belongs (a query, a rule, a curator)."""
        self.cards.append(card)
        if basis is not None:
            self.meta.setdefault("membership", {})[card.id] = basis

    def basis(self, card_id: str) -> Dict[str, Any] | None:
        """Why a card is in the deck, when that was recorded."""
        return (self.meta.get("membership") or {}).get(card_id)

    def exclude(self, candidate: str, reason: str, by: str | None = None) -> None:
        """Leave a candidate out, with the reason. The card is removed if present."""
        if not reason:
            from .errors import SchemaError

            raise SchemaError("An exclusion needs its reason.")
        self.cards = [c for c in self.cards if c.id != candidate]
        (self.meta.get("membership") or {}).pop(candidate, None)
        record = {"candidate": candidate, "reason": reason}
        if by:
            record["by"] = by
        self.meta.setdefault("excluded", []).append(record)

    def _derived(
        self,
        cards: List[Any],
        operation: str,
        parameters: Dict[str, Any] | None = None,
        reproducible: bool = True,
        **extra: Any,
    ) -> "Deck":
        """A deck derived from this one: membership kept for the cards it holds, and
        the operation appended to ``meta["operations"]``."""
        meta = {k: v for k, v in self.meta.items() if k != "membership"}
        membership = self.meta.get("membership") or {}
        kept = {c.id: membership[c.id] for c in cards if c.id in membership}
        if kept:
            meta["membership"] = kept
        step: Dict[str, Any] = {"operation": operation, "parameters": parameters or {}}
        if not reproducible:
            step["reproducible"] = False
        meta["operations"] = [*self.meta.get("operations", []), step]
        meta.update(extra)
        return Deck(list(cards), meta=meta)

    def snapshot_id(self) -> str:
        """Content address of the deck: its meta and the pinned state of each card."""
        from .snapshot import deck_snapshot_id

        return deck_snapshot_id(self.meta, [c.pinned_ref() for c in self.cards])

    def extend(self, cards: List[Any]) -> None:
        self.cards.extend(cards)

    def filter(self, predicate: Callable[[Any], bool]) -> "Deck":
        """Cards for which ``predicate`` is true. A Python predicate cannot be recorded,
        so the operation is marked as not reproducible from the deck alone."""
        return self._derived(
            [c for c in self.cards if predicate(c)],
            "filter",
            {"predicate": getattr(predicate, "__name__", "custom")},
            reproducible=False,
        )

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
        return self._derived(ordered, "sort", {"key": key, "reverse": reverse})

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
        extra = {"lineage_not_stated": unknown} if unknown else {}
        return self._derived(kept, "in_lineage", {"taxon": taxon}, **extra)

    def group_by(self, key: str) -> Dict[Any, "Deck"]:
        """Decks of the cards that share the resolved value at field path ``key``, e.g.
        ``"annotations.organism"`` or ``"annotations.taxon_id"``. Cards without a value
        are grouped under None."""
        members: Dict[Any, List[Any]] = {}
        for card in self.cards:
            node = card.get(key)
            value = node.get("value") if isinstance(node, dict) else node
            if isinstance(value, list):
                value = tuple(value)
            members.setdefault(value, []).append(card)
        return {
            value: self._derived(
                cards,
                "group_by",
                {
                    "key": key,
                    "value": list(value) if isinstance(value, tuple) else value,
                },
            )
            for value, cards in members.items()
        }

    def group_by_rank(self, rank: str) -> Dict[Any, "Deck"]:
        """Decks of the cards whose organism falls in the same taxon of ``rank`` (e.g.
        ``"genus"``, ``"family"``), from NCBI Taxonomy (``annotations.taxonomy``, #67).
        Cards without that information, or without a taxon of that rank, are grouped
        under None."""
        wanted = rank.lower()
        members: Dict[Any, List[Any]] = {}
        for card in self.cards:
            node = card.get("annotations.taxonomy")
            taxonomy = node.get("value") if isinstance(node, dict) else None
            key = None
            if taxonomy:
                chain = [*taxonomy.get("ancestors", []), taxonomy]
                key = next(
                    (t.get("name") for t in chain if (t.get("rank") or "") == wanted),
                    None,
                )
            members.setdefault(key, []).append(card)
        return {
            key: self._derived(cards, "group_by_rank", {"rank": wanted, "value": key})
            for key, cards in members.items()
        }

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
        return self._derived(
            [c for c in self.cards if c.id in wanted],
            "intersect",
            {"other": sorted(wanted)},
        )

    def difference(self, other: "Deck") -> "Deck":
        """Cards of this deck whose id is not in ``other``."""
        unwanted = set(other.ids())
        return self._derived(
            [c for c in self.cards if c.id not in unwanted],
            "difference",
            {"other": sorted(unwanted)},
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
