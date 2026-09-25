"""Traceable deck membership and derived decks (uibcdf/sabueso#58)."""

import pytest

import sabueso
from sabueso.core.deck import Deck
from sabueso.core.errors import SchemaError
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)
from sabueso.tools.card.protein import ambiguity_deck


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


@pytest.fixture(scope="module")
def tims(resolver):
    return [sabueso.resolve(a, resolver=resolver)[0] for a in ("P52270", "P60174")]


def test_an_ambiguity_deck_says_why_each_candidate_is_there(resolver):
    resolution = resolver.resolve(
        EntityQuery(
            name="triosephosphate isomerase", organism=5722, include_subtaxa=True
        )
    )
    deck = ambiguity_deck(resolution)
    assert set(deck.meta["membership"]) == set(deck.ids())
    for card_id in deck.ids():
        assert deck.basis(card_id)["role"] == "candidate"


def test_members_carry_their_basis_and_exclusions_their_reason(tims):
    tc, hs = tims
    deck = Deck(meta={"kind": "cohort"})
    deck.add(tc, basis={"rule": "curator choice", "by": "curator-a"})
    deck.add(hs, basis={"rule": "comparator"})
    deck.exclude(hs.id, "human comparator handled apart", by="curator-a")
    assert deck.ids() == [tc.id]
    assert deck.basis(tc.id) == {"rule": "curator choice", "by": "curator-a"}
    assert deck.basis(hs.id) is None
    assert deck.meta["excluded"] == [
        {
            "candidate": hs.id,
            "reason": "human comparator handled apart",
            "by": "curator-a",
        }
    ]
    with pytest.raises(SchemaError, match="reason"):
        deck.exclude(tc.id, "")


def test_derived_decks_record_their_operations(tims):
    tc, hs = tims
    deck = Deck(meta={"kind": "cohort"})
    deck.add(tc, basis={"rule": "a"})
    deck.add(hs, basis={"rule": "b"})
    derived = deck.in_lineage("Eukaryota").sort("annotations.taxon_id", reverse=True)
    assert [op["operation"] for op in derived.meta["operations"]] == [
        "in_lineage",
        "sort",
    ]
    assert derived.meta["operations"][0]["parameters"] == {"taxon": "Eukaryota"}
    only = derived.in_lineage("Trypanosomatida")
    assert only.meta["membership"] == {tc.id: {"rule": "a"}}  # kept for kept cards
    custom = deck.filter(lambda c: True)
    assert custom.meta["operations"][-1]["reproducible"] is False
    # The source deck is untouched.
    assert "operations" not in deck.meta


def test_membership_survives_jsonl_and_the_store(tims, tmp_path):
    tc, hs = tims
    deck = Deck(meta={"kind": "cohort"})
    deck.add(tc, basis={"rule": "a"})
    deck.exclude(hs.id, "not in scope")
    deck.to_jsonl(str(tmp_path / "cohort.jsonl"))
    assert Deck.from_jsonl(str(tmp_path / "cohort.jsonl")).meta == deck.meta

    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    ref = store.save_deck(deck, "cohort")
    assert store.load_deck(ref).meta == deck.meta
    before = deck.snapshot_id()
    deck.add(hs, basis={"rule": "reconsidered"})
    assert deck.snapshot_id() != before  # membership is part of the deck's content
