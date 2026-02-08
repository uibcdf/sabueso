import pytest
import sabueso


@pytest.mark.online
def test_online_interpro_entry():
    card = sabueso.create_interpro_card_online("IPR000001", retrieved_at="2026-02-04")
    assert card.get("annotations.domains") is not None
