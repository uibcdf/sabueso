"""Application focal switching keeps an independent exact Deck entry context."""

import socket

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.explorer._deck_session import _DeckSession


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Related Deck reading must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def make_deck(ambiguous=False):
    first = Card(
        meta={
            "card_id": "sabueso:protein:uniprot:synthetic-A",
            "entity_type": "protein",
        }
    )
    target = Card(
        meta={"card_id": "sabueso:disease:mondo:synthetic-B", "entity_type": "disease"}
    )
    assertion = make_source_assertion(
        "relationships.associated_with",
        "mondo:synthetic-B",
        "Synthetic",
        "deck-context-control",
        "2026-11-13",
        subject_ref="uniprot:synthetic-A",
    )
    first.source_assertion_store.add(assertion)
    first.relationship_store.add(
        make_relationship(
            "uniprot:synthetic-A",
            "associated_with",
            "mondo:synthetic-B",
            source_assertion_ids=[assertion["id"]],
        )
    )
    cards = [target, first, first]
    if ambiguous:
        other = Card.from_dict(target.to_dict())
        other.unknown_stored["synthetic_revision"] = 2
        cards.append(other)
    return Deck(cards, meta={"extension": {"source": "Synthetic context control"}})


def act(session, name, **arguments):
    return session.dispatch({"name": name, "revision": session.revision, **arguments})


def open_related(session):
    act(session, "topic", topic="content")
    relationships = next(
        i for i in session.card_session.current.items() if i.label == "Relationships"
    )
    act(session, "open", item_ref=relationships.item_ref)
    item = session.card_session.current.items()[0]
    act(session, "related", item_ref=item.item_ref)
    links = session.card_session.current
    target = links.filter("role", equals="object").items()[0]
    act(session, "open", item_ref=target.item_ref)
    return links


def test_related_profile_changes_without_reassigning_the_entry_occurrence(tmp_path):
    deck = make_deck()
    target_pin = deck.cards[0].pinned_ref()
    source_pin = deck.cards[1].pinned_ref()
    session = _DeckSession(deck, tmp_path)
    act(session, "sort", column="label", descending=False)
    selected = act(session, "search", text="synthetic-A")
    original = act(session, "open", item_ref=selected["items"][1]["ref"])
    assert original["deck_context"]["entry_position"] == 2
    links = open_related(session)
    current = session.panel()
    assert current["profile"] == "disease"
    assert current["deck_context"]["scope"] == "entry_occurrence"
    assert current["deck_context"]["card"]["card_ref"] == source_pin
    assert current["deck_context"]["current_card"]["card_ref"] == target_pin
    assert (
        current["deck_context"]["member_ref"] == original["deck_context"]["member_ref"]
    )
    assert act(session, "back")["view_ref"] == links.view_ref
    restored = act(session, "deck")
    assert (
        restored["view_ref"] == selected["view_ref"]
        and restored["items"] == selected["items"]
    )
    assert session.entry_position is None


def test_cross_member_saved_card_retains_entry_but_does_not_claim_saved_deck(tmp_path):
    session = _DeckSession(make_deck(), tmp_path)
    original = session.panel()
    act(session, "open", item_ref=original["items"][2]["ref"])
    open_related(session)
    target = session.card_session.current
    act(session, "save")
    reopened = act(session, "reopen")
    assert reopened["mode"] == "saved" and reopened["profile"] == "disease"
    assert session.card_session.current.native_payload == target.native_payload
    assert reopened["deck_context"]["entry_position"] == 2
    assert (
        reopened["deck_context"]["current_card"]["card_ref"]
        == target.context["card_ref"]
    )
    assert act(session, "deck")["view_ref"] == original["view_ref"]
    assert session.current.capabilities["saved_deck_reading"] is False


def test_application_revision_choice_and_back_keep_exact_destination(tmp_path):
    deck = make_deck(ambiguous=True)
    session = _DeckSession(deck, tmp_path)
    act(session, "open", item_ref=session.panel()["items"][1]["ref"])
    open_related(session)
    choices = session.card_session.current
    assert choices.outcome["status"] == "ambiguous" and len(choices.items()) == 2
    chosen = choices.items()[1]
    expected = chosen.open().context["card_ref"]
    act(session, "open", item_ref=chosen.item_ref)
    assert session.panel()["deck_context"]["current_card"]["card_ref"] == expected
    assert session.panel()["deck_context"]["entry_position"] == 1
    assert act(session, "back")["view_ref"] == choices.view_ref
