"""Card core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso._private.argdigest import arg_digest

from .quantities import field_node, quantity_columns, seal, to_quantity, verify
from .relationship_store import Relationship, RelationshipStore
from .source_assertion_store import SourceAssertionStore

CARD_SCHEMA_VERSION = "0.3.0"


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

    @arg_digest()
    def structures(
        self, include_fragments: bool = False, skip_digestion: bool = False
    ) -> Dict[str, Any]:
        """Protein-centric view of this card's experimental structures."""
        from .structures import structures_view

        return structures_view(self, include_fragments=include_fragments)

    @arg_digest()
    def bioactivities(
        self,
        include_indirect: bool = False,
        thresholds: Dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """Molecule-centric view of this card's measured bioactivities."""
        from .bioactivities import bioactivities_view

        return bioactivities_view(
            self, include_indirect=include_indirect, thresholds=thresholds
        )

    def ligand_sites(self) -> Dict[str, Any]:
        """Residues each ligand contacts, next to the protein's annotated sites."""
        from .ligand_sites import ligand_sites_view

        return ligand_sites_view(self)

    @arg_digest()
    def ligands(
        self,
        deck: Any,
        include_indirect: bool = False,
        thresholds: Dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """This protein crossed with a deck of SmallMoleculeCards (``ligand_deck``)."""
        from .ligands import ligands_view

        return ligands_view(self, deck, include_indirect, thresholds)

    @arg_digest()
    def compare_ligands(
        self,
        deck: Any,
        other: "Card",
        other_deck: Any,
        include_indirect: bool = False,
        thresholds: Dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """Molecules related to this protein and to ``other``, side by side."""
        from .ligands import compare_ligands

        return compare_ligands(
            self, deck, other, other_deck, include_indirect, thresholds
        )

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
        cur[parts[-1]] = field_node(field_path, value, source_assertion_ids)

    def quantity(self, field_path: str) -> Any:
        """The field's value as a PyUnitWizard quantity (session's default form).

        Raises SchemaError when the field holds no quantity.
        """
        return to_quantity(self.get(field_path))

    def quantity_columns(self, template: str) -> Dict[str, Any]:
        """Every quantity at ``template`` as array quantities, one per stored unit.

        ``template`` names a column as the seal does, without list indices, e.g.
        ``relationships.has_structure.resolution`` or
        ``relationships.has_bioactivity.measurement.normalized``. Values keep their stored
        order (relationships by id). Units are never mixed or converted: a column holding
        nanomolar and percent returns both, keyed by unit.
        """
        return quantity_columns(
            {
                "sections": self.sections,
                "relationship_store": self.relationship_store.to_list(),
            },
            template,
        )

    @arg_digest()
    def extract(
        self, field_paths: List[str], skip_digestion: bool = False
    ) -> Dict[str, Any]:
        """``{field_path: node}``; a single path is one field, not its characters."""
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
        """The stored form: every quantity node sealed by ``quantities`` (#32)."""
        data = {
            "meta": self.meta,
            "sections": self.sections,
            "source_assertion_store": self.source_assertion_store.to_list(),
            "relationship_store": self.relationship_store.to_list(),
            "selection_rules": self.selection_rules,
            "quality": self.quality,
        }
        data["quantities"] = seal(data)
        return data

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
        """Rebuild a Card, including its SourceAssertionStore, from ``to_dict()`` output.

        The quantities seal is verified first; a card whose quantities were changed
        outside Sabueso is refused (StorageError).
        """
        data = dict(data)
        verify(data, data.pop("quantities", None))
        return cls(**data)

    @classmethod
    def from_json(cls, path: str) -> "Card":
        from sabueso.tools.card.storage import _read_card_json

        return cls.from_dict(_read_card_json(path))

    @classmethod
    def from_sqlite(
        cls, path: str, table: str = "cards", card_id: str | None = None
    ) -> "Card | None":
        from sabueso.tools.card.storage import _read_card_sqlite

        data = _read_card_sqlite(path, table=table, card_id=card_id)
        if data is None:
            return None
        return cls.from_dict(data)

    def to_deck(self) -> Any:
        from .deck import Deck

        return Deck([self])

    def compare(self, other: "Card", fields: List[str] | None = None) -> Dict[str, Any]:
        """``{field_path: {"self": node, "other": node}}``; ``fields`` as in ``extract``."""
        mine = self.extract([] if fields is None else fields)
        theirs = other.extract(list(mine))
        return {fp: {"self": mine[fp], "other": theirs[fp]} for fp in mine}

    def expand(self, kind: str) -> Any:
        """Not implemented. It used to return an empty Deck, which read as "nothing
        related" rather than "not computed"."""
        raise NotImplementedError("Card.expand is not implemented yet.")
