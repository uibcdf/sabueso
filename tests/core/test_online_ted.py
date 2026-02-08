from urllib.error import HTTPError, URLError

import pytest
import sabueso


@pytest.mark.online
def test_online_ted():
    try:
        card = sabueso.create_ted_card_online(
            "AF-A0A7M3WA57-F1-model_v4_TED05", retrieved_at="2026-02-04"
        )
    except (HTTPError, URLError):
        pytest.skip("TED endpoint unreachable or not yet confirmed.")
    assert card.get("annotations.domains") is not None
