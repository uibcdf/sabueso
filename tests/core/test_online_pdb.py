import pytest
import sabueso


@pytest.mark.online
def test_online_pdb_card():
    card = sabueso.create_structure_card_online("2NZT", retrieved_at="2026-02-04")
    assert card.get("structure.entry_metadata.experimental_method") is not None
