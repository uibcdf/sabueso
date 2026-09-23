"""Sequence variants and mutagenesis (uibcdf/sabueso#33).

Frozen UniProt entries (release 2026_03): human TIM P60174 (natural variants), mu-opioid
receptor P35372 and hexokinase-2 P52789 (mutagenesis).
"""

import json
from pathlib import Path

import pytest

from sabueso import resolve_protein_card
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

NATURAL_VARIANT = "features_positional.natural_variant"
MUTAGENESIS = "features_positional.mutagenesis"


def _features(accession, field_path):
    entry = json.loads(Path(f"temp_data/{accession}.json").read_text(encoding="utf-8"))
    return map_protein(entry, "2026-09-23")["features"].get(field_path, [])


def _at(items, position):
    return next(i for i in items if i["location"]["sequence"]["start"] == position)


def test_a_variant_keeps_its_substitution_identifiers_and_stated_effect():
    variants = _features("P60174", NATURAL_VARIANT)
    assert len(variants) == 8
    # Glu105Asp is the only one of the eight whose description states an effect on the
    # homodimer; the others state only the disease, or thermolability.
    e105d = _at(variants, 105)
    assert e105d["substitution"] == {"original": "E", "alternatives": ["D"]}
    assert e105d["feature_id"] == "VAR_007536"
    assert e105d["cross_references"] == [{"database": "dbSNP", "id": "rs121964845"}]
    assert "changed protein homodimerization activity" in e105d["description"]
    assert "no effect on triose-phosphate isomerase activity" in e105d["description"]


def test_the_stated_effect_is_kept_verbatim_and_never_classified():
    variants = _features("P60174", NATURAL_VARIANT)
    # Thermolability is stated in free text; Sabueso does not turn it into a category.
    thermolabile = [v for v in variants if "thermolabile" in v["description"]]
    assert {v["location"]["sequence"]["start"] for v in thermolabile} == {123, 241}
    assert set(_at(variants, 123)) <= {
        "location",
        "description",
        "substitution",
        "feature_id",
        "cross_references",
    }


def test_variants_carry_the_evidence_of_their_own_assertion():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = resolve_protein_card("P60174", resolver)
    node = card.get(NATURAL_VARIANT)
    assert len(node["value"]) == 8
    by_value = {
        json.dumps(
            card.source_assertion_store.get(i)["asserted_value"], sort_keys=True
        ): i
        for i in node["source_assertion_ids"]
    }
    e105d = _at(node["value"], 105)
    assertion = card.source_assertion_store.get(
        by_value[json.dumps(e105d, sort_keys=True)]
    )
    pubmed = [
        e["id"]
        for e in assertion["source_metadata"]["eco"]
        if e.get("source") == "PubMed"
    ]
    assert len(pubmed) == 4
    assert all(e["code"] == "ECO:0000269" for e in assertion["source_metadata"]["eco"])


@pytest.mark.parametrize(
    "accession, position, original, alternatives, effect",
    [
        ("P35372", 142, "C", ["A", "S"], "Abolishes ligand binding"),
        ("P35372", 273, "K", ["A"], "Impairs interaction with calmodulin"),
        ("P52789", 209, "D", ["A"], "Decreased hexokinase activity"),
    ],
)
def test_mutagenesis_keeps_every_alternative_residue_stated(
    accession, position, original, alternatives, effect
):
    item = _at(_features(accession, MUTAGENESIS), position)
    assert item["substitution"] == {"original": original, "alternatives": alternatives}
    assert effect in item["description"]
    assert "feature_id" not in item  # UniProt gives mutagenesis no accession


def test_the_two_kinds_of_statement_stay_apart():
    # An observed variant and an experiment the authors performed are different claims.
    assert _features("P60174", MUTAGENESIS) == []
    assert _features("P35372", MUTAGENESIS) != []
    assert _features("P35372", NATURAL_VARIANT) != []
    assert _features("P52270", NATURAL_VARIANT) == []  # TcTIM has neither
