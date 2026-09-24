"""ChEMBL bioactivities as protein–molecule relationships (uibcdf/sabueso#23).

Frozen public ChEMBL_37 responses for TcTIM (CHEMBL5834, UniProt P52270) and HsTIM
(CHEMBL4880, UniProt P60174), retrieved 2026-09-23.
"""

import pytest
import pyunitwizard as puw

from sabueso import resolve_protein_card
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
)
from sabueso.core.bioactivities import (
    classify_measurement,
    single_point_concentration,
)
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient

TCTIM, HSTIM = "P52270", "P60174"


@pytest.fixture
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, **chembl):
    card, _ = resolve_protein_card(
        accession,
        resolver,
        chembl=chembl,
        chembl_client=FixtureChEMBLClient("temp_data"),
    )
    return card


def _molecules(view):
    return {item["molecule_ref"]: item for item in view["items"]}


def test_every_activity_record_is_a_supported_relationship(resolver):
    card = _card(resolver, TCTIM)
    (enrichment,) = card.quality["enrichments"]
    assert enrichment == {
        "source": "ChEMBL",
        "target": "CHEMBL5834",  # from the UniProt ChEMBL cross-reference
        "status": "added",
        "version": "ChEMBL_37",
        "count": 493,
        "total_count": 493,
        "truncated": False,
    }

    relationships = card.relationships("has_bioactivity")
    assert len(relationships) == 493  # one per measurement, none merged away
    ic50 = next(
        r
        for r in relationships
        if r["object_ref"] == "chembl:CHEMBL567076"
        and r["qualifiers"]["measurement"]["type"] == "IC50"
    )
    q = ic50["qualifiers"]
    assert (q["measurement"]["value"], q["measurement"]["units"]) == (6500.0, "nM")
    assert q["measurement"]["pchembl"] == 5.19
    assert (q["assay"]["relationship_type"], q["assay"]["confidence_score"]) == ("D", 9)

    activity_sa, assay_sa = (
        card.source_assertion_store.get(i) for i in ic50["source_assertion_ids"]
    )
    assert activity_sa["source"] == {
        "type": "database",
        "name": "ChEMBL",
        "record_id": "CHEMBL5834",
        "version": "ChEMBL_37",
    }
    assert activity_sa["asserted_value"]["activity"]["standard_value"] == "6500.0"
    assert assay_sa["field_path"] == "relationships.has_bioactivity.assay"
    assert assay_sa["subject_ref"] == "chembl:CHEMBL1049665"
    # Assay records are stated once per assay, not once per activity.
    assays = card.source_assertion_store.find_by_field(
        "relationships.has_bioactivity.assay"
    )
    assert len(assays) == 13


def test_derived_classes_follow_the_stated_rule(resolver):
    view = _card(resolver, TCTIM).bioactivities()
    rule = view["classification"]
    assert rule["rule"] == "bioactivity_class@2"
    # Thresholds are recorded as quantities, never as numbers named after a unit (#32).
    assert rule["parameters"]["active_max"] == {"value": 10.0, "unit": "micromolar"}
    assert rule["parameters"]["weak_max"] == {"value": 100.0, "unit": "micromolar"}
    assert rule["parameters"]["single_point_min"] == {"value": 50.0, "unit": "percent"}

    molecules = _molecules(view)
    assert len(molecules) == 256
    # IC50 6.5 µM (active) and Kd 10.4 µM (weak): the strongest class is kept.
    assert molecules["chembl:CHEMBL567076"]["class"] == "active"
    assert molecules["chembl:CHEMBL567076"]["classes"] == {"active": 1, "weak": 1}
    assert molecules["chembl:CHEMBL1630897"]["class"] == "weak"  # IC50 13 µM
    # The whole set is kept, negatives and "Not Determined" included.
    classes = [x["class"] for i in view["items"] for x in i["measurements"]]
    assert classes.count("not_determined") == 185
    assert classes.count("inactive") == 202
    # One paper holds most of the data: the bias is visible.
    assert next(iter(view["documents"].items())) == ("CHEMBL1629474", 459)


