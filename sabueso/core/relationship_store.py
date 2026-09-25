"""Relationship records and the RelationshipStore.

A Relationship is first-class, traceable knowledge linking a subject to an object through
a predicate, with qualifiers. It is supported either by the SourceAssertions of sources
that state it, or by a derivation record when Sabueso infers it. Derived relationships
never masquerade as SourceAssertions (see ``devguide/SCIENTIFIC_POTENTIAL.md`` and the
EntityResolver contract in ``devguide/archive/entity_resolver.md``).
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, List, Optional, TypedDict

from .errors import SchemaError

# MVP predicate vocabulary (uibcdf/sabueso#6). Extend deliberately, not ad hoc.
PREDICATES = frozenset(
    {
        "same_as",
        "possibly_same_as",
        "isoform_of",
        "superseded_by",
        "has_structure",
        "has_predicted_structure",  # protein -> predicted model (AlphaFold DB), #57
        "engages",  # protein -> molecule: residues and mechanism a paper states, #61
        "annotated_with",  # protein -> GO term
        "classified_in",  # protein -> family / domain / superfamily / site entry
        "interacts_with",  # protein -> protein (physical interaction, e.g. IntAct)
        "functionally_associated_with",  # protein -> protein (STRING functional link)
        "has_bioactivity",  # protein -> molecule (one measured activity, e.g. ChEMBL)
        "has_ligand_site",  # protein -> PDB ligand (residues it contacts, e.g. PDBe-KB)
        "has_interface_with",  # protein -> partner chain (interface residues, PDBe-KB)
        "described_in",  # protein -> publication (pubmed:, doi:), e.g. UniProt references
    }
)

# Qualifiers that distinguish two relationships with the same subject, predicate and
# object, and therefore take part in the relationship id. has_structure is identified by
# the (protein, structure) pair: UniProt cross-references do not name polymer entities,
# so entity-level details are qualifiers and sources stating the pair can agree.
IDENTITY_QUALIFIERS: Dict[str, tuple] = {
    "isoform_of": ("isoform",),
    # One relationship per measurement: the same molecule is often measured several
    # times (assays, papers), and each measurement keeps its own support and context.
    "has_bioactivity": ("activity_id",),
    # One relationship per curated statement: two papers can state engagements of the
    # same molecule (#61).
    "engages": ("statement_id",),
}


class Derivation(TypedDict, total=False):
    """How Sabueso inferred a relationship: never a SourceAssertion."""

    rule: str
    inputs: List[str]
    parameters: Dict[str, Any]
    sabueso_version: str


class Relationship(TypedDict, total=False):
    id: str
    subject_ref: str
    predicate: str
    object_ref: str
    qualifiers: Dict[str, Any]
    qualifier_conflicts: Dict[
        str, List[Any]
    ]  # values that supporting sources disagree on
    source_assertion_ids: List[str]
    derivation: Derivation


def generate_relationship_id(
    subject_ref: str,
    predicate: str,
    object_ref: str,
    qualifiers: Dict[str, Any] | None = None,
) -> str:
    """Deterministic id from subject, predicate, object and identity qualifiers."""
    keys = IDENTITY_QUALIFIERS.get(predicate, ())
    identity = {k: (qualifiers or {}).get(k) for k in keys}
    payload = json.dumps(
        [subject_ref, predicate, object_ref, identity],
        sort_keys=True,
        ensure_ascii=True,
        default=str,
    )
    return "REL_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def make_derivation(
    rule: str,
    inputs: List[str] | None = None,
    parameters: Dict[str, Any] | None = None,
) -> Derivation:
    """Derivation record for a relationship Sabueso infers."""
    from sabueso import __version__

    return {
        "rule": rule,
        "inputs": list(inputs or []),
        "parameters": dict(parameters or {}),
        "sabueso_version": __version__,
    }


def make_relationship(
    subject_ref: str,
    predicate: str,
    object_ref: str,
    qualifiers: Dict[str, Any] | None = None,
    source_assertion_ids: List[str] | None = None,
    derivation: Derivation | None = None,
) -> Relationship:
    """Build a Relationship, asserted (SourceAssertion ids) and/or derived (derivation)."""
    if predicate not in PREDICATES:
        raise SchemaError(f"Unknown relationship predicate: {predicate!r}")
    if not subject_ref or not object_ref:
        raise SchemaError("A relationship needs both subject_ref and object_ref.")
    if not source_assertion_ids and not derivation:
        raise SchemaError(
            "A relationship must be supported by SourceAssertions or a derivation record."
        )
    relationship: Relationship = {
        "id": generate_relationship_id(subject_ref, predicate, object_ref, qualifiers),
        "subject_ref": subject_ref,
        "predicate": predicate,
        "object_ref": object_ref,
        "qualifiers": dict(qualifiers or {}),
    }
    if source_assertion_ids:
        relationship["source_assertion_ids"] = list(dict.fromkeys(source_assertion_ids))
    if derivation:
        relationship["derivation"] = derivation
    return relationship


class RelationshipStore:
    """Registry of the Relationships carried by a card (subject side)."""

    def __init__(self, relationships: List[Relationship] | None = None) -> None:
        self.store: Dict[str, Relationship] = {}
        for relationship in relationships or []:
            self.add(relationship)

    def add(self, relationship: Relationship) -> str:
        """Add a relationship; the same relationship from another source merges support."""
        rel_id = relationship.get("id") or generate_relationship_id(
            relationship["subject_ref"],
            relationship["predicate"],
            relationship["object_ref"],
            relationship.get("qualifiers"),
        )
        existing = self.store.get(rel_id)
        if existing is None:
            # Copy so that merging support later never mutates the caller's record.
            stored = copy.deepcopy(relationship)
            stored["id"] = rel_id
            self.store[rel_id] = stored
            return rel_id
        ids = existing.get("source_assertion_ids", []) + relationship.get(
            "source_assertion_ids", []
        )
        if ids:
            existing["source_assertion_ids"] = list(dict.fromkeys(ids))
        if "derivation" in relationship and "derivation" not in existing:
            existing["derivation"] = relationship["derivation"]
        qualifiers = existing.setdefault("qualifiers", {})
        for key, value in relationship.get("qualifiers", {}).items():
            if key not in qualifiers:
                qualifiers[key] = value
            elif qualifiers[key] != value:
                # Sources disagree on a qualifier: keep every value visible.
                seen = existing.setdefault("qualifier_conflicts", {}).setdefault(
                    key, [qualifiers[key]]
                )
                if value not in seen:
                    seen.append(value)
        return rel_id

    def get(self, relationship_id: str) -> Optional[Relationship]:
        return self.store.get(relationship_id)

    def find(
        self,
        subject_ref: str | None = None,
        predicate: str | None = None,
        object_ref: str | None = None,
    ) -> List[Relationship]:
        return [
            r
            for r in self.store.values()
            if (subject_ref is None or r["subject_ref"] == subject_ref)
            and (predicate is None or r["predicate"] == predicate)
            and (object_ref is None or r["object_ref"] == object_ref)
        ]

    def to_list(self) -> List[Relationship]:
        return list(self.store.values())
