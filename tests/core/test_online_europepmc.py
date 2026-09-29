import pytest


@pytest.mark.online
def test_online_mentions_are_paged_and_counted():
    from sabueso.tools.db.europepmc import OnlineEuropePMCClient

    response = OnlineEuropePMCClient().mentions("P60174", limit=3)
    record = response["record"]
    assert record["hitCount"] >= 354 and len(record["articles"]) == 3
    assert response["version"]
