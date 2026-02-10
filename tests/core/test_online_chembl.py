import pytest
import sabueso


@pytest.mark.online
def test_online_chembl_card():
    card = sabueso.create_molecule_card_online("CHEMBL1", retrieved_at="2026-02-04")
    assert card.get("identifiers.chembl") is not None
