"""resolve_molecule_card against live ChEMBL, RCSB (CCD) and UniChem (network)."""

import pytest

from sabueso import resolve_molecule_card


@pytest.mark.online
def test_online_structure_ligand_resolves_with_its_chembl_record():
    card, resolution = resolve_molecule_card("pdb.ligand:BTS")
    assert resolution.status == "resolved"
    assert card.id == "sabueso:small_molecule:inchikey:XBNHRNFODJOFRU-UHFFFAOYSA-N"
    refs = {r["subject_ref"] for r in card.relationships("same_as")}
    assert {"pdb.ligand:BTS", "chembl:CHEMBL1161789"} <= refs
