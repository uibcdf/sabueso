from pathlib import Path
import sqlite3

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.tools.card.storage import save_card_json, save_card_sqlite
from sabueso.tools.deck.storage import save_deck_jsonl, save_deck_sqlite


def test_save_card_json(tmp_path: Path):
    card = Card(sections={"identifiers": {"uniprot": {"value": "P00001", "evidence_ids": []}}})
    out = tmp_path / "card.json"
    save_card_json(card, out)
    assert out.exists()
    out2 = tmp_path / "card2.json"
    card.to_json(str(out2))
    assert out2.exists()


def test_save_deck_jsonl(tmp_path: Path):
    card = Card(sections={"identifiers": {"uniprot": {"value": "P00001", "evidence_ids": []}}})
    deck = Deck([card, card])
    out = tmp_path / "deck.jsonl"
    save_deck_jsonl(deck, out)
    assert out.exists()
    assert out.read_text(encoding="utf-8").count("\n") == 2
    out2 = tmp_path / "deck2.jsonl"
    deck.to_jsonl(str(out2))
    assert out2.exists()


def test_save_card_sqlite(tmp_path: Path):
    card = Card(sections={"identifiers": {"uniprot": {"value": "P00001", "evidence_ids": []}}})
    out = tmp_path / "cards.db"
    save_card_sqlite(card, out, id_field="identifiers.uniprot")
    assert out.exists()
    with sqlite3.connect(out) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cards")
        assert cur.fetchone()[0] == 1
    out2 = tmp_path / "cards2.db"
    card.to_sqlite(str(out2), id_field="identifiers.uniprot")
    assert out2.exists()


def test_save_deck_sqlite(tmp_path: Path):
    card = Card(sections={"identifiers": {"uniprot": {"value": "P00001", "evidence_ids": []}}})
    deck = Deck([card, card])
    out = tmp_path / "cards.db"
    save_deck_sqlite(deck, out, id_field="identifiers.uniprot")
    assert out.exists()
    with sqlite3.connect(out) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM cards")
        assert cur.fetchone()[0] == 2
    out2 = tmp_path / "cards2.db"
    deck.to_sqlite(str(out2), id_field="identifiers.uniprot")
    assert out2.exists()
