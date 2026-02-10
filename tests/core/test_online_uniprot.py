import pytest
import sabueso


@pytest.mark.online
def test_online_uniprot_card():
    card = sabueso.create_protein_card_online("P52789")
    assert card.get("identifiers.uniprot") is not None
