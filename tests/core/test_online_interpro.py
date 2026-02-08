from urllib.error import HTTPError, URLError

import pytest
import sabueso


@pytest.mark.online
def test_online_interpro_entry():
    try:
        card = sabueso.create_interpro_card_online("IPR000001", retrieved_at="2026-02-04")
    except (HTTPError, URLError, TimeoutError):
        pytest.skip("InterPro endpoint slow or unreachable from this environment.")
    assert card.get("annotations.domains") is not None
