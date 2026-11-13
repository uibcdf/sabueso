"""Captured member occurrence/return/byte boundaries, not new scientific findings."""

import json
import socket

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.snapshot import canonical_json


@pytest.fixture(autouse=True)
def no_acquisition(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Deck exploration must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def card(identity="one", nature="protein", value=1):
    item = Card(
        meta={"card_id": f"sabueso:{nature}:test:{identity}", "entity_type": nature}
    )
    item.unknown_stored["synthetic"] = {"value": value, "unit": "nanometer"}
    return item


def test_capture_detaches_all_metadata_and_member_revisions_once():
    first = card()
    second = card("two", "disease")
    deck = Deck(
        [first, first, second],
        {
            "membership": {first.id: {"query": "synthetic"}},
            "excluded": [{"candidate": "outside", "reason": "synthetic"}],
            "extension": [1, None],
        },
    )
    native_snapshot = deck.snapshot_id()
    explorer = deck.explore()
    root = explorer.overview()
    before = root.page()
    assert before["context"]["deck_snapshot_id"] == native_snapshot
    first.unknown_stored["synthetic"]["value"] = 999
    deck.meta["extension"].clear()
    deck.cards.reverse()
    assert root.page() == before
    assert root.inspect()["extension"] == [1, None]
    root.inspect()["extension"].clear()
    assert root.inspect()["extension"] == [1, None]
    assert len(root.items()) == 3
    assert root.items()[0].member_ref != root.items()[1].member_ref
    assert root.items()[0].context["card_ref"] == root.items()[1].context["card_ref"]
    assert root.items()[0].basis == {"query": "synthetic"}
    assert root.items()[2].context["membership"]["state"] == "not_stated"
    visit = root.items()[0].open()
    view = visit.explorer.inspect()
    assert view.native_payload["synthetic"] == {"value": 1, "unit": "nanometer"}
    assert (
        visit.back() is root
        and visit.context["member_ref"] == root.items()[0].member_ref
    )


def test_equal_id_different_revisions_and_unidentified_members_are_never_merged():
    old, new = card(value=1), card(value=2)
    anonymous = Card()
    root = Deck([old, new, anonymous]).explore().overview()
    assert root.context["input_count"] == 3
    assert root.context["unidentified_members"] == 1
    assert root.context["deck_snapshot_id"] is None
    assert root.items()[0].context["card_ref"] != root.items()[1].context["card_ref"]
    assert root.items()[2].context["card_ref"] is None
    assert (
        root.items()[2].open().context["card"]["snapshot_id"]
        == root.items()[2].context["snapshot_id"]
    )


def test_selection_order_filter_back_and_card_return_context():
    root = Deck([card("z"), card("a", "disease"), card("b")]).explore().overview()
    ordered = root.sort("label")
    assert [item.position for item in ordered.items()] == [1, 2, 0]
    selected = ordered.select(
        [ordered.items()[2].member_ref, ordered.items()[0].member_ref]
    )
    assert [item.position for item in selected.items()] == [0, 1]
    visit = selected.items()[0].open()
    assert visit.back() is selected and selected.back() is ordered
    assert ordered.back() is root and root.back() is root
    assert [i.position for i in root.filter("disease").items()] == [1]
    assert root.select([]).page()["complete"]
    assert not root.select([]).items()
    with pytest.raises(ArgumentError):
        selected.member(root.items()[2].member_ref)
    with pytest.raises(ArgumentError):
        root.select([root.items()[0].member_ref] * 2)


def test_typed_pages_are_byte_bounded_and_cursor_is_exact_selection_and_session():
    deck = Deck([card(str(i)) for i in range(12)])
    explorer = deck.explore()
    root = explorer.overview()
    page = root.page(limit=3, max_bytes=2048)
    seen = list(page["items"])
    assert len(canonical_json(page).encode("utf-8")) <= 2048
    first_cursor = page["next_cursor"]
    while page["next_cursor"]:
        page = root.page(limit=3, max_bytes=2048, cursor=page["next_cursor"])
        seen.extend(page["items"])
        assert len(canonical_json(page).encode("utf-8")) <= 2048
    assert [row["position"] for row in seen] == list(range(12))
    with pytest.raises(ArgumentError):
        root.sort("label").page(cursor=first_cursor)
    with pytest.raises(ArgumentError):
        deck.access().page(cursor=first_cursor)
    with pytest.raises(ArgumentError):
        root.page(limit=True)
    assert root.select([]).page()["items"] == []
    json.dumps(page)


def test_oversized_membership_is_explicitly_deferred_but_remains_inspectable():
    item = card()
    original = {"source_context": "🧬" * 3000}
    root = Deck([item], {"membership": {item.id: original}}).explore().overview()
    page = root.page(max_bytes=1024)
    assert len(canonical_json(page).encode("utf-8")) <= 1024
    assert page["items"][0]["status"] == "deferred"
    assert root.member(page["items"][0]["member_ref"]).basis == original


def test_empty_deck_and_non_scientific_metadata_are_explicit():
    root = Deck([], {"excluded": [], "extension": {"x": None}}).access()
    assert root.context["input_count"] == 0
    assert root.page()["complete"] and root.page()["items"] == []
    assert root.inspect() == {"excluded": [], "extension": {"x": None}}
