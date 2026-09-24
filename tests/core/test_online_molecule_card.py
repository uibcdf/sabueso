"""Molecule cards and ligand decks against live ChEMBL, RCSB (CCD) and UniChem (network)."""

import pytest

from sabueso import resolve_molecule_card


@pytest.mark.online
def test_online_structure_ligand_resolves_with_its_chembl_record():
    card, resolution = resolve_molecule_card("pdb.ligand:BTS")
    assert resolution.status == "resolved"
    assert card.id == "sabueso:small_molecule:inchikey:XBNHRNFODJOFRU-UHFFFAOYSA-N"
    refs = {r["subject_ref"] for r in card.relationships("same_as")}
    assert {"pdb.ligand:BTS", "chembl:CHEMBL1161789"} <= refs


@pytest.mark.online
def test_online_ligand_deck_of_a_protein():
    from sabueso import ligand_deck, resolve_protein_card

    card, _ = resolve_protein_card("P60174", structures=["1HTI"], chembl={"limit": 20})
    deck = ligand_deck(card)
    assert {s["source"]: s["status"] for s in deck.meta["sources"]} == {
        "ChEMBL": "added",
        "PDB CCD": "added",
    }
    view = card.ligands(deck)
    pga = "sabueso:small_molecule:inchikey:ASCFNMCAHFUBCO-UHFFFAOYSA-N"
    assert pga in {i["molecule_ref"] for i in view["items"]}
