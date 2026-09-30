"""SAbDab: antibody structures of a protein, joined by stated chains (#83).

Fixtures: SAbDab2's annotations of 1YY9 (cetuximab–EGFR), 10BT (an antibody with a
hapten), 9IJR and 9IJS (an scFv bound to a GPR52–arrestin complex) and 9MQI (a
nanobody bound to the mu-opioid receptor, and a Fab bound to that nanobody).
"""

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.mappings.sabdab import map_complexes
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.sabdab import FixtureSAbDabClient, classic_id

FIELD = "annotations.antibody_complexes"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession, client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        sabdab=True,
        sabdab_client=client or FixtureSAbDabClient("temp_data"),
    )
    return card


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "SAbDab"]
    return record


def test_a_nanobody_joins_through_the_chain_uniprot_states(resolver):
    card = _card(resolver, "P35372")
    (item,) = card.get(FIELD)["value"]
    assert item["structure"] == "pdb:9MQI"
    assert item["heavy_chain"] == {"chain": "C", "entity": 2, "type": "H"}
    assert "light_chain" not in item  # a nanobody
    assert item["antigen_chains"] == ["A"]
    # The Fab of 9MQI binds the nanobody, not the receptor: it is not on the card.
    assert _record(card)["count"] == 1


def test_every_antigen_of_the_antibody_is_kept_and_marked(resolver):
    card = _card(resolver, "Q9Y2T5")
    items = card.get(FIELD)["value"]
    assert [i["structure"] for i in items] == ["pdb:9IJR", "pdb:9IJS"]
    antigens = items[0]["antigens"]
    assert [(a["name"], a["chain"], a["this_protein"]) for a in antigens] == [
        ("G-protein coupled receptor 52", "A", True),
        ("Beta-arrestin-1", "C", False),
    ]
    # An scFv: SAbDab names one PDB chain for both domains.
    assert items[0]["heavy_chain"]["chain"] == items[0]["light_chain"]["chain"] == "H"
    record = _record(card)
    assert (record["version"], len(record["checksum"])) == ("2.1.4", 64)


def test_a_hapten_on_a_chain_never_makes_a_protein_an_antigen():
    # 10BT: SAbDab gives the hapten the chain of the polymer it is attached to (A).
    entry = {
        "uniProtKBCrossReferences": [
            {
                "database": "PDB",
                "id": "10BT",
                "properties": [{"key": "Chains", "value": "A=1-100"}],
            }
        ]
    }
    record = FixtureSAbDabClient("temp_data").complexes(["10BT"])["record"]
    assert map_complexes(record, "X", entry, "fixture", "2.1.4")["fields"] == {}


def test_a_protein_without_antibody_structures_is_not_found(resolver):
    card = _card(resolver, "P60174")
    record = _record(card)
    assert record["status"] == "not_found"
    assert "antigen" in record["detail"]


def test_a_failing_source_is_an_error_not_an_absence(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver,
            "P35372",
            client=FixtureSAbDabClient("temp_data", failing={"9MQI"}),
        )
    assert _record(card)["status"] == "error"


def test_extended_pdb_ids_are_read_as_classic_ones():
    assert classic_id("pdb_00001yy9") == "1YY9"
    assert classic_id("1yy9") == "1YY9"
