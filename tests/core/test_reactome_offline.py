"""Reactome: the pathways and reactions a protein takes part in (#83).

Fixture: Reactome 97's mapping of HsTIM (P60174): glycolysis and gluconeogenesis, two
reactions, and the paths up to top-level pathways.
"""

import pytest

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.reactome import FixtureReactomeClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        reactome=True,
        reactome_client=FixtureReactomeClient("temp_data"),
    )
    return card


def test_pathways_and_reactions_keep_reactomes_hierarchy(resolver):
    card = _card(resolver, "P60174")
    events = {
        r["object_ref"]: r["qualifiers"] for r in card.relationships("participates_in")
    }
    glycolysis = events["reactome:R-HSA-70171"]
    assert (glycolysis["kind"], glycolysis["name"], glycolysis["is_inferred"]) == (
        "pathway",
        "Glycolysis",
        False,
    )
    assert [e["name"] for e in glycolysis["ancestors"][0]] == [
        "Glycolysis",
        "Glucose metabolism",
        "Metabolism of carbohydrates and carbohydrate derivatives",
        "Metabolism",
    ]
    reactions = [q for q in events.values() if q["kind"] == "reaction"]
    assert len(reactions) == 2 and "ancestors" not in reactions[0]
    (sa_id,) = card.relationships("participates_in")[0]["source_assertion_ids"]
    assert card.source_assertion_store.get(sa_id)["source"]["version"] == "97"


def test_a_protein_reactome_does_not_map_is_not_stated(resolver):
    card = _card(resolver, "P52270")
    states = {
        (r["area"], r["source"]): r["state"] for r in card.knowledge_state()["rows"]
    }
    assert states[("relationships.participates_in", "Reactome")] == "not_stated"
