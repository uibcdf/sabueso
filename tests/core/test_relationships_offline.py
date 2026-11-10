"""Relationship model and RelationshipStore (uibcdf/sabueso#6, step 1)."""

from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import SchemaError
from sabueso.core.relationship_store import (
    RelationshipStore,
    make_derivation,
    make_relationship,
)
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion


def _structure_assertion(source, record, value):
    """What a source states about a protein-structure link (public TcTIM data)."""
    return make_source_assertion(
        "relationships.has_structure", value, source, record, "2026-09-23"
    )


def test_relationship_id_is_deterministic_and_uses_identity_qualifiers():
    sa = _structure_assertion("UniProt", "P52270", {"object_ref": "pdb:1TCD"})
    base = dict(
        subject_ref="uniprot:P52270",
        predicate="has_structure",
        object_ref="pdb:1TCD",
        source_assertion_ids=[sa["id"]],
    )
    a = make_relationship(qualifiers={"polymer_entity": "1", "coverage": 0.99}, **base)
    b = make_relationship(qualifiers={"coverage": 0.5}, **base)
    # has_structure is identified by the (protein, structure) pair, so sources that do
    # and do not name polymer entities (RCSB vs UniProt) state the same relationship.
    assert a["id"] == b["id"]
    assert a["id"].startswith("REL_")

    iso = dict(
        subject_ref="uniprot:P60174-3",
        predicate="isoform_of",
        object_ref="uniprot:P60174",
        source_assertion_ids=[sa["id"]],
    )
    assert (
        make_relationship(qualifiers={"isoform": "P60174-3"}, **iso)["id"]
        != make_relationship(qualifiers={"isoform": "P60174-4"}, **iso)["id"]
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(predicate="inhibits"),  # not in the vocabulary
        dict(object_ref=""),
        dict(source_assertion_ids=None, derivation=None),  # unsupported relationship
    ],
)
def test_invalid_relationships_are_rejected(kwargs):
    args = dict(
        subject_ref="uniprot:P60174",
        predicate="same_as",
        object_ref="uniprot:V9HWK1",
        source_assertion_ids=["SA_x"],
    )
    args.update(kwargs)
    with pytest.raises(SchemaError):
        make_relationship(**args)


def test_same_relationship_from_two_sources_merges_support_and_keeps_conflicts():
    uniprot = _structure_assertion(
        "UniProt", "P52270", {"object_ref": "pdb:1TCD", "chains": "A/B"}
    )
    rcsb = _structure_assertion(
        "RCSB PDB", "1TCD", {"object_ref": "uniprot:P52270", "chains": "A"}
    )
    common = dict(
        subject_ref="uniprot:P52270", predicate="has_structure", object_ref="pdb:1TCD"
    )
    from_uniprot = make_relationship(
        qualifiers={"polymer_entity": "1", "chains": "A/B"},
        source_assertion_ids=[uniprot["id"]],
        **common,
    )
    from_rcsb = make_relationship(
        qualifiers={"polymer_entity": "1", "chains": "A"},
        source_assertion_ids=[rcsb["id"]],
        **common,
    )

    store = RelationshipStore([from_uniprot, from_rcsb])
    (merged,) = store.to_list()

    assert merged["source_assertion_ids"] == [uniprot["id"], rcsb["id"]]
    assert merged["qualifiers"]["chains"] == "A/B"
    assert merged["qualifier_conflicts"] == {"chains": ["A/B", "A"]}
    assert "qualifier_conflicts" not in from_uniprot  # caller's record is not mutated


