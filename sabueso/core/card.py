"""Card core implementation (minimal)."""

from __future__ import annotations

from typing import Any, Dict, List

from sabueso._private.argdigest import arg_digest

from .quantities import field_node, quantity_columns, seal, to_quantity, verify
from .relationship_store import Relationship, RelationshipStore
from .source_assertion_store import SourceAssertionStore

CARD_SCHEMA_VERSION = "0.3.1"


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
        entities: Dict[str, Any] | None = None,
    ) -> None:
        self.meta = meta or {}
        # A card always states its schema; a stored card keeps the one it was written with.
        self.meta.setdefault("schema_version", CARD_SCHEMA_VERSION)
        self.sections = sections or {}
        # Top-level keys of a newer schema this version does not know: kept, never
        # dropped, so saving the card again does not lose them (#42).
        self.unknown_stored: Dict[str, Any] = {}
        # Resolved identities (anchor -> records), the stored part of the glossary of
        # entities; the rest of the glossary is derived from relationships (#52).
        self.entity_identities: Dict[str, Dict[str, Any]] = {
            key: {
                "entity_type": entry.get("entity_type"),
                "records": list(entry.get("records") or []),
                "resolved": entry["identity"],
            }
            for key, entry in (entities or {}).items()
            if entry.get("identity")
        }
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

    @arg_digest()
    def add_literature_assertion(
        self,
        field_path: str,
        value: Any,
        publication: str,
        curator: str,
        locator: str | None = None,
        quote: str | None = None,
        method: str | None = None,
        eco_code: str | None = None,
        curated_at: str | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """Record what a publication states about one of this card's fields.

        ``publication`` is ``pubmed:<id>`` or ``doi:<doi>``; ``locator`` says where
        (figure, table, page) and ``quote`` is an optional short excerpt. The assertion
        is compared with what other sources state, never given priority, and never
        discarded; a difference is recorded in ``quality.conflicts`` and warned about.
        Returns the curation record (``outcome``: new, corroborates, differs,
        not_comparable or not_compared). See ``sabueso.core.curation``.
        """
        from sabueso._private.smonitor.outcomes import report_curated_disagreement

        from .curation import add_literature_assertion

        record = add_literature_assertion(
            self,
            field_path,
            value,
            publication,
            curator,
            locator=locator,
            quote=quote,
            method=method,
            eco_code=eco_code,
            curated_at=curated_at,
        )
        if record["outcome"] == "differs":
            report_curated_disagreement(self.id or "", field_path, publication)
        return record

    @arg_digest()
    def add_literature_relationship(
        self,
        predicate: str,
        object_ref: str,
        qualifiers: Dict[str, Any] | None,
        publication: str,
        curator: str,
        locator: str | None = None,
        quote: str | None = None,
        eco_code: str | None = None,
        curated_at: str | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """Record a relationship a publication states, e.g. an interaction or the
        residues at an interface. It merges with the same relationship from other
        sources; qualifiers it states differently are kept as conflicts and warned
        about. See ``sabueso.core.curation``."""
        from sabueso._private.smonitor.outcomes import report_curated_disagreement

        from .curation import add_literature_relationship

        record = add_literature_relationship(
            self,
            predicate,
            object_ref,
            qualifiers,
            publication,
            curator,
            locator=locator,
            quote=quote,
            eco_code=eco_code,
            curated_at=curated_at,
        )
        if record["outcome"] == "differs":
            report_curated_disagreement(self.id or "", record["field"], publication)
        return record

    @arg_digest()
    def add_literature_bioactivity(
        self,
        molecule: Any,
        measurement_type: str,
        value: Any,
        publication: str,
        curator: str,
        target_assignment: str,
        relation: str = "=",
        assay_description: str | None = None,
        locator: str | None = None,
        quote: str | None = None,
        eco_code: str | None = None,
        curated_at: str | None = None,
        skip_digestion: bool = False,
    ) -> Dict[str, Any]:
        """Record a bioactivity a publication reports, e.g. an IC50 read in a table.

        ``molecule`` is a small-molecule card, an identifier Sabueso resolves
        (``chembl:``, ``pubchem:``, ``pdb.ligand:``, ``inchikey:``) or a recorded identity
        ``{"inchikey", "records"}``; the measurement keeps the InChIKey and every linked
        record. ``value`` has its unit (``"33 uM"``, ``"45 %"``, a quantity).
        ``target_assignment`` says whether it was measured on this protein ("direct") or
        an ortholog ("homology"). It is compared with ChEMBL's measurements of the same
        publication, never given priority. See ``sabueso.core.curation``.
        """
        from sabueso._private.smonitor.outcomes import report_curated_disagreement

        from .curation import add_literature_bioactivity

        record = add_literature_bioactivity(
            self,
            molecule,
            measurement_type,
            value,
            publication,
            curator,
            target_assignment,
            relation=relation,
            assay_description=assay_description,
            locator=locator,
            quote=quote,
            eco_code=eco_code,
            curated_at=curated_at,
        )
        if record["outcome"] == "differs":
            report_curated_disagreement(self.id or "", record["field"], publication)
        return record

    def entities(self) -> Dict[str, Any]:
        """The glossary of molecular entities this card mentions, each once (#52)."""
        from .entities import build_entities

        return build_entities(self)

    def entity(self, ref: str) -> Dict[str, Any] | None:
        """The glossary entry of the entity a record belongs to, with its key."""
        from .entities import resolve_ref

        key, entry = resolve_ref(self, ref)
        return None if entry is None else {"key": key, **entry}

    def register_identity(
        self,
        anchor: str,
        records: List[str],
        entity_type: str,
        resolved: Dict[str, Any],
    ) -> None:
        """Record that ``records`` name the entity anchored at ``anchor``."""
        known = self.entity_identities.setdefault(
            anchor, {"entity_type": entity_type, "records": [], "resolved": resolved}
        )
        known["records"] = sorted(set(known["records"]) | set(records))

    def literature(self) -> Dict[str, Any]:
        """The publications that support statements on this card, and what for."""
        from .literature import literature_view

        return literature_view(self)

    def oligomer(self) -> Dict[str, Any]:
        """What sources state about this protein's quaternary structure and interfaces."""
        from .oligomer import oligomer_view

        return oligomer_view(self)

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
            "entities": self.entities(),
            **self.unknown_stored,
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

        The card's schema version is checked first (``sabueso.core.schema_version``): a
        card of another schema line is refused, and one of a newer version of this line is
        read with a warning. Then the quantities seal is verified; a card whose quantities
        were changed outside Sabueso is refused (StorageError).
        """
        from .schema_version import check_card_schema

        data = dict(data)
        newer = check_card_schema(data.get("meta"), CARD_SCHEMA_VERSION)
        verify(data, data.pop("quantities", None))
        known = {
            "meta",
            "sections",
            "source_assertion_store",
            "relationship_store",
            "selection_rules",
            "quality",
            "entities",
        }
        card = cls(**{k: v for k, v in data.items() if k in known})
        card.unknown_stored = {k: v for k, v in data.items() if k not in known}
        if newer:
            from sabueso._private.smonitor.outcomes import report_newer_schema

            report_newer_schema(card.id or "", card.meta["schema_version"])
        return card

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
