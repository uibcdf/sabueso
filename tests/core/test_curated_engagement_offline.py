"""Curated ligand engagement: residues a paper says a compound acts on (#61).

The observed site is real: PDBe-KB states that BTS contacts Arg71, Phe75 and Tyr102 of
TcTIM (P52270) in 1SUX. The curated statements below are constructed for the tests,
under placeholder DOIs, and claim nothing about the literature.
"""

import json

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient
from sabueso.tools.db.unichem import FixtureUniChemClient

PAPER = "doi:10.0000/constructed-engagement"


def _resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _tctim(**kwargs):
    card, _ = sabueso.resolve(
        "P52270",
        resolver=_resolver(),
        ligand_sites=True,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        **kwargs,
    )
    return card


@pytest.fixture(scope="module")
def bts():
    card, _ = sabueso.resolve(
        "pdb.ligand:BTS",
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    return card


def test_shared_residues_corroborate_the_observed_site(bts):
    card = _tctim()
    record = card.add_literature_engagement(
        bts, [71, 75, 102], "non_covalent", PAPER, "curator-a", method="mutagenesis"
    )
    assert record["outcome"] == "corroborates"
    assert record["shared_positions"] == [71, 75, 102]
    (rel,) = card.relationships("engages")
    assert rel["object_ref"] == "pdb.ligand:BTS"
    assert [r["residue"] for r in rel["qualifiers"]["residues"]] == ["R", "F", "Y"]
    view = card.ligand_sites()
    (curated,) = view["curated_engagements"]
    assert (curated["mechanism"], curated["publication"]) == ("non_covalent", PAPER)
    # The observed site stays as PDBe-KB states it, next to the curated one.
    assert any(i["ligand_ref"] == "pdb.ligand:BTS" for i in view["items"])


def test_other_residues_are_not_a_contradiction(bts):
    card = _tctim()
    record = card.add_literature_engagement(
        bts,
        [{"position": 15, "residue": "Cys"}],
        "covalent",
        PAPER + "-2",
        "curator-a",
        covalent_residue=15,
        method="mass spectrometry",
    )
    assert record["outcome"] == "not_comparable"
    assert not card.quality.get("conflicts")


def test_a_molecule_without_an_observed_site_is_new():
    card = _tctim()
    record = card.add_literature_engagement(
        {"inchikey": "AAAAAAAAAAAAAA-UHFFFAOYSA-N", "records": ["chembl:CHEMBL1"]},
        [15],
        "unspecified",
        PAPER,
        "curator-a",
    )
    assert record["outcome"] == "new"
    entities = card.entities()
    assert "inchikey:AAAAAAAAAAAAAA-UHFFFAOYSA-N" in entities


@pytest.mark.parametrize(
    "kwargs, error, message",
    [
        (dict(residues=[{"position": 15, "residue": "A"}]), SchemaError, "is C"),
        (dict(residues=[999]), SchemaError, "outside the sequence"),
        (dict(residues=[]), SchemaError, "at least one residue"),
        (dict(mechanism="covalent"), SchemaError, "covalent_residue"),
        (dict(covalent_residue=15), SchemaError, "covalent engagements only"),
        (dict(mechanism="glue"), ArgumentError, None),
    ],
)
def test_malformed_engagements_are_refused(bts, kwargs, error, message):
    card = _tctim()
    args = dict(residues=[15], mechanism="non_covalent") | kwargs
    with pytest.raises(error, match=message):
        card.add_literature_engagement(
            bts, args.pop("residues"), args.pop("mechanism"), PAPER, "curator-a", **args
        )
    assert not card.relationships("engages")


def test_an_engagement_survives_rebuilds_and_storage(bts, tmp_path):
    card = _tctim()
    record = card.add_literature_engagement(
        bts, [15], "covalent", PAPER, "curator-a", covalent_residue=15
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    (saved,) = store.records()
    assert (saved["kind"], saved["mechanism"], saved["covalent_residue"]) == (
        "engagement",
        "covalent",
        15,
    )
    rebuilt = _tctim(curations=store)
    assert rebuilt.source_assertion_store.get(
        record["source_assertion_id"]
    ) == card.source_assertion_store.get(record["source_assertion_id"])
    again = Card.from_dict(json.loads(json.dumps(rebuilt.to_dict())))
    assert (
        again.ligand_sites()["curated_engagements"]
        == (rebuilt.ligand_sites()["curated_engagements"])
    )
