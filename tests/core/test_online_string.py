import pytest
import sabueso


@pytest.mark.online
def test_online_string():
    card = sabueso.create_string_card_online("TP53")
    assert card.get("interactions.binding_partners") is not None
