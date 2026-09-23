"""ProteinCards built from resolved entities (uibcdf/sabueso#6, step 4c).

Covers the subject boundary of acceptance case A5, the resolution trace on the card,
structures as relationships (no scalar structure fields), and ambiguity Decks.
"""

import json
from pathlib import Path

import pytest

from sabueso import ambiguity_deck, resolve_protein_card
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import SchemaError
from sabueso.core.merge import merge_mapping_results
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)

HUMAN_TIM = "sabueso:protein:uniprot:P60174"
TIM_NAME = "triosephosphate isomerase"


@pytest.fixture
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _field_subjects(card, field_paths):
    return {
        card.source_assertion_store.get(sa_id)["subject_ref"]
        for fp in field_paths
        for sa_id in card.get(fp)["source_assertion_ids"]
    }


def test_a5_other_records_can_never_feed_the_entity_fields():
    load = lambda acc: json.loads(Path(f"temp_data/{acc}.json").read_text())  # noqa: E731
    merged = merge_mapping_results(
        [
            map_protein(load("P60174"), "2026-02-01"),
            map_protein(load("V9HWK1"), "2026-02-01"),
        ]
    )
    with pytest.raises(SchemaError):
        build_card_from_mapping(
            merged, meta={"entity_type": "protein"}, entity_subjects={"uniprot:P60174"}
        )


def test_card_from_name_query_keeps_the_trace_and_the_boundary(resolver):
    card, resolution = resolve_protein_card(
        EntityQuery(name=TIM_NAME, organism=9606), resolver, structures=["1HTI", "1KLG"]
    )
    assert card.id == HUMAN_TIM == resolution.entity_ref
    assert _field_subjects(
        card, ["identifiers.uniprot", "sequence.primary", "annotations.function"]
    ) == {"uniprot:P60174"}

    trace = card.quality["entity_resolution"]
    assert (trace["policy"], len(trace["alternatives"])) == ("prefer_reviewed@1", 18)
    assert trace["decision"]["rules"] == ["preference:prefer_reviewed@1"]

    (link,) = card.relationships(predicate="possibly_same_as")
    assert link["object_ref"] == "uniprot:V9HWK1" and "derivation" in link

    view = card.structures()
    assert len(view["items"]) == 24
    hti = next(i for i in view["items"] if i["structure_ref"] == "pdb:1HTI")
    assert hti["sources"] == ["RCSB PDB", "UniProt"]
    assert not [f for f in card.list_fields() if f.startswith("structure")]


def test_card_survives_persistence_with_relationships_and_trace(resolver, tmp_path):
    card, _ = resolve_protein_card("P60174-3", resolver)
    assert card.id == HUMAN_TIM
    assert card.quality["entity_resolution"]["qualifiers"] == {"isoform": "P60174-3"}
    assert card.relationships(predicate="isoform_of")

    card.to_json(str(tmp_path / "card.json"))
    assert Card.from_json(str(tmp_path / "card.json")).to_dict() == card.to_dict()


def test_merged_secondary_accession_builds_the_anchor_card(resolver):
    card, _ = resolve_protein_card("Q6FHP9", resolver)
    assert card.id == HUMAN_TIM
    (link,) = card.relationships(predicate="same_as")
    assert link["subject_ref"] == "uniprot:Q6FHP9"


def test_ambiguous_query_yields_no_card_but_an_ambiguity_deck(resolver):
    card, resolution = resolve_protein_card("P00938", resolver)
    assert card is None and resolution.status == "ambiguous"

    deck = ambiguity_deck(resolution)
    assert deck.meta["kind"] == "entity_ambiguity"
    assert [c.id for c in deck.cards] == [HUMAN_TIM, "sabueso:protein:uniprot:P60175"]
    assert [c.get("annotations.organism")["value"] for c in deck.cards] == [
        "Homo sapiens",
        "Pan troglodytes",
    ]
    assert all(
        c.quality["entity_resolution"]["status"] == "candidate" for c in deck.cards
    )


def test_alternatives_of_a_preference_are_available_as_a_deck(resolver):
    _, resolution = resolve_protein_card(
        EntityQuery(name=TIM_NAME, organism=9606), resolver
    )
    deck = ambiguity_deck(resolution)
    assert deck.meta["kind"] == "entity_alternatives"
    assert len(deck.cards) == 18
    assert "sabueso:protein:uniprot:V9HWK1" in [c.id for c in deck.cards]


def test_unresolved_query_yields_no_card(resolver):
    card, resolution = resolve_protein_card("A0A000Z9Z9", resolver)
    assert card is None and resolution.status == "not_found"