@pytest.mark.parametrize(
    "measurement, description, expected",
    [
        ({"type": "IC50", "relation": "=", "value": 990.0, "units": "nM"}, "", "active"),
        ({"type": "Ki", "relation": "=", "value": 15000, "units": "nM"}, "", "weak"),
        ({"type": "IC50", "relation": ">", "value": 1e6, "units": "nM"}, "", "inactive"),
        ({"type": "IC50", "relation": ">", "value": 5e4, "units": "nM"}, "", "inconclusive"),
        ({"type": "Inhibition", "value": 62, "units": "%"}, "at 100 uM", "weak"),
        ({"type": "Inhibition", "value": 12, "units": "%"}, "at 100 uM", "inactive"),
        ({"type": "Inhibition", "value": 70, "units": "%"}, "at 400 uM", "inconclusive"),
        ({"type": "Inhibition", "value": 70, "units": "%"}, "no concentration", "inconclusive"),
        ({"type": "Inhibition", "value": None, "activity_comment": "Not Determined"}, "", "not_determined"),
        ({"type": "Km", "relation": "=", "value": 300, "units": "nM"}, "", "unclassified"),
    ],
)  # fmt: skip
def test_measurement_classification(measurement, description, expected):
    assert classify_measurement(measurement, description)["class"] == expected


def test_test_concentration_is_read_from_the_assay_text():
    text = "Inhibition of Trypanosoma cruzi triosephosphate isomerase at 400 uM after 2 hrs"
    # Kept in the stated unit, read through the explicit ChEMBL vocabulary.
    assert single_point_concentration(text) == {"value": 400.0, "unit": "micromolar"}
    assert single_point_concentration("at 50 nM") == {
        "value": 50.0,
        "unit": "nanomolar",
    }
    assert single_point_concentration("after 2 hrs") is None


def test_thresholds_are_parameters_and_are_recorded(resolver):
    view = _card(resolver, TCTIM).bioactivities(
        thresholds={"active_max": puw.quantity(20.0, "uM")}
    )
    assert view["classification"]["parameters"]["active_max"] == {
        "value": 20.0,
        "unit": "micromolar",
    }
    assert _molecules(view)["chembl:CHEMBL1630897"]["class"] == "active"


def test_homology_assigned_assays_are_excluded_and_reported(resolver):
    view = _card(resolver, HSTIM).bioactivities()
    # All HsTIM Ki values were measured on rabbit TIM or TIM of unknown organism and
    # assigned to the human target by homology (ChEMBL relationship type "H").
    assert len(view["excluded"]) == 8
    assert {e["reason"] for e in view["excluded"]} == {"target_assignment:H"}
    assert "Oryctolagus cuniculus" in {e["assay_organism"] for e in view["excluded"]}
    assert view["scope"] == {"target_assignment": "D"}
    assert len(view["items"]) == 26

    everything = _card(resolver, HSTIM).bioactivities(include_indirect=True)
    assert everything["excluded"] == []
    assert sum(len(i["measurements"]) for i in everything["items"]) == 36

    flags = {f for i in view["items"] for x in i["measurements"] for f in x["flags"]}
    assert "assay_organism_unknown_origin" in flags  # "TPI (unknown origin)" assays
    assert "data_validity:Outside typical range" in flags


def test_molecules_measured_on_both_tims_expose_selectivity(resolver):
    tc = _molecules(_card(resolver, TCTIM).bioactivities())
    hs = _molecules(_card(resolver, HSTIM).bioactivities())
    shared = set(tc) & set(hs)
    assert len(shared) == 14
    # Active on TcTIM (IC50 6.5 µM), inactive on HsTIM (IC50 > 1 mM).
    brevifolin = "chembl:CHEMBL567076"
    assert (tc[brevifolin]["class"], hs[brevifolin]["class"]) == ("active", "inactive")


