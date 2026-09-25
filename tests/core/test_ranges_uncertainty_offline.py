"""Ranges and stated uncertainty in bioactivity measurements (uibcdf/sabueso#37).

ChEMBL_37 states no range: ``standard_upper_value`` is null in all 24,527,044 of its
activities (ChEMBL API, ``standard_upper_value__isnull=true``, 2026-09-25). The ChEMBL
range below is therefore constructed. It is a real TcTIM activity with an upper end
added, and it guards the mapping for a release that states ranges. Ranges and
uncertainties read in papers are the curated case.
"""

import copy
import json
import shutil
from pathlib import Path

import pytest
import pyunitwizard as puw

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.core.bioactivities import BIOACTIVITY_CLASS_RULE, classify_measurement
from sabueso.core.card import Card
from sabueso.core.errors import SchemaError, StorageError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

PAPER = "pubmed:35189560"  # BTS on TcTIM: ChEMBL states IC50 = 33000 nM (24815542)
BTS_ACTIVITY = 24815542


def _resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _tctim(chembl_client):
    card, _ = sabueso.resolve(
        "P52270", resolver=_resolver(), chembl={}, chembl_client=chembl_client
    )
    return card


@pytest.fixture(scope="module")
def ranged_client(tmp_path_factory):
    """TcTIM's ChEMBL fixture with BTS's IC50 turned into the range 33-45 uM."""
    directory = tmp_path_factory.mktemp("chembl_range")
    (directory / "chembl").mkdir()
    for name in ("molecules.json",):
        shutil.copy(Path("temp_data/chembl") / name, directory / "chembl" / name)
    saved = json.loads(
        Path("temp_data/chembl/CHEMBL5834.json").read_text(encoding="utf-8")
    )
    (activity,) = [a for a in saved["activities"] if a["activity_id"] == BTS_ACTIVITY]
    assert (activity["standard_value"], activity["standard_units"]) == ("33000.0", "nM")
    activity["standard_upper_value"] = "45000.0"
    (directory / "chembl" / "CHEMBL5834.json").write_text(
        json.dumps(saved), encoding="utf-8"
    )
    return FixtureChEMBLClient(directory)


@pytest.fixture
def tctim():
    return _tctim(FixtureChEMBLClient("temp_data"))


