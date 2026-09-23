"""EntityResolver against the live UniProt REST API (network)."""

import pytest

from sabueso.resolver import EntityQuery, EntityResolver


@pytest.mark.online
def test_online_entity_resolution_matches_the_offline_contract():
    resolver = EntityResolver()
    human = "sabueso:protein:uniprot:P60174"

    assert resolver.resolve("P60174").entity_ref == human

    merged = resolver.resolve("Q6FHP9")  # answered by redirect to the active entry
    assert merged.entity_ref == human
    assert [(lk["predicate"], lk["object_ref"]) for lk in merged.identity_links] == [
        ("same_as", "uniprot:P60174")
    ]

    assert resolver.resolve("P00938").status == "ambiguous"
    demerged = resolver.resolve(EntityQuery(identifier="P00938", organism=9606))
    assert demerged.entity_ref == human

    assert resolver.resolve("A0A000Z9Z9").status == "not_found"
