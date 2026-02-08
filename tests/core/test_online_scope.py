from urllib.error import HTTPError, URLError

import pytest
import sabueso


@pytest.mark.online
def test_online_scope():
    try:
        card = sabueso.create_scope_card_online("46456", retrieved_at="2026-02-04")
    except (HTTPError, URLError):
        pytest.skip("SCOPe endpoint unreachable from this environment.")
    assert card.get("annotations.domains") is not None
