"""Curated bioactivity measurements, compared with the ChEMBL record of the same paper
(uibcdf/sabueso#44).

BTS (CHEMBL1161789, PDB component BTS, InChIKey XBNHRNFODJOFRU-UHFFFAOYSA-N): ChEMBL_37
states one IC50 on TcTIM, 33000 nM (activity 24815542), from PubMed 35189560.
"""

import json

import pytest

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.core.card import Card
from sabueso.core.curation import molecule_identity
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

PAPER = "pubmed:35189560"
BTS_KEY = "XBNHRNFODJOFRU-UHFFFAOYSA-N"


@pytest.fixture(scope="module")
def clients():
    return dict(
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )


@pytest.fixture(scope="module")
def bts(clients):
    card, _ = sabueso.resolve("pdb.ligand:BTS", **clients)
    return card


@pytest.fixture
def tctim(clients):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve(
        "P52270", resolver=resolver, chembl={}, chembl_client=clients["chembl_client"]
    )
    return card


def test_the_molecule_keeps_its_inchikey_and_every_linked_record(bts):
    identity = molecule_identity(bts)
    assert identity["inchikey"] == BTS_KEY
    assert {"chembl:CHEMBL1161789", "pdb.ligand:BTS", "pubchem:162569"} <= set(
        identity["records"]
    )


@pytest.mark.parametrize("value", ["33 uM", "33000 nM", "0.033 mM"])
def test_the_same_value_from_the_same_paper_corroborates_chembl(tctim, bts, value):
    record = tctim.add_literature_bioactivity(
        bts, "IC50", value, PAPER, "curator-a", "direct", locator="Table 1"
    )
    assert record["outcome"] == "corroborates"
    (chembl,) = [tctim.relationship_store.get(i) for i in record["compared_with"]]
    assert chembl["qualifiers"]["activity_id"] == 24815542


def test_another_value_from_the_same_paper_differs_and_is_flagged(tctim, bts):
    with pytest.warns(CuratedDisagreementWarning):
        record = tctim.add_literature_bioactivity(
            bts, "IC50", "30 uM", PAPER, "curator-a", "direct"
        )
    assert record["outcome"] == "differs"
    (conflict,) = tctim.quality["conflicts"]
    assert conflict["type"] == "curated_difference"
    # ChEMBL's measurement stays as ChEMBL states it.
    (chembl,) = [tctim.relationship_store.get(i) for i in record["compared_with"]]
    assert chembl["qualifiers"]["measurement"]["value"] == 33000.0


def test_a_measurement_chembl_does_not_hold_is_new(tctim, bts):
    record = tctim.add_literature_bioactivity(
        bts, "IC50", "25 uM", "pubmed:15321726", "curator-a", "direct"
    )
    assert (record["outcome"], record["compared_with"]) == ("new", [])


def test_the_molecule_may_be_named_by_any_of_its_records(tctim, bts):
    # The curator names BTS by its PubChem CID; ChEMBL by its ChEMBL id. One molecule.
    identity = molecule_identity(bts)
    record = tctim.add_literature_bioactivity(
        identity, "IC50", "33 uM", PAPER, "curator-a", "direct", locator="Table 2"
    )
    assert record["outcome"] == "corroborates"


def test_curated_measurements_join_the_bioactivity_view(tctim, bts):
    tctim.add_literature_bioactivity(bts, "IC50", "33 uM", PAPER, "curator-a", "direct")
    tctim.add_literature_bioactivity(
        bts, "IC50", "25 uM", "pubmed:15321726", "curator-a", "homology"
    )
    view = tctim.bioactivities()
    (item,) = [i for i in view["items"] if i["molecule_ref"] == "chembl:CHEMBL1161789"]
    curated = [m for m in item["measurements"] if m["curated"]]
    assert len(curated) == 1 and curated[0]["class"] == "weak"
    # Measured on an ortholog: left out by default, as ChEMBL's homology assignments are.
    assert [e for e in view["excluded"] if str(e["activity_id"]).startswith("curated:")]
    everything = tctim.bioactivities(include_indirect=True)
    (item,) = [
        i for i in everything["items"] if i["molecule_ref"] == "chembl:CHEMBL1161789"
    ]
    assert len([m for m in item["measurements"] if m["curated"]]) == 2


def test_curated_measurements_survive_rebuilds_with_the_same_outcome(
    tctim, bts, clients, tmp_path
):
    first = tctim.add_literature_bioactivity(
        bts, "IC50", "33 uM", PAPER, "curator-a", "direct", locator="Table 1"
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(tctim)
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    rebuilt, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        chembl={},
        chembl_client=clients["chembl_client"],
        curations=store,
    )
    (again,) = rebuilt.quality["curation"]
    assert again["source_assertion_id"] == first["source_assertion_id"]
    assert again["outcome"] == "corroborates"
    assert rebuilt.quality["curation_store"]["changed"] == []
    loaded = Card.from_dict(json.loads(json.dumps(rebuilt.to_dict())))
    assert loaded.quality["curation"] == rebuilt.quality["curation"]


@pytest.mark.parametrize(
    "change",
    [
        {"target_assignment": "maybe"},
        {"relation": "about"},
        {"measurement_type": ""},
        {"molecule": 42},
    ],
)
def test_wrong_arguments_are_refused(tctim, bts, change):
    kwargs = dict(
        molecule=bts,
        measurement_type="IC50",
        value="33 uM",
        publication=PAPER,
        curator="curator-a",
        target_assignment="direct",
    )
    kwargs.update(change)
    with pytest.raises(ArgumentError):
        tctim.add_literature_bioactivity(**kwargs)


@pytest.mark.parametrize("value", ["33", 33.0, "33 seconds"])
def test_a_value_needs_a_concentration_or_percentage_unit(tctim, bts, value):
    with pytest.raises(SchemaError):
        tctim.add_literature_bioactivity(
            bts, "IC50", value, PAPER, "curator-a", "direct"
        )


def test_a_protein_card_is_not_a_molecule(tctim):
    with pytest.raises(SchemaError):
        tctim.add_literature_bioactivity(
            tctim, "IC50", "33 uM", PAPER, "curator-a", "direct"
        )