@pytest.fixture(scope="module")
def bts():
    card, _ = sabueso.resolve(
        "pdb.ligand:BTS",
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    return card


def _measurement(card, activity_id):
    (rel,) = [
        r
        for r in card.relationships("has_bioactivity")
        if r["qualifiers"]["activity_id"] == activity_id
    ]
    return rel["qualifiers"]["measurement"]


# --- ChEMBL ranges ----------------------------------------------------------------------------


def test_a_chembl_range_keeps_both_ends_normalized_and_sealed(ranged_client):
    card = _tctim(ranged_client)
    m = _measurement(card, BTS_ACTIVITY)
    assert m["upper_value"] == 45000.0
    assert m["normalized_upper"] == {"value": 45000.0, "unit": "nanomolar"}
    # Every other measurement is unchanged: the key exists only for ranges.
    others = [
        r["qualifiers"]["measurement"]
        for r in card.relationships("has_bioactivity")
        if r["qualifiers"]["activity_id"] != BTS_ACTIVITY
    ]
    assert others and all("normalized_upper" not in o for o in others)

    data = json.loads(json.dumps(card.to_dict()))
    assert Card.from_dict(data).to_dict() == card.to_dict()
    for rel in data["relationship_store"]:
        if rel["qualifiers"].get("activity_id") == BTS_ACTIVITY:
            rel["qualifiers"]["measurement"]["normalized_upper"]["value"] = 4500.0
    with pytest.raises(StorageError):
        Card.from_dict(data)


def test_the_view_shows_the_range_and_classifies_it_by_its_band(ranged_client):
    card = _tctim(ranged_client)
    view = card.bioactivities(include_indirect=True)
    assert (
        view["classification"]["rule"]
        == BIOACTIVITY_CLASS_RULE
        == ("bioactivity_class@3")
    )
    (m,) = [
        x
        for item in view["items"]
        for x in item["measurements"]
        if x["activity_id"] == BTS_ACTIVITY
    ]
    assert puw.get_value(puw.convert(m["normalized_upper"], to_unit="micromolar")) == (
        pytest.approx(45.0)
    )
    # 33-45 uM lies within the weak band (10-100 uM).
    assert (m["class"], m["basis"]) == ("weak", "potency_range")
    (row,) = [
        r
        for r in card.table("bioactivities", include_indirect=True)
        if r["activity_id"] == BTS_ACTIVITY
    ]
    assert puw.is_quantity(row["normalized_upper"])


@pytest.mark.parametrize(
    "value, upper, relation, expected",
    [
        (33000.0, 45000.0, "=", "weak"),
        (1000.0, 5000.0, "=", "active"),
        (5000.0, 20000.0, "=", "inconclusive"),  # spans 10 uM
        (50000.0, 200000.0, "~", "inconclusive"),  # spans 100 uM
        (1000.0, 5000.0, "<", "inconclusive"),  # a bounded range is not read
    ],
)
def test_a_range_across_a_threshold_is_inconclusive(value, upper, relation, expected):
    measurement = {
        "type": "IC50",
        "relation": relation,
        "value": value,
        "upper_value": upper,
        "units": "nM",
    }
    # Cards written before schema 0.3.2 keep the upper end only verbatim: it is
    # normalized when read.
    assert classify_measurement(measurement)["class"] == expected


def test_a_range_takes_no_potency_checks():
    from sabueso.core.bioactivities import bioactivities_view

    def rel(activity_id, value, upper=None, pchembl=None):
        return {
            "id": f"REL_{activity_id}",
            "subject_ref": "uniprot:P00000",
            "predicate": "has_bioactivity",
            "object_ref": "chembl:CHEMBL1",
            "qualifiers": {
                "activity_id": activity_id,
                "measurement": {
                    "type": "IC50",
                    "relation": "=",
                    "value": value,
                    "upper_value": upper,
                    "units": "nM",
                    "pchembl": pchembl,
                },
                "assay": {"relationship_type": "D"},
                "document": {},
            },
            "source_assertion_ids": [],
        }

    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P00000"},
        relationship_store=[
            rel(1, 10.0, upper=20.0, pchembl=5.0),  # a single value would be 8.0
            rel(2, 10000.0),  # 3 orders from the lower end: not a slip, a range
        ],
    )
    flags = {
        m["activity_id"]: m["flags"]
        for item in bioactivities_view(card)["items"]
        for m in item["measurements"]
    }
    assert flags == {1: [], 2: []}


# --- curated ranges and uncertainty ---------------------------------------------------------


def test_a_curated_range_and_uncertainty_are_stated_and_sealed(tctim, bts):
    with pytest.warns(CuratedDisagreementWarning):
        record = tctim.add_literature_bioactivity(
            bts,
            "IC50",
            "33 uM",
            PAPER,
            "curator-a",
            "direct",
            upper_value="45 uM",
            uncertainty={
                "kind": "ci",
                "lower": "30 uM",
                "upper": "37 uM",
                "level": 0.95,
                "n": 3,
            },
        )
    # ChEMBL states this paper's measurement as the single value 33000 nM: a range read
    # in the same paper is a difference, never a corroboration of one end.
    assert record["outcome"] == "differs"
    assertion = tctim.source_assertion_store.get(record["source_assertion_id"])
    stated = assertion["asserted_value"]["measurement"]
    assert stated["upper"] == {"value": "45", "unit": "uM"}
    assert stated["uncertainty"] == {
        "kind": "ci",
        "lower": {"value": "30", "unit": "uM"},
        "upper": {"value": "37", "unit": "uM"},
        "level": 0.95,
        "n": 3,
    }
    m = tctim.relationship_store.get(record["relationship_id"])["qualifiers"][
        "measurement"
    ]
    assert m["normalized_upper"] == {"value": 45000.0, "unit": "nanomolar"}
    assert m["normalized_uncertainty"]["lower"] == {
        "value": 30000.0,
        "unit": "nanomolar",
    }
    again = Card.from_dict(json.loads(json.dumps(tctim.to_dict())))
    assert again.to_dict() == tctim.to_dict()
    (row,) = [r for r in tctim.table("bioactivities") if r["curated"]]
    assert row["uncertainty_kind"] == "ci" and row["uncertainty_level"] == 0.95
    assert puw.is_quantity(row["uncertainty_lower"])


