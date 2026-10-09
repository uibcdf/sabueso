"""SQLite operations close their connections, including failed transactions (#133)."""

import json
import sqlite3
from contextlib import closing

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.tools.card.storage import load_card_sqlite, save_card_sqlite
from sabueso.tools.deck.storage import load_deck_sqlite, save_deck_sqlite


@pytest.fixture
def connections(monkeypatch):
    """Retain real handles so closure is tested independently of garbage collection."""
    original = sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    try:
        yield opened
        assert opened
        for connection in opened:
            with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
                connection.execute("SELECT 1")
    finally:
        for connection in opened:
            connection.close()


@pytest.mark.parametrize("kind", ["card", "deck"])
def test_sqlite_round_trip_closes_handles(tmp_path, connections, kind):
    card = Card(meta={"card_id": "sabueso:protein:uniprot:P60174"})
    path = tmp_path / "round-trip.db"
    if kind == "card":
        save_card_sqlite(card, path)
        assert load_card_sqlite(path).to_dict() == card.to_dict()
    else:
        deck = Deck([card], meta={"purpose": "connection lifetime"})
        save_deck_sqlite(deck, path)
        loaded = load_deck_sqlite(path)
        assert loaded.meta == deck.meta
        assert loaded.cards[0].to_dict() == card.to_dict()


def test_empty_card_lookup_closes_handle(tmp_path, connections):
    path = tmp_path / "empty.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE cards (id INTEGER, card_json TEXT)")
    assert load_card_sqlite(path) is None


@pytest.mark.parametrize("reader", [load_card_sqlite, load_deck_sqlite])
def test_failed_sqlite_query_closes_handle(tmp_path, connections, reader):
    with pytest.raises(sqlite3.OperationalError, match="no such table"):
        reader(tmp_path / "missing-table.db")


@pytest.mark.parametrize("reader", [load_card_sqlite, load_deck_sqlite])
def test_malformed_sqlite_payload_closes_handle(tmp_path, connections, reader):
    path = tmp_path / "malformed.db"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE cards (id INTEGER, card_json TEXT)")
        connection.execute("INSERT INTO cards VALUES (1, 'not JSON')")
    with pytest.raises(json.JSONDecodeError):
        reader(path)


def test_failed_deck_replacement_rolls_back_and_closes_handle(tmp_path, connections):
    card = Card(meta={"card_id": "sabueso:protein:uniprot:P60174"})
    original = Deck([card], meta={"revision": 1})
    path = tmp_path / "replacement.db"
    save_deck_sqlite(original, path)

    class UnserializableCard:
        def to_dict(self):
            raise ValueError("Cannot serialize replacement")

    replacement = Deck([card], meta={"revision": 2})
    replacement.cards.append(UnserializableCard())
    with pytest.raises(ValueError, match="Cannot serialize replacement"):
        save_deck_sqlite(replacement, path)
    loaded = load_deck_sqlite(path)
    assert loaded.meta == original.meta
    assert [item.to_dict() for item in loaded.cards] == [card.to_dict()]
