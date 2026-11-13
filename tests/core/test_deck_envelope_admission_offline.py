"""Unknown persisted Deck protocols must not silently be interpreted as format 1."""

import json
import sqlite3

import pytest

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import StorageError


def original():
    return Deck(
        [Card(meta={"card_id": "sabueso:protein:test:synthetic"})],
        meta={"extension": {"value": 1.0, "unit": "nanometer"}},
    )


@pytest.mark.parametrize("version", [None, False, True, 0, 2, 999, "1", [1]])
def test_unknown_jsonl_version_refused_without_changing_input(tmp_path, version):
    deck = original()
    path = tmp_path / "deck.jsonl"
    deck.to_jsonl(str(path))
    lines = path.read_text().splitlines()
    header = json.loads(lines[0])
    header["sabueso_deck"]["format"] = version
    lines[0] = json.dumps(header)
    raw = "\n".join(lines) + "\n"
    path.write_text(raw)
    with pytest.raises(StorageError, match="Unsupported Deck envelope"):
        Deck.from_jsonl(str(path))
    assert path.read_text() == raw


def test_version_one_and_header_free_jsonl_retain_original_cards_and_metadata(tmp_path):
    deck = original()
    path = tmp_path / "deck.jsonl"
    deck.to_jsonl(str(path))
    restored = Deck.from_jsonl(str(path))
    assert restored.meta == deck.meta
    assert restored.cards[0].to_dict() == deck.cards[0].to_dict()
    path.write_text(path.read_text().split("\n", 1)[1])
    legacy = Deck.from_jsonl(str(path))
    assert legacy.meta == {}
    assert legacy.cards[0].to_dict() == deck.cards[0].to_dict()


@pytest.mark.parametrize("version", [0, 2, 999, "unsupported"])
def test_unknown_sqlite_version_refused_and_metadata_kept(tmp_path, version):
    deck = original()
    path = tmp_path / "deck.sqlite"
    deck.to_sqlite(str(path))
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE deck_meta SET format=?", (version,))
    with pytest.raises(StorageError, match="Unsupported Deck SQLite"):
        Deck.from_sqlite(str(path))
    with sqlite3.connect(path) as connection:
        assert (
            json.loads(
                connection.execute("SELECT meta_json FROM deck_meta").fetchone()[0]
            )
            == deck.meta
        )


def test_sqlite_version_one_and_without_metadata_table_remain_readable(tmp_path):
    deck = original()
    path = tmp_path / "deck.sqlite"
    deck.to_sqlite(str(path))
    assert Deck.from_sqlite(str(path)).meta == deck.meta
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE deck_meta")
    legacy = Deck.from_sqlite(str(path))
    assert legacy.meta == {} and legacy.cards[0].to_dict() == deck.cards[0].to_dict()


@pytest.mark.parametrize("placement", ["duplicate", "after_members"])
def test_jsonl_header_cannot_replace_already_admitted_context(tmp_path, placement):
    path = tmp_path / "headers.jsonl"
    deck = original()
    deck.meta = {}
    deck.to_jsonl(str(path))
    header, member = path.read_text().splitlines()
    lines = [header, header, member] if placement == "duplicate" else [member, header]
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(StorageError, match="header must appear once"):
        Deck.from_jsonl(str(path))
