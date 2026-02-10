"""Card core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List


class Card:
    """Single entity representation with evidence links."""

    def __init__(
        self,
        meta: Dict[str, Any] | None = None,
        sections: Dict[str, Any] | None = None,
        evidence_store: Any | None = None,
        selection_rules: Dict[str, Any] | None = None,
        quality: Dict[str, Any] | None = None,
    ) -> None:
        self.meta = meta or {}
        self.sections = sections or {}
        self.evidence_store = evidence_store
        self.selection_rules = selection_rules or {}
        self.quality = quality or {}

    def get(self, field_path: str) -> Any:
        cur = self.sections
        for key in field_path.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return None
            cur = cur[key]
        return cur

    def set(self, field_path: str, value: Any, evidence_ids: List[str]) -> None:
        cur = self.sections
        parts = field_path.split(".")
        for key in parts[:-1]:
            if key not in cur or not isinstance(cur[key], dict):
                cur[key] = {}
            cur = cur[key]
        cur[parts[-1]] = {"value": value, "evidence_ids": evidence_ids}

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
            "selection_rules": self.selection_rules,
            "quality": self.quality,
        }

    def to_json(self, path: str) -> None:
        from sabueso.tools.card.storage import save_card_json

        save_card_json(self, path)

    def to_sqlite(self, path: str, table: str = "cards", id_field: str | None = None) -> None:
        from sabueso.tools.card.storage import save_card_sqlite

        save_card_sqlite(self, path, table=table, id_field=id_field)

    @classmethod
    def from_json(cls, path: str) -> "Card":
        from sabueso.tools.card.storage import load_card_json

        data = load_card_json(path)
        return cls(**data)

    @classmethod
    def from_sqlite(cls, path: str, table: str = "cards", card_id: str | None = None) -> "Card | None":
        from sabueso.tools.card.storage import load_card_sqlite

        data = load_card_sqlite(path, table=table, card_id=card_id)
        if data is None:
            return None
        return cls(**data)

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
