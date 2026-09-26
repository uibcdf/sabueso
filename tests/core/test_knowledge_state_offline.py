"""Knowledge states: known, conflicting, not stated, not queried, unavailable (#56)."""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _states(card):
    return {(r["area"], r["source"]): r for r in card.knowledge_state()["rows"]}


def test_known_not_stated_and_not_queried_are_told_apart(resolver):
    card, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        chembl={},
        chembl_client=FixtureChEMBLClient("temp_data"),
    )
    states = _states(card)
    known = states[("annotations.subunit", "UniProt")]
    assert (known["state"], known["release"]) == ("known", "120")
    # UniProt release 120 was consulted and states no function for TcTIM.
    absent = states[("annotations.function", "UniProt")]
    assert (absent["state"], absent["release"], absent["count"]) == (
        "not_stated",
        "120",
        0,
    )
    chembl = states[("relationships.has_bioactivity", "ChEMBL")]
    assert (chembl["state"], chembl["release"], chembl["count"]) == (
        "known",
        "ChEMBL_37",
        493,
    )
    # Ligand sites were not requested: nothing is said about them.
    assert (
        states[("relationships.has_ligand_site", "PDBe-KB")]["state"] == "not_queried"
    )
    assert states[("relationships.interacts_with", "UniProt")]["state"] == "not_stated"
    assert card.knowledge_state()["rule"]["rule"] == "knowledge_state@2"


def test_a_failed_source_is_unavailable(resolver):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "P52270",
            resolver=resolver,
            chembl={},
            chembl_client=FixtureChEMBLClient("temp_data", failing={"CHEMBL5834"}),
        )
    row = _states(card)[("relationships.has_bioactivity", "ChEMBL")]
    assert (row["state"], row["basis"]["errors"]) == ("unavailable", 1)


def test_no_cross_reference_is_not_stated_with_its_reason(resolver):
    # Chimpanzee TIM has no ChEMBL cross-reference: ChEMBL was not asked, and the basis
    # says so. It is not "ChEMBL has no data".
    card, _ = sabueso.resolve(
        "P60175",
        resolver=resolver,
        chembl={},
        chembl_client=FixtureChEMBLClient("temp_data"),
    )
    row = _states(card)[("relationships.has_bioactivity", "ChEMBL")]
    assert row["state"] == "not_stated"
    assert "no ChEMBL cross-reference" in row["basis"]["detail"]


def test_a_disagreement_is_conflicting_for_every_source(resolver):
    card, _ = sabueso.resolve("P60174", resolver=resolver)
    with pytest.warns(CuratedDisagreementWarning):
        card.add_literature_assertion(
            "features_positional.natural_variant",
            {"start": 105, "substitution": {"original": "E", "alternatives": ["D"]}},
            "pubmed:18562316",
            "curator-a",
        )
    states = _states(card)
    for source in ("UniProt", "Literature"):
        assert states[("features_positional.natural_variant", source)]["state"] == (
            "conflicting"
        )


def test_a_molecule_card_reports_its_source_records():
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    card = single_molecule_card(
        chembl={
            "retrieved_at": "2026-02-01",
            "molecules": {"CHEMBL90555": load("temp_data/CHEMBL90555.json")},
        },
    )
    rows = card.knowledge_state()["rows"]
    assert {r["source"] for r in rows if r["state"] == "known"} >= {"ChEMBL"}
    assert not [r for r in rows if r["source"] == "UniProt"]


def test_the_table_is_flat(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    rows = card.table("knowledge_state")
    assert rows and all(isinstance(r["basis"], str) for r in rows)
    assert {r["state"] for r in rows} >= {"known", "not_stated", "not_queried"}
