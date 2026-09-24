"""STRING functional associations and recorded enrichment outcomes (#21, part 2c)."""

import pytest

from sabueso import resolve_protein_card
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.stringdb import FixtureStringClient


@pytest.fixture
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _associations(card):
    return {
        r["qualifiers"]["partner_name"]: r
        for r in card.relationships("functionally_associated_with")
    }


def test_string_adds_scored_functional_associations(resolver):
    card, _ = resolve_protein_card(
        "P60174", resolver, string={}, string_client=FixtureStringClient("temp_data")
    )
    (enrichment,) = card.quality["enrichments"]
    assert enrichment == {
        "source": "STRING",
        "identifier": "P60174",
        "species": 9606,
        "required_score": 700,
        "limit": 50,
        "status": "added",
        "version": "12.0",
        "count": 50,
    }

    associations = _associations(card)
    assert len(associations) == 50
    gapdhs = associations["GAPDHS"]
    assert gapdhs["object_ref"] == "string:9606.ENSP00000222286"
    q = gapdhs["qualifiers"]
    assert q["combined_score"] == 0.999
    # Mostly curated pathways and gene fusion, little experimental support:
    # a functional association, not evidence of physical binding.
    assert (q["channels"]["databases"], q["channels"]["experiments"]) == (0.978, 0.137)

    assertion = card.source_assertion_store.get(gapdhs["source_assertion_ids"][0])
    assert assertion["source"] == {
        "type": "database",
        "name": "STRING",
        "record_id": "9606.ENSP00000229270",
        "version": "12.0",
    }
    assert assertion["subject_ref"] == "string:9606.ENSP00000229270"
    assert assertion["asserted_value"]["row"]["escore"] == 0.137


def test_protein_absent_from_string_is_recorded_not_mixed(resolver):
    # STRING covers T. cruzi through strain CL Brener (Q4DV43), not P52270: the strain
    # network must not be attached silently to the species-level entry.
    card, _ = resolve_protein_card(
        "P52270", resolver, string={}, string_client=FixtureStringClient("temp_data")
    )
    assert card.quality["enrichments"] == [
        {
            "source": "STRING",
            "identifier": "P52270",
            "species": 5693,
            "status": "not_found",
        }
    ]
    assert card.relationships("functionally_associated_with") == []


def test_string_failure_is_recorded_and_the_card_is_still_built(resolver):
    client = FixtureStringClient("temp_data", failing={"P60174__9606"})
    with pytest.warns(EnrichmentFailedWarning, match="STRING could not be consulted"):
        card, _ = resolve_protein_card(
            "P60174", resolver, string={}, string_client=client
        )
    (enrichment,) = card.quality["enrichments"]
    assert enrichment["status"] == "error"
    assert card.id == "sabueso:protein:uniprot:P60174"


def test_all_structures_only_fetches_pdb_entries_and_records_each_outcome(resolver):
    card, _ = resolve_protein_card("P52270", resolver, structures="all")
    outcomes = {e["structure"]: e["status"] for e in card.quality["enrichments"]}
    # Only has_structure objects are fetched (never go:, pfam: or other knowledge refs).
    assert sorted(outcomes) == ["1CI1", "1SUX", "1TCD", "2OMA", "2V5B", "3Q37", "4HHP"]
    added = {pdb for pdb, status in outcomes.items() if status == "added"}
    assert added == {"1TCD", "1SUX"}  # the saved RCSB entries
    assert {s for pdb, s in outcomes.items() if pdb not in added} == {"not_found"}
