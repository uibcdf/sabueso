"""Scientific operations (#91): navigate relationships into decks, explain why an item
is there, and read what a store knew on a date."""

import json
import time
import warnings
from datetime import date, datetime, timedelta, timezone

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentTruncatedWarning
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.tools.db.mondo import FixtureMONDOClient

DISEASE_OPTIONS = {"disease": {"mondo_client": FixtureMONDOClient("temp_data")}}


@pytest.fixture(scope="module")
def hstim():
    return Card.from_dict(
        json.loads(
            open(
                "temp_data/frozen_cards/schema_0.3.6__P60174.json", encoding="utf-8"
            ).read()
        )
    )


def _expand(card, predicate, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return sabueso.expand(card, predicate, options=DISEASE_OPTIONS, **kwargs)


def test_related_entities_become_a_deck_with_their_statements(hstim):
    deck = _expand(hstim, "associated_with", limit=200)
    assert deck.meta["rule"] == "relationship_expansion@1"
    assert deck.meta["from"] == [hstim.id]
    tpi = "sabueso:disease:mondo:MONDO:0014221"
    basis = deck.basis(tpi)
    # DISEASES (DOID), Open Targets (MONDO) and Orphanet (ORPHA) name one disease: one
    # member, with every statement that brought it.
    assert {"doid:DOID:0050884", "mondo:MONDO:0014221", "orphanet:ORPHA:868"} <= set(
        basis["refs"]
    )
    sources = {a["source"] for s in basis["statements"] for a in s["source_assertions"]}
    assert {"DISEASES", "Open Targets", "Orphanet"} <= sources


def test_what_cannot_be_followed_says_why(hstim):
    deck = _expand(hstim, ["participates_in", "associated_with"], limit=3)
    reasons = {e["reason"] for e in deck.meta["excluded"]}
    # Reactome pathways have no card type in Sabueso; past the limit, candidates wait.
    assert {"no_card_type", "limit"} <= reasons
    assert len(deck.cards) <= 3


def test_a_cut_is_reported(hstim):
    with pytest.warns(EnrichmentTruncatedWarning):
        sabueso.expand(hstim, "associated_with", limit=2, options=DISEASE_OPTIONS)


def test_the_best_supported_entities_come_first(hstim):
    deck = _expand(hstim, "associated_with", limit=1)
    (only,) = deck.cards
    assert only.id == "sabueso:disease:mondo:MONDO:0014221"


def test_explain_walks_back_to_the_source_assertions(hstim):
    deck = _expand(hstim, "associated_with", limit=1)
    why = deck.explain("sabueso:disease:mondo:MONDO:0014221")
    assert why["in_deck"] and why["deck"]["rule"] == "relationship_expansion@1"
    statement = why["basis"]["statements"][0]
    (sa,) = hstim.explain([statement["source_assertions"][0]["id"]])
    assert sa["found"] and sa["source"] in {"DISEASES", "Open Targets", "Orphanet"}
    assert sa["subject_ref"] == "uniprot:P60174"
    assert hstim.explain(["SA_nowhere"]) == [{"id": "SA_nowhere", "found": False}]
    left_out = deck.meta["excluded"][0]["candidate"]
    assert deck.explain(left_out)["excluded"]


def test_a_deck_expands_from_every_card(hstim):
    deck = Deck([hstim])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        expanded = deck.expand("associated_with", limit=1, options=DISEASE_OPTIONS)
    assert expanded.meta["from"] == [hstim.id]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        same = hstim.expand("associated_with", limit=1, options=DISEASE_OPTIONS)
    assert same.ids() == expanded.ids()


def test_only_known_predicates_are_followed(hstim):
    with pytest.raises(ArgumentError):
        sabueso.expand(hstim, "likes")


def test_what_the_store_knew_on_a_date(hstim, tmp_path):
    store = sabueso.KnowledgeStore(tmp_path / "k.db")
    store.save(hstim)
    yesterday = date.today() - timedelta(days=1)
    assert store.as_of(hstim.id, yesterday) is None  # nothing stored by then
    assert store.as_of(hstim.id, date.today()).id == hstim.id
    assert store.as_of(hstim.id, datetime.now(timezone.utc)).id == hstim.id
    assert store.changed_since(hstim.id, yesterday)["changed"] is None
    assert store.changed_since(hstim.id, date.today())["changed"] is False
    # The store keeps times to the second: the next revision is a second later.
    first_saved = datetime.now(timezone.utc)
    time.sleep(1.1)
    # A new revision with different knowledge is a change.
    changed = Card.from_dict(json.loads(json.dumps(hstim.to_dict())))
    changed.add_literature_assertion(
        "properties.physchem.logp", 2.0, "pubmed:2", "test", method="test"
    )
    store.save(changed)
    assert store.changed_since(hstim.id, first_saved)["changed"] is True
    assert store.changed_since(hstim.id, date.today())["changed"] is False
    with pytest.raises(sabueso.StorageError):
        store.as_of("sabueso:protein:uniprot:NOWHERE", date.today())


def test_a_deck_as_of_a_date(hstim, tmp_path):
    store = sabueso.KnowledgeStore(tmp_path / "k.db")
    store.save_deck(Deck([hstim]), "tim")
    assert store.as_of("tim", date.today()).cards[0].id == hstim.id
    with pytest.raises(ArgumentError):
        store.as_of("tim", "not a date")
