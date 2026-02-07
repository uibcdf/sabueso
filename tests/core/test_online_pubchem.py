import pytest
import sabueso


@pytest.mark.online
def test_online_pubchem_card():
    card = sabueso.create_compound_card_online("66414", retrieved_at="2026-02-04")
    assert card.get("identifiers.secondary_ids.pubchem") is not None