@pytest.mark.parametrize(
    "first,second",
    [
        (0, False),
        (1, True),
        (1, 1.0),
        ([0], [False]),
        ({"counts": [1]}, {"counts": [True]}),
        ({"count": 1}, {"count": 1.0}),
        ([{"count": 0}], [{"count": False}]),
    ],
)
def test_typed_qualifier_alternatives_survive_merge_and_card_roundtrip(
    first, second, tmp_path
):
    mapping = _mapping_with_relationship()
    original = mapping["relationships"][0]
    original["qualifiers"]["experiments"] = first
    alternative = deepcopy(original)
    alternative["qualifiers"]["experiments"] = second
    alternative["source_assertion_ids"] = ["SA_second"]
    before = deepcopy([original, alternative])
    store = RelationshipStore([original, alternative, alternative])
    (merged,) = store.to_list()
    assert merged["id"] == original["id"]
    assert canonical_json(merged["qualifiers"]["experiments"]) == canonical_json(first)
    assert canonical_json(
        merged["qualifier_conflicts"]["experiments"]
    ) == canonical_json([first, second])
    assert merged["source_assertion_ids"] == original["source_assertion_ids"] + [
        "SA_second"
    ]
    assert canonical_json([original, alternative]) == canonical_json(before)
    # Persist the already merged metadata using the original valid source binding.
    merged["source_assertion_ids"] = original["source_assertion_ids"]
    mapping["relationships"] = [merged]
    card = build_card_from_mapping(
        mapping, meta={"entity_type": "protein"}, card_id="synthetic:typed-qualifiers"
    )
    target = str(tmp_path / "typed-qualifiers.json")
    card.to_json(target)
    loaded = Card.from_json(target)
    assert canonical_json(loaded.relationship_store.to_list()) == canonical_json(
        card.relationship_store.to_list()
    )


def test_existing_typed_conflict_alternatives_merge_without_losing_or_duplicating():
    original = _mapping_with_relationship()["relationships"][0]
    original["qualifiers"]["experiments"] = 0
    alternative = deepcopy(original)
    alternative["qualifier_conflicts"] = {"experiments": [0, False, 0.0, False]}
    before = deepcopy(alternative)
    store = RelationshipStore([original, alternative, alternative])
    (merged,) = store.to_list()
    assert (
        canonical_json(merged["qualifier_conflicts"]["experiments"]) == "[0,false,0.0]"
    )
    assert canonical_json(alternative) == canonical_json(before)


def test_derived_relationship_carries_a_derivation_record():
    derivation = make_derivation(
        "identical_sequence_same_organism",
        inputs=["uniprot:P60174", "uniprot:V9HWK1"],
        parameters={"checksum": "md5", "organism": 9606},
    )
    rel = make_relationship(
        "uniprot:P60174",
        "possibly_same_as",
        "uniprot:V9HWK1",
        derivation=derivation,
    )

    assert "source_assertion_ids" not in rel  # derived, never presented as asserted
    assert rel["derivation"]["rule"] == "identical_sequence_same_organism"
    assert rel["derivation"]["sabueso_version"]


def _mapping_with_relationship():
    sa = _structure_assertion(
        "UniProt",
        "P52270",
        {"object_ref": "pdb:1TCD", "chains": "A/B", "range": "3-251"},
    )
    rel = make_relationship(
        "uniprot:P52270",
        "has_structure",
        "pdb:1TCD",
        qualifiers={"polymer_entity": "1", "chains": "A/B", "range": "3-251"},
        source_assertion_ids=[sa["id"]],
    )
    return {
        "fields": {},
        "source_assertions": [sa],
        "field_source_assertions": {},
        "relationships": [rel],
    }


def test_card_keeps_relationships_through_persistence(tmp_path: Path):
    card = build_card_from_mapping(
        _mapping_with_relationship(),
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )
    (rel,) = card.relationships(predicate="has_structure")
    assert rel["object_ref"] == "pdb:1TCD"
    assert card.source_assertion_store.get(rel["source_assertion_ids"][0])

    card.to_json(str(tmp_path / "card.json"))
    loaded = Card.from_json(str(tmp_path / "card.json"))
    assert loaded.to_dict() == card.to_dict()
    assert loaded.relationships(object_ref="pdb:1TCD") == [rel]

    Deck([card]).to_jsonl(str(tmp_path / "deck.jsonl"))
    (from_deck,) = Deck.from_jsonl(str(tmp_path / "deck.jsonl")).cards
    assert from_deck.relationships() == [rel]


def test_relationship_citing_unknown_source_assertions_is_rejected():
    mapping = _mapping_with_relationship()
    mapping["source_assertions"] = []
    with pytest.raises(SchemaError):
        build_card_from_mapping(mapping, meta={"entity_type": "protein"})