def test_an_uncertainty_does_not_change_agreement(tctim, bts):
    # The paper reports 33 +/- 4 uM; ChEMBL recorded 33000 nM. Both read the same
    # number, which is what agreement is about.
    record = tctim.add_literature_bioactivity(
        bts,
        "IC50",
        "33 uM",
        PAPER,
        "curator-a",
        "direct",
        uncertainty={"kind": "sd", "value": "4 uM", "n": 3},
    )
    assert record["outcome"] == "corroborates"
    # 30 +/- 4 uM does not become agreement because 33 lies within the spread.
    with pytest.warns(CuratedDisagreementWarning):
        record = tctim.add_literature_bioactivity(
            bts,
            "IC50",
            "30 uM",
            PAPER,
            "curator-a",
            "direct",
            uncertainty={"kind": "sd", "value": "4 uM"},
        )
    assert record["outcome"] == "differs"


def test_the_uncertainty_is_part_of_the_statement(tctim, bts):
    plain = tctim.add_literature_bioactivity(
        bts, "IC50", "33 uM", PAPER, "curator-a", "direct"
    )
    with_sd = tctim.add_literature_bioactivity(
        bts,
        "IC50",
        "33 uM",
        PAPER,
        "curator-a",
        "direct",
        uncertainty={"kind": "sem", "value": "2 uM"},
    )
    assert plain["source_assertion_id"] != with_sd["source_assertion_id"]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"upper_value": "20 uM"}, "below its lower end"),
        ({"upper_value": "45000 nM"}, "same unit"),
        ({"upper_value": "45 uM", "relation": "<"}, "both of its ends"),
        ({"uncertainty": {"kind": "range", "value": "1 uM"}}, "Unknown uncertainty"),
        ({"uncertainty": {"kind": "sd"}}, "takes"),
        ({"uncertainty": {"kind": "sd", "value": "4 %"}}, "not the same kind"),
        ({"uncertainty": {"kind": "sd", "value": "-4 uM"}}, "negative"),
        (
            {"uncertainty": {"kind": "ci", "lower": "34 uM", "upper": "40 uM"}},
            "contain the value",
        ),
        (
            {
                "uncertainty": {
                    "kind": "ci",
                    "lower": "30 uM",
                    "upper": "40 uM",
                    "level": 95,
                }
            },
            "fraction",
        ),
        ({"uncertainty": {"kind": "sd", "value": "4 uM", "n": 0}}, "replicates"),
        ({"uncertainty": {"kind": "sd", "value": 4}}, "unit"),
    ],
)
def test_malformed_ranges_and_uncertainties_are_refused(tctim, bts, kwargs, message):
    before = copy.deepcopy(tctim.to_dict())
    with pytest.raises(SchemaError, match=message):
        tctim.add_literature_bioactivity(
            bts, "IC50", "33 uM", PAPER, "curator-a", "direct", **kwargs
        )
    assert tctim.to_dict() == before  # nothing was recorded


def test_the_curation_store_keeps_ranges_and_uncertainty(tmp_path, bts):
    card = _tctim(FixtureChEMBLClient("temp_data"))
    with pytest.warns(CuratedDisagreementWarning):
        record = card.add_literature_bioactivity(
            bts,
            "IC50",
            "33 uM",
            PAPER,
            "curator-a",
            "direct",
            upper_value="45 uM",
            uncertainty={"kind": "sd", "value": "4 uM", "n": 3},
            curated_at="2026-09-25",
        )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    (saved,) = store.records()
    assert saved["upper_value"] == {"value": "45", "unit": "uM"}
    assert saved["uncertainty"]["kind"] == "sd"
    with pytest.warns(CuratedDisagreementWarning):
        rebuilt, _ = sabueso.resolve(
            "P52270",
            resolver=_resolver(),
            chembl={},
            chembl_client=FixtureChEMBLClient("temp_data"),
            curations=store,
        )
    new = rebuilt.source_assertion_store.get(record["source_assertion_id"])
    assert new == card.source_assertion_store.get(record["source_assertion_id"])
