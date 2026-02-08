import os
import pytest
import sabueso


@pytest.mark.online
def test_online_biogrid():
    if not os.getenv("BIOGRID_ACCESS_KEY"):
        pytest.skip("BIOGRID_ACCESS_KEY not set")
    card = sabueso.create_biogrid_card_online("TP53", retrieved_at="2026-02-04")
    assert card.get("interactions.binding_partners") is not None
