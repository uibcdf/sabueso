import pytest
import sabueso


@pytest.mark.online
def test_online_go_term():
    card = sabueso.create_go_card_online("GO:0008150", retrieved_at="2026-02-04")
    assert card.get("annotations.go_terms") is not None
