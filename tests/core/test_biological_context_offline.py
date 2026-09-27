"""Biological context of a target, curated from publications (#60, step 1).

The statements below are invented for the test and attached to a placeholder
publication; they are not knowledge about TcTIM.
"""

import warnings

import pytest

import sabueso
from sabueso.core.errors import SchemaError
from sabueso.resolver import EntityResolver, FixtureUniProtClient

PAPER = "doi:10.0000/example.0001"


@pytest.fixture()
def card():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    return sabueso.resolve("P52270", resolver=resolver)[0]


def _curate(card, field_path, value, locator="Fig. 1"):
    return card.add_literature_assertion(
        field_path, value, PAPER, curator="tester", locator=locator
    )


def test_each_field_takes_stated_text_items(card):
    record = _curate(
        card,
        "annotations.essentiality",
        {
            "method": "RNAi knockdown",
            "phenotype": "  growth arrest after 48 h ",
            "stage": "epimastigote",
            "call": "essential",
        },
    )
    assert record["outcome"] == "new"
    (item,) = card.get("annotations.essentiality")["value"]
    # Kept as stated, trimmed: never turned into a category.
    assert item["phenotype"] == "growth arrest after 48 h"
    assert item["call"] == "essential"
    _curate(
        card,
        "annotations.stage_expression",
        {"stage": "amastigote", "observation": "protein detected", "method": "western"},
    )
    _curate(
        card,
        "annotations.accessibility",
        {"compartment": "glycosome", "exposure": "not surface-exposed"},
    )
    _curate(
        card,
        "annotations.metabolic_role",
        {"pathway": "glycolysis", "role": "required", "stage": "trypomastigote"},
    )


@pytest.mark.parametrize(
    "field_path, value",
    [
        ("annotations.essentiality", {"method": "RNAi"}),  # no phenotype
        (
            "annotations.essentiality",
            {"method": "RNAi", "phenotype": "lethal", "x": "1"},
        ),
        ("annotations.stage_expression", {"stage": "amastigote", "observation": ""}),
        ("annotations.accessibility", {"compartment": 3}),
        ("annotations.metabolic_role", "glycolysis"),
    ],
)
def test_what_does_not_fit_is_refused(card, field_path, value):
    with pytest.raises(SchemaError):
        _curate(card, field_path, value)


def test_the_same_condition_is_compared(card):
    first = {"method": "RNAi", "phenotype": "lethal", "stage": "epimastigote"}
    _curate(card, "annotations.essentiality", first)
    same = _curate(card, "annotations.essentiality", dict(first), locator="Fig. 2")
    assert same["outcome"] == "corroborates"
    other = {"method": "RNAi", "phenotype": "no growth defect", "stage": "epimastigote"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        differs = _curate(card, "annotations.essentiality", other, locator="Fig. 3")
    assert differs["outcome"] == "differs"
    # Another stage is another statement, not a disagreement.
    stage = {"method": "RNAi", "phenotype": "no growth defect", "stage": "amastigote"}
    assert _curate(card, "annotations.essentiality", stage)["outcome"] == "new"


def test_uncurated_context_is_not_queried_never_not_stated(card):
    def states():
        return {
            r["area"]: r
            for r in card.knowledge_state()["rows"]
            if r["area"].startswith(
                (
                    "annotations.essentiality",
                    "annotations.stage_expression",
                    "annotations.accessibility",
                    "annotations.metabolic_role",
                )
            )
        }

    before = states()
    assert {r["state"] for r in before.values()} == {"not_queried"}
    assert {r["source"] for r in before.values()} == {"Literature"}
    assert before["annotations.essentiality"]["basis"] == {"route": "curation"}
    _curate(card, "annotations.essentiality", {"method": "RNAi", "phenotype": "lethal"})
    after = states()
    assert after["annotations.essentiality"]["state"] == "known"
    assert after["annotations.metabolic_role"]["state"] == "not_queried"


def test_a_packet_carries_the_biological_context(card):
    _curate(
        card,
        "annotations.metabolic_role",
        {"pathway": "glycolysis", "role": "required"},
    )
    query = sabueso.KnowledgeQuery("P52270", aspects=["biological_context"])
    packet = sabueso.compose_packet(query, card)
    facts = packet.facts["biological_context"]["subject"]
    assert facts["annotations.metabolic_role"]["value"] == [
        {"pathway": "glycolysis", "role": "required"}
    ]
    unknown = {r["area"] for r in packet.unknowns["subject"]["rows"]}
    assert "annotations.essentiality" in unknown
    assert "annotations.metabolic_role" not in unknown
