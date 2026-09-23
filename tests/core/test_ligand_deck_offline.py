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
    # 256 measured molecules. BTS, the ligand of 1SUX, is one of them (CHEMBL1161789),
    # so it merges into an existing card.
    assert len(deck.cards) == 256
    assert deck.meta["kind"] == "protein_ligands"
    assert deck.meta["protein"] == "sabueso:protein:uniprot:P52270"
    assert deck.meta["identity_rule"] == "standard_inchikey_anchor"
    assert [s["source"] for s in deck.meta["sources"]] == ["ChEMBL", "PDB CCD"]
    assert deck.meta["unanchored"] == []
    assert deck.meta["structure_ligands"] == "of_interest"
    # Sulfate is not declared subject of investigation in 1SUX: left out, and said so.
    assert deck.meta["excluded_structure_ligands"] == [
        {
            "ref": "pdb.ligand:SO4",
            "structures": ["pdb:1SUX"],
            "reason": "not_subject_of_investigation",
        }
    ]
    assert "not assert that it is irrelevant" in deck.meta["notes"][0]


def test_the_pdb_states_which_ligand_a_structure_studies(cards):
    (rel,) = cards["tc"].relationships("has_structure", object_ref="pdb:1SUX")
    flags = {
        lig["comp_id"]: (
            lig["subject_of_investigation"],
            lig["subject_of_investigation_provenance"],
        )
        for lig in rel["qualifiers"]["ligands"]
    }
    # 1SUX (2004) predates depositor declarations: RCSB assigned the flag.
    assert flags == {"BTS": (True, ["RCSB"]), "SO4": (False, None)}
    # The flag is part of what RCSB states, not only a qualifier.
    (sa_id,) = [
        i for i in rel["source_assertion_ids"] if i.startswith("SA_RCSB PDB_1SUX")
    ]
    stated = cards["tc"].source_assertion_store.get(sa_id)["asserted_value"]
    assert [n["comp_id"] for n in stated["nonpolymer_entities"]] == ["BTS", "SO4"]


def test_structure_meets_bioactivity(cards, decks):
    view = cards["tc"].ligands(decks["tc"])
    items = _items(view)
    bts = items[BTS]
    assert bts["records"] == ["chembl:CHEMBL1161789", "pdb.ligand:BTS"]
    assert bts["observed_in"] == ["bioactivity", "structure"]
    assert bts["structures"] == bts["structures_of_interest"] == ["pdb:1SUX"]
    assert bts["bioactivity"] == {
        "class": "weak",
        "best_pchembl": 4.48,
        "measurements": 1,
    }
    assert SULFATE not in items
    assert view["unmatched"] == []  # additives and ions are not unmatched molecules
    assert view["classification"]["rule"] == "bioactivity_class@1"


def test_all_structure_ligands_on_request(cards, clients):
    deck = ligand_deck(cards["tc"], structure_ligands="all", **clients)
    assert len(deck.cards) == 257
    assert deck.meta["excluded_structure_ligands"] == []
    sulfate = _items(cards["tc"].ligands(deck))[SULFATE]
    # Shown, never promoted: observed in 1SUX, not declared of interest, not measured.
    assert sulfate["observed_in"] == ["structure"]
    assert (sulfate["structures"], sulfate["structures_of_interest"]) == (
        ["pdb:1SUX"],
        [],
    )
    assert sulfate["bioactivity"] is None


def test_homology_assigned_measurements_stay_visible_without_a_class(cards, decks):
    items = _items(cards["hs"].ligands(decks["hs"]))
    # Phosphoglycolohydroxamate: its only HsTIM measurements were made on rabbit TIM.
    pgh = next(i for i in items.values() if i["name"] == "PHOSPHOGLYCOLOHYDROXAMATE")
    assert (pgh["bioactivity"], pgh["excluded_measurements"]) == (None, 2)
    assert items[PGA]["structures_of_interest"] == ["pdb:1HTI"]


def test_decks_intersect_by_molecule_identity(decks):
    shared = decks["tc"].intersect(decks["hs"])
    assert len(shared.cards) == 14  # molecules measured on both TIMs
    assert len(decks["tc"].difference(decks["hs"]).cards) == 242
    assert set(shared.ids()) <= set(decks["hs"].ids())


def test_compare_ligands_juxtaposes_both_proteins(cards, decks):
    comparison = cards["tc"].compare_ligands(decks["tc"], cards["hs"], decks["hs"])
    assert (comparison["self"], comparison["other"]) == (
        "sabueso:protein:uniprot:P52270",
        "sabueso:protein:uniprot:P60174",
    )
    assert len(comparison["shared"]) == 14
    assert (len(comparison["only_self"]), len(comparison["only_other"])) == (242, 20)
    shared = {s["molecule"]: s for s in comparison["shared"]}
    # Methyl brevifolincarboxylate: IC50 6.5 uM on TcTIM, > 1 mM on HsTIM.
    brevifolin = next(
        s for s in shared.values() if s["name"] == "METHYLBREVIFOLIN CARBOXYLATE"
    )
    assert brevifolin["self"]["bioactivity"]["class"] == "active"
    assert brevifolin["other"]["bioactivity"]["class"] == "inactive"


def test_structure_ligands_are_optional(cards, clients):
    deck = ligand_deck(cards["tc"], structure_ligands=None, **clients)
    assert len(deck.cards) == 256
    assert (deck.meta["notes"], deck.meta["excluded_structure_ligands"]) == ([], [])
    assert [s["source"] for s in deck.meta["sources"]] == ["ChEMBL"]
    with pytest.raises(ValueError):
        ligand_deck(cards["tc"], structure_ligands="artifacts", **clients)


def test_source_failures_are_recorded(cards):
    deck = ligand_deck(
        cards["tc"],
        chembl_client=FixtureChEMBLClient("temp_data", failing={"CHEMBL1161789"}),
        ccd_client=FixtureCCDClient("temp_data"),
    )
    chembl = deck.meta["sources"][0]
    assert (chembl["source"], chembl["status"]) == ("ChEMBL", "error")
    # The structure ligand of interest still gets its card.
    assert deck.ids() == [BTS]


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