def test_chembl_outcomes_are_recorded_and_never_block_the_card(resolver):
    # The failure is recorded as data and shown to the user (uibcdf/sabueso#31).
    with pytest.warns(EnrichmentFailedWarning, match="ChEMBL could not be consulted"):
        card, _ = resolve_protein_card(
            TCTIM,
            resolver,
            chembl={},
            chembl_client=FixtureChEMBLClient("temp_data", failing={"CHEMBL5834"}),
        )
    (enrichment,) = card.quality["enrichments"]
    assert enrichment["status"] == "error"
    assert card.relationships("has_bioactivity") == []

    missing, _ = resolve_protein_card(
        TCTIM, resolver, chembl={}, chembl_client=FixtureChEMBLClient("/nonexistent")
    )
    assert missing.quality["enrichments"][0]["status"] == "not_found"


def test_activity_limit_is_recorded_as_truncation(resolver):
    with pytest.warns(EnrichmentTruncatedWarning, match="returned 10 of 36 records"):
        card = _card(resolver, HSTIM, limit=10)
    (enrichment,) = card.quality["enrichments"]
    assert (enrichment["count"], enrichment["total_count"]) == (10, 36)
    assert enrichment["truncated"] is True


def test_the_same_threshold_in_another_unit_classifies_identically(resolver):
    card = _card(resolver, TCTIM)
    in_uM = card.bioactivities(thresholds={"active_max": puw.quantity(20.0, "uM")})
    in_nM = card.bioactivities(thresholds={"active_max": puw.quantity(20000.0, "nM")})
    assert _molecules(in_uM) == _molecules(in_nM)


@pytest.mark.parametrize(
    "thresholds",
    [
        {"active_max_uM": 20.0},  # the old unit-in-name key
        {"active_max": 20.0},  # a bare number: its unit would be a guess
        {"active_max": "20 nm"},  # a string quantity, but a length
        {"single_point_min": puw.quantity(5.0, "uM")},
    ],
)
def test_thresholds_must_be_quantities_of_the_right_dimension(resolver, thresholds):
    from sabueso.core.errors import ArgumentError

    with pytest.raises(ArgumentError):
        _card(resolver, TCTIM).bioactivities(thresholds=thresholds)


def test_a_single_point_test_concentration_is_a_quantity(resolver):
    derived = classify_measurement(
        {"type": "Inhibition", "value": 80.0, "units": "%", "relation": "="},
        "Inhibition of TcTIM at 400 uM",
    )
    # IC50 <= 400 uM: an upper bound beyond weak_max cannot decide, so inconclusive.
    assert derived["class"] == "inconclusive"
    assert puw.get_value(derived["test_concentration"], to_unit="uM") == 400.0


def test_a_threshold_may_be_any_quantity_form_including_a_string(resolver):
    card = _card(resolver, TCTIM)
    as_string = card.bioactivities(thresholds={"active_max": "20 uM"})
    as_pint = card.bioactivities(thresholds={"active_max": puw.quantity(20.0, "uM")})
    assert _molecules(as_string) == _molecules(as_pint)


def test_conversions_carry_no_floating_point_noise():
    from sabueso.core.quantities import normalized_measurement

    assert normalized_measurement(33.0, "uM") == {"value": 33000.0, "unit": "nanomolar"}
    assert normalized_measurement(5.0, "pM") == {"value": 0.005, "unit": "nanomolar"}
    assert normalized_measurement(1.5, "mM") == {
        "value": 1500000.0,
        "unit": "nanomolar",
    }


def test_each_measurement_knows_its_publication(resolver):
    card = _card(resolver, TCTIM)
    documents = [
        r["qualifiers"]["document"] for r in card.relationships("has_bioactivity")
    ]
    # ChEMBL_37 states a PubMed id for every document behind the TcTIM measurements.
    assert all(d["pubmed"] and d["id"] for d in documents)
    assert len({d["pubmed"] for d in documents}) == 5  # the five TcTIM documents
    pubs = {p["publication_ref"]: p for p in card.literature()["publications"]}
    assert sum(p["measurements"] for p in pubs.values()) == len(documents)
