import pytest
import sabueso


@pytest.mark.online
def test_online_cath():
    card = sabueso.create_cath_card_online("1cukA01", retrieved_at="2026-02-04")
    assert card.get("annotations.domains") is not None
