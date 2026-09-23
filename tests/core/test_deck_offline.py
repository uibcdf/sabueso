"""Deck ordering and persistence round trips (uibcdf/sabueso#14)."""

from pathlib import Path

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.tools.db.chembl import create_molecule_card_from_file
from sabueso.tools.db.uniprot import create_protein_card_from_file


def _cards():
    hk2, hs_tim, tc_tim = (
        create_protein_card_from_file(
            f"temp_data/{acc}.json", retrieved_at="2026-02-01"
        )
        for acc in ("P52789", "P60174", "P52270")
    )
    molecule = create_molecule_card_from_file(
        "temp_data/CHEMBL90555.json", retrieved_at="2026-02-01"
    )  # no sequence
    return hk2, hs_tim, tc_tim, molecule


def test_sort_uses_resolved_values_and_puts_missing_last():
    hk2, hs_tim, tc_tim, molecule = _cards()
    deck = Deck([hk2, molecule, tc_tim, hs_tim])

    ascending = deck.sort("sequence.length")
    assert [c.id for c in ascending.cards] == [
        hs_tim.id,
        tc_tim.id,
        hk2.id,
        molecule.id,
    ]

    descending = deck.sort("sequence.length", reverse=True)
    assert [c.id for c in descending.cards] == [
        hk2.id,
        tc_tim.id,
        hs_tim.id,
        molecule.id,
    ]

    by_name = Deck([tc_tim, hk2, hs_tim]).sort("names.canonical_name")
    assert [c.get("names.canonical_name")["value"] for c in by_name.cards] == [
        "Hexokinase-2",
        "Triosephosphate isomerase",
        "Triosephosphate isomerase, glycosomal",
    ]


def test_deck_loaders_return_cards(tmp_path: Path):
    hk2, hs_tim, tc_tim, _ = _cards()
    deck = Deck([hs_tim, tc_tim])

    deck.to_jsonl(str(tmp_path / "deck.jsonl"))
    deck.to_sqlite(str(tmp_path / "deck.db"))

    for loaded in (
        Deck.from_jsonl(str(tmp_path / "deck.jsonl")),
        Deck.from_sqlite(str(tmp_path / "deck.db")),
    ):
        assert all(isinstance(c, Card) for c in loaded.cards)
        assert [c.id for c in loaded.cards] == [hs_tim.id, tc_tim.id]
        assert [c.to_dict() for c in loaded.cards] == [
            hs_tim.to_dict(),
            tc_tim.to_dict(),
        ]
        node = loaded.cards[1].get("sequence.length")
        assert loaded.cards[1].source_assertion_store.get(
            node["source_assertion_ids"][0]
        )
        assert loaded.sort("sequence.length", reverse=True).cards[0].id == tc_tim.id
