"""Deck/Card application return context, repeated occurrences and original inputs."""

import socket

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.explorer._deck_session import _DeckSession


@pytest.fixture(autouse=True)
def no_source_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Ordinary Deck reading must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def make_deck(count=3):
    a = Card(meta={"card_id": "sabueso:protein:test:z", "entity_type": "protein"})
    a.unknown_stored["synthetic"] = "original"
    b = Card(meta={"card_id": "sabueso:disease:test:a", "entity_type": "disease"})
    return Deck(
        ([a, b, a] * count)[:count],
        meta={
            "membership": {a.id: {"basis": "synthetic_control"}},
            "extension": {"unknown": None},
        },
    )


def act(session, name, **args):
    return session.dispatch({"name": name, "revision": session.revision, **args})


def test_order_filter_member_source_and_exact_deck_return(tmp_path):
    session = _DeckSession(make_deck(), tmp_path)
    first = session.panel()
    assert first["workspace"] == "deck" and first["count"] == 3
    assert first["items"][0]["ref"] != first["items"][2]["ref"]
    ordered = act(session, "sort", column="label", descending=False)
    selected = act(session, "search", text="protein")
    member = selected["items"][1]
    inside = act(session, "open", item_ref=member["ref"])
    assert inside["profile"] == "protein"
    assert inside["deck_context"]["member_ref"] == member["ref"]
    act(session, "topic", topic="content")
    assert act(session, "back")["profile"] == "protein"
    restored = act(session, "back")
    assert restored["view_ref"] == selected["view_ref"]
    assert [x["ref"] for x in restored["items"]] == [
        x["ref"] for x in selected["items"]
    ]
    assert act(session, "back")["view_ref"] == ordered["view_ref"]
    assert act(session, "back")["view_ref"] == first["view_ref"]


def test_member_card_save_reopen_and_explicit_outer_return(tmp_path):
    s = _DeckSession(make_deck(), tmp_path)
    member = s.panel()["items"][0]
    act(s, "open", item_ref=member["ref"])
    act(s, "topic", topic="content")
    original = s.card_session.current
    act(s, "save")
    reopened = act(s, "reopen")
    assert reopened["mode"] == "saved"
    assert s.card_session.current.native_payload == original.native_payload
    assert reopened["deck_context"]["member_ref"] == member["ref"]
    assert act(s, "deck")["workspace"] == "deck"


def test_paging_and_metadata_return_do_not_change_selection(tmp_path):
    s = _DeckSession(make_deck(83), tmp_path)
    first = s.panel()
    assert len(first["items"]) == 40
    second = act(s, "deck_next")
    assert second["offset"] == 40
    metadata = act(s, "metadata")
    assert metadata["items"] == [] and "synthetic_control" in metadata["text"]
    assert act(s, "back")["offset"] == 40
    act(s, "open", item_ref=second["items"][0]["ref"])
    assert act(s, "deck")["offset"] == 40
    assert act(s, "deck_previous")["items"] == first["items"]


@pytest.mark.parametrize(
    "action",
    [
        {"name": []},
        {"name": "save"},
        {"name": "open", "item_ref": []},
        {"name": "open", "item_ref": "foreign"},
        {"name": "deck_next"},
        {"name": "deck_previous"},
        {"name": "back"},
    ],
)
def test_refused_deck_action_retains_context(tmp_path, action):
    s = _DeckSession(make_deck(), tmp_path)
    before = s.panel()
    with pytest.raises(ArgumentError):
        s.dispatch({"revision": s.revision, **action})
    assert s.panel() == before
