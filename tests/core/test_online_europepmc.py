import pytest


@pytest.mark.online
def test_online_mentions_are_paged_and_counted():
    from sabueso.tools.db.europepmc import OnlineEuropePMCClient

    response = OnlineEuropePMCClient().mentions("P60174", limit=3)
    record = response["record"]
    assert record["hitCount"] >= 354 and len(record["articles"]) == 3
    assert response["version"]


@pytest.mark.online
def test_online_located_accession_enters_a_card_with_its_original_locator():
    import sabueso
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.europepmc import OnlineEuropePMCClient

    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": "PMC:PMC12400196"},
        europepmc_client=OnlineEuropePMCClient(timeout=20),
    )
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "Europe PMC"]
    assert record["status"] == "added", record
    (relationship,) = card.relationships("mentioned_in")
    assert relationship["object_ref"] == "pubmed:40832834"
    annotations = [
        location["annotation"] for location in relationship["qualifiers"]["locations"]
    ]
    assert all(a["exact"] == "P60174" and a["provider"] for a in annotations)
    assert any(a["section"].startswith("Figure") for a in annotations)
    for location in relationship["qualifiers"]["locations"]:
        (support,) = card.explain([location["source_assertion_id"]])
        assert support["asserted_value"]["annotation"] == location["annotation"]
        assert support["acquisition"] == {"method": "database", "origin": "text_mining"}
