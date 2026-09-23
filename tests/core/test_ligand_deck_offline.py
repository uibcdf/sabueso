"""Ligand decks of protein cards and their crossing (uibcdf/sabueso#23, #25).

TcTIM (P52270, CHEMBL5834) and HsTIM (P60174, CHEMBL4880) with ChEMBL_37 bioactivities,
the structures 1SUX (TcTIM with BTS and sulfate) and 1HTI (HsTIM with PGA), and the
saved ChEMBL molecules and PDB chemical components, all retrieved on 2026-09-23.
"""

from pathlib import Path

import pytest

from sabueso import ligand_deck, resolve_protein_card
from sabueso.core.deck import Deck
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

BTS = "sabueso:small_molecule:inchikey:XBNHRNFODJOFRU-UHFFFAOYSA-N"
SULFATE = "sabueso:small_molecule:inchikey:QAOWNCQODCNURD-UHFFFAOYSA-L"
PGA = "sabueso:small_molecule:inchikey:ASCFNMCAHFUBCO-UHFFFAOYSA-N"


@pytest.fixture(scope="module")
def clients():
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
    )


@pytest.fixture(scope="module")
def cards(clients):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    tc, _ = resolve_protein_card(
        "P52270",
        resolver,
        structures=["1SUX"],
        chembl={},
        chembl_client=clients["chembl_client"],
    )
    hs, _ = resolve_protein_card(
        "P60174",
        resolver,
        structures=["1HTI"],
        chembl={},
        chembl_client=clients["chembl_client"],
    )
    return {"tc": tc, "hs": hs}


@pytest.fixture(scope="module")
def decks(cards, clients):
    return {name: ligand_deck(card, **clients) for name, card in cards.items()}


def _items(view):
    return {i["molecule"]: i for i in view["items"]}


def test_the_deck_holds_one_card_per_molecule(decks):
    deck = decks["tc"]
    # 256 measured molecules plus two structure ligands, BTS and sulfate. BTS is also a
    # measured molecule, so one of them merges into an existing card.
    assert len(deck.cards) == 257
    assert deck.meta["kind"] == "protein_ligands"
    assert deck.meta["protein"] == "sabueso:protein:uniprot:P52270"
    assert deck.meta["identity_rule"] == "standard_inchikey_anchor"
    assert [s["source"] for s in deck.meta["sources"]] == ["ChEMBL", "PDB CCD"]
    assert deck.meta["unanchored"] == []
    assert "not filtered" in deck.meta["notes"][0]  # artifacts are not hidden


def test_structure_meets_bioactivity(cards, decks):
    view = cards["tc"].ligands(decks["tc"])
    items = _items(view)
    bts = items[BTS]
    assert bts["records"] == ["chembl:CHEMBL1161789", "pdb.ligand:BTS"]
    assert bts["observed_in"] == ["bioactivity", "structure"]
    assert bts["structures"] == ["pdb:1SUX"]
    assert bts["bioactivity"] == {
        "class": "weak",
        "best_pchembl": 4.48,
        "measurements": 1,
    }
    # Sulfate is in the structure, not a measured ligand: shown, not promoted.
    assert items[SULFATE]["observed_in"] == ["structure"]
    assert items[SULFATE]["bioactivity"] is None
    assert view["unmatched"] == []
    assert view["classification"]["rule"] == "bioactivity_class@1"


def test_homology_assigned_measurements_stay_visible_without_a_class(cards, decks):
    items = _items(cards["hs"].ligands(decks["hs"]))
    # Phosphoglycolohydroxamate: its only HsTIM measurements were made on rabbit TIM.
    pgh = next(i for i in items.values() if i["name"] == "PHOSPHOGLYCOLOHYDROXAMATE")
    assert (pgh["bioactivity"], pgh["excluded_measurements"]) == (None, 2)
    assert items[PGA]["structures"] == ["pdb:1HTI"]


def test_decks_intersect_by_molecule_identity(decks):
    shared = decks["tc"].intersect(decks["hs"])
    assert len(shared.cards) == 14  # molecules measured on both TIMs
    assert len(decks["tc"].difference(decks["hs"]).cards) == 243
    assert set(shared.ids()) <= set(decks["hs"].ids())


def test_compare_ligands_juxtaposes_both_proteins(cards, decks):
    comparison = cards["tc"].compare_ligands(decks["tc"], cards["hs"], decks["hs"])
    assert (comparison["self"], comparison["other"]) == (
        "sabueso:protein:uniprot:P52270",
        "sabueso:protein:uniprot:P60174",
    )
    assert len(comparison["shared"]) == 14
    assert (len(comparison["only_self"]), len(comparison["only_other"])) == (243, 20)
    shared = {s["molecule"]: s for s in comparison["shared"]}
    # Methyl brevifolincarboxylate: IC50 6.5 uM on TcTIM, > 1 mM on HsTIM.
    brevifolin = next(
        s for s in shared.values() if s["name"] == "METHYLBREVIFOLIN CARBOXYLATE"
    )
    assert brevifolin["self"]["bioactivity"]["class"] == "active"
    assert brevifolin["other"]["bioactivity"]["class"] == "inactive"


def test_structure_ligands_are_optional(cards, clients):
    deck = ligand_deck(cards["tc"], structure_ligands=False, **clients)
    assert len(deck.cards) == 256
    assert deck.meta["notes"] == []
    assert SULFATE not in deck.ids()


def test_source_failures_are_recorded(cards):
    deck = ligand_deck(
        cards["tc"],
        chembl_client=FixtureChEMBLClient("temp_data", failing={"CHEMBL1161789"}),
        ccd_client=FixtureCCDClient("temp_data"),
    )
    chembl = deck.meta["sources"][0]
    assert (chembl["source"], chembl["status"]) == ("ChEMBL", "error")
    # The structure ligands still get cards.
    assert set(deck.ids()) == {BTS, SULFATE}


def test_unichem_is_opt_in_and_its_gaps_are_recorded(cards, clients):
    deck = ligand_deck(
        cards["hs"],
        unichem=True,
        unichem_client=FixtureUniChemClient("temp_data"),
        **clients,
    )
    unichem = deck.meta["sources"][-1]
    assert unichem["source"] == "UniChem"
    assert unichem["found"] == 1  # only 2-phosphoglycolate is saved
    assert len(unichem["not_found"]) == 33
    pga = next(c for c in deck.cards if c.id == PGA)
    refs = {r["subject_ref"] for r in pga.relationships("same_as")}
    assert {"pdb.ligand:PGA", "pdb.ligand:2PL", "chebi:17150"} <= refs


def test_deck_persists(decks, tmp_path: Path):
    path = tmp_path / "tc_ligands.jsonl"
    decks["tc"].to_jsonl(str(path))
    loaded = Deck.from_jsonl(str(path))
    assert loaded.ids() == decks["tc"].ids()
