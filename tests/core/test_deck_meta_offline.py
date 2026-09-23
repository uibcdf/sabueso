"""Deck meta survives persistence (uibcdf/sabueso#26).

A deck's meta holds the traces that make it interpretable: the decision of an ambiguous
resolution, or the source outcomes and unanchored records of a ligand deck.
"""

import json
import sqlite3
from pathlib import Path

import pytest

from sabueso import ambiguity_deck, ligand_deck, resolve_protein_card
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.deck import read_deck_jsonl, read_deck_sqlite, save_deck_sqlite


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


@pytest.fixture(scope="module")
def decks(resolver):
    chembl = FixtureChEMBLClient("temp_data")
    protein, _ = resolve_protein_card(
        "P60174", resolver, structures=["1HTI"], chembl={}, chembl_client=chembl
    )
    ligands = ligand_deck(
        protein, chembl_client=chembl, ccd_client=FixtureCCDClient("temp_data")
    )
    # P00938 was demerged into human and chimpanzee TIM: ambiguous without an organism.
    ambiguity = ambiguity_deck(resolver.resolve("P00938"))
    return {"ligands": ligands, "ambiguity": ambiguity}


@pytest.mark.parametrize("name", ["ligands", "ambiguity"])
def test_meta_survives_a_jsonl_round_trip(decks, name, tmp_path: Path):
    deck = decks[name]
    path = tmp_path / f"{name}.jsonl"
    deck.to_jsonl(str(path))
    loaded = Deck.from_jsonl(str(path))
    assert loaded.meta == json.loads(json.dumps(deck.meta))
    assert loaded.ids() == deck.ids()


@pytest.mark.parametrize("name", ["ligands", "ambiguity"])
def test_meta_survives_a_sqlite_round_trip(decks, name, tmp_path: Path):
    deck = decks[name]
    path = tmp_path / "decks.db"
    deck.to_sqlite(str(path), table=name)
    loaded = Deck.from_sqlite(str(path), table=name)
    assert loaded.meta == json.loads(json.dumps(deck.meta))
    assert loaded.ids() == deck.ids()


def test_the_traces_are_what_survives(decks, tmp_path: Path):
    decks["ambiguity"].to_jsonl(str(tmp_path / "a.jsonl"))
    decks["ligands"].to_sqlite(str(tmp_path / "l.db"), table="ligands")
    ambiguity = Deck.from_jsonl(str(tmp_path / "a.jsonl")).meta
    ligands = Deck.from_sqlite(str(tmp_path / "l.db"), table="ligands").meta
    assert ambiguity["kind"] == "entity_ambiguity"
    assert ambiguity["decision"]["query"]["identifier"] == "P00938"
    assert ligands["protein"] == "sabueso:protein:uniprot:P60174"
    assert [s["source"] for s in ligands["sources"]] == ["ChEMBL", "PDB CCD"]


def test_two_decks_in_one_database_keep_their_own_meta(decks, tmp_path: Path):
    path = tmp_path / "decks.db"
    for name, deck in decks.items():
        deck.to_sqlite(str(path), table=name)
    assert read_deck_sqlite(path, "ligands")[0]["kind"] == "protein_ligands"
    assert read_deck_sqlite(path, "ambiguity")[0]["kind"] == "entity_ambiguity"


def test_saving_a_deck_into_a_table_replaces_it(tmp_path: Path):
    card = Card(meta={"card_id": "sabueso:protein:uniprot:P60174"})
    path = tmp_path / "decks.db"
    Deck([card], meta={"version": 1}).to_sqlite(str(path))
    Deck([card], meta={"version": 2}).to_sqlite(str(path))
    meta, cards = read_deck_sqlite(path)
    assert (meta, len(cards)) == ({"version": 2}, 1)  # one deck, not an accumulation


def test_files_without_a_header_load_with_empty_meta(tmp_path: Path):
    path = tmp_path / "legacy.jsonl"
    card = Card(meta={"card_id": "sabueso:protein:uniprot:P60174"})
    path.write_text(json.dumps(card.to_dict()) + "\n", encoding="utf-8")
    meta, cards = read_deck_jsonl(path)
    assert (meta, len(cards)) == ({}, 1)


@pytest.mark.parametrize("table", ["cards; DROP TABLE x", "1cards", "deck_meta", ""])
def test_invalid_table_names_are_rejected(table, tmp_path: Path):
    with pytest.raises(ValueError):
        save_deck_sqlite(Deck([]), tmp_path / "decks.db", table=table)


def test_the_tutorial_imports_work():
    from sabueso.tools.card import load_card_json, save_card_json  # noqa: F401
    from sabueso.tools.deck import load_deck_jsonl, save_deck_jsonl  # noqa: F401


def test_the_sqlite_layout(decks, tmp_path: Path):
    path = tmp_path / "decks.db"
    decks["ligands"].to_sqlite(str(path), table="ligands")
    with sqlite3.connect(path) as conn:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"ligands", "deck_meta"} <= tables
        (table,) = conn.execute("SELECT deck_table FROM deck_meta").fetchone()
        assert table == "ligands"
