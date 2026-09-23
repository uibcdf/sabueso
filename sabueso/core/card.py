"""Card core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from .relationship_store import Relationship, RelationshipStore
from .source_assertion_store import SourceAssertionStore

CARD_SCHEMA_VERSION = "0.2.0"


def make_card_id(entity_type: str, subject_ref: str) -> str:
    """Stable, location-independent card reference, e.g. ``sabueso:protein:uniprot:P52789``.

    The syntax is provisional: MOLI Architecture 1.0 freezes stable referencability,
    not the identifier format.
    """
    return f"sabueso:{entity_type or 'entity'}:{subject_ref}"


class Card:
    """Resolved knowledge about a single entity, linked to its SourceAssertions."""

    def __init__(
        self,
        meta: Dict[str, Any] | None = None,
        sections: Dict[str, Any] | None = None,
        source_assertion_store: SourceAssertionStore
        | List[Dict[str, Any]]
        | None = None,
        selection_rules: Dict[str, Any] | None = None,
        quality: Dict[str, Any] | None = None,
        relationship_store: RelationshipStore | List[Dict[str, Any]] | None = None,
    ) -> None:
        self.meta = meta or {}
        self.sections = sections or {}
        if not isinstance(source_assertion_store, SourceAssertionStore):
            source_assertion_store = SourceAssertionStore(source_assertion_store)
        self.source_assertion_store = source_assertion_store
        if not isinstance(relationship_store, RelationshipStore):
            relationship_store = RelationshipStore(relationship_store)
        self.relationship_store = relationship_store
        self.selection_rules = selection_rules or {}
        self.quality = quality or {}

    @property
    def id(self) -> str | None:
        """Stable card reference (``meta.card_id``), independent of storage location."""
        return self.meta.get("card_id")

    def relationships(
        self, predicate: str | None = None, object_ref: str | None = None
    ) -> List[Relationship]:
        """Relationships carried by this card, optionally filtered."""
        return self.relationship_store.find(predicate=predicate, object_ref=object_ref)

    def get(self, field_path: str) -> Any:
        cur = self.sections
        for key in field_path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return None
            cur = cur[key]
        return cur

    def set(self, field_path: str, value: Any, source_assertion_ids: List[str]) -> None:
        cur = self.sections
        parts = field_path.split(".")
        for key in parts[:-1]:
            if key not in cur or not isinstance(cur[key], dict):
                cur[key] = {}
            cur = cur[key]
        cur[parts[-1]] = {"value": value, "source_assertion_ids": source_assertion_ids}

    def extract(self, field_paths: List[str]) -> Dict[str, Any]:
        return {fp: self.get(fp) for fp in field_paths}

    def list_fields(self) -> List[str]:
        out: List[str] = []

        def walk(prefix: str, obj: Any) -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    path = f"{prefix}.{k}" if prefix else k
                    out.append(path)
                    walk(path, v)

        walk("", self.sections)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta,
            "sections": self.sections,
            "source_assertion_store": self.source_assertion_store.to_list(),
            "relationship_store": self.relationship_store.to_list(),
            "selection_rules": self.selection_rules,
            "quality": self.quality,
        }

    def to_json(self, path: str) -> None:
        from sabueso.tools.card.storage import save_card_json

        save_card_json(self, path)

    def to_sqlite(
        self, path: str, table: str = "cards", id_field: str | None = None
    ) -> None:
        from sabueso.tools.card.storage import save_card_sqlite

        save_card_sqlite(self, path, table=table, id_field=id_field)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Card":
        """Rebuild a Card, including its SourceAssertionStore, from ``to_dict()`` output."""
        return cls(**data)

    @classmethod
    def from_json(cls, path: str) -> "Card":
        from sabueso.tools.card.storage import load_card_json

        return cls.from_dict(load_card_json(path))

    @classmethod
    def from_sqlite(
        cls, path: str, table: str = "cards", card_id: str | None = None
    ) -> "Card | None":
        from sabueso.tools.card.storage import load_card_sqlite

        data = load_card_sqlite(path, table=table, card_id=card_id)
        if data is None:
            return None
        return cls.from_dict(data)

    def to_deck(self) -> Any:
        from .deck import Deck

        return Deck([self])

    def compare(self, other: "Card", fields: List[str] | None = None) -> Dict[str, Any]:
        fields = fields or []
        diffs: Dict[str, Any] = {}
        for fp in fields:
            diffs[fp] = {"self": self.get(fp), "other": other.get(fp)}
        return diffs

    def expand(self, kind: str) -> Any:
        # Placeholder: actual expansion will be implemented in ops/tools.
        from .deck import Deck

        return Deck([])
