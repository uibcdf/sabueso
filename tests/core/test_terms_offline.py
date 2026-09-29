"""What may be done with the knowledge: the terms its sources state (#29)."""

import json
import warnings
from datetime import date

import pytest

import sabueso
from sabueso.core import terms as terms_module
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.terms import source_terms, verdict


@pytest.fixture(scope="module")
def hstim():
    return Card.from_dict(
        json.loads(
            open(
                "temp_data/frozen_cards/schema_0.3.6__P60174.json", encoding="utf-8"
            ).read()
        )
    )


@pytest.fixture(scope="module")
def tctim():
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.bindingdb import FixtureBindingDBClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.pubchem_bioassay import FixturePubChemBioAssayClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data"),
            ),
            chembl={},
            chembl_client=FixtureChEMBLClient("temp_data"),
            bindingdb={},
            bindingdb_client=FixtureBindingDBClient("temp_data"),
            unichem_client=FixtureUniChemClient("temp_data"),
            pubchem_bioassay=True,
            pubchem_bioassay_client=FixturePubChemBioAssayClient("temp_data"),
        )
    return card


def test_every_source_on_a_card_has_its_terms_recorded(hstim, tctim):
    known = set(source_terms())
    for card in (hstim, tctim):
        names = {
            (sa.get("source") or {}).get("name")
            for sa in card.source_assertion_store.to_list()
        }
        assert names <= known, names - known


@pytest.mark.parametrize(
    "use, obligations",
    [
        ("internal_research", []),
        ("academic_publication", ["attribution"]),
        ("redistribution", ["attribution", "share_alike"]),
        ("derived_dataset", ["attribution", "share_alike"]),
        ("commercial_product", ["attribution", "share_alike"]),
    ],
)
def test_a_share_alike_source_is_allowed_with_its_obligations(use, obligations):
    answer = verdict("ChEMBL", use, today=date(2026, 9, 29))
    assert answer["verdict"] == "allowed"
    assert answer["obligations"] == obligations
    assert answer["licence"] == "CC-BY-SA-3.0"
    assert answer["statement"].startswith("https://")
    assert answer["reviewed"] == "2026-09-29"


def test_unknown_is_its_own_answer_never_no_restriction():
    assert verdict("Nowhere", "commercial_product") == {
        "verdict": "unknown",
        "reason": "no_terms_recorded",
    }
    for name in ("PubChem BioAssay", "Literature"):
        answer = verdict(name, "internal_research")
        assert (answer["verdict"], answer["reason"]) == ("unknown", "terms_per_record")


def test_a_non_commercial_licence_restricts_a_commercial_product(monkeypatch):
    stated = {
        "Somewhere": {
            "licence": "CC-BY-NC-4.0",
            "attribution": "Somewhere",
            "statement": "https://example.org/terms",
            "reviewed": "2026-09-29",
        }
    }
    monkeypatch.setattr(terms_module, "source_terms", lambda: stated)
    answer = verdict("Somewhere", "commercial_product")
    assert (answer["verdict"], answer["reason"]) == (
        "restricted",
        "non_commercial_licence",
    )
    assert answer["statement"] == "https://example.org/terms"
    assert verdict("Somewhere", "academic_publication")["verdict"] == "allowed"


def test_an_old_review_is_flagged():
    assert "review_due" not in verdict("UniProt", "redistribution", date(2026, 10, 1))
    assert verdict("UniProt", "redistribution", date(2028, 1, 1))["review_due"]


def test_what_remains_for_a_commercial_product_molecule_by_molecule(tctim):
    report = tctim.terms("commercial_product")
    assert report["rule"] == "terms_propagation@1"
    assert "not legal advice" in report["disclaimer"]
    (card,) = report["cards"]
    molecules = {
        ref: entry
        for ref, entry in card["objects"].items()
        if "has_bioactivity" in entry["predicates"]
    }
    # Every assay in the fixture was deposited in PubChem by ChEMBL: each result is
    # judged by ChEMBL's terms, so every measured molecule may be used, with
    # attribution and share-alike.
    assert molecules and {e["status"] for e in molecules.values()} == {"complete"}
    label = "PubChem BioAssay (deposited by ChEMBL)"
    assert report["sources"][label]["verdict"] == "allowed"
    assert report["sources"][label]["basis"] == {
        "source": "PubChem BioAssay",
        "depositor": "ChEMBL",
        "terms_of": "ChEMBL",
    }
    assert {"attribution", "share_alike"} <= set(report["obligations"])
    assert any("ChEMBL" in text for text in report["attribution"])


def test_a_depositor_whose_terms_are_not_recorded_stays_unknown():
    answer = terms_module.labelled_verdict(
        "PubChem BioAssay (deposited by Somebody)", "commercial_product"
    )
    assert (answer["verdict"], answer["reason"]) == (
        "unknown",
        "depositor_terms_not_recorded",
    )


def test_a_deck_keeps_only_what_is_admissible_and_says_why(hstim, tctim, monkeypatch):
    # Without ChEMBL's terms on record, the TcTIM card's bioactivities are unknown.
    stated = {k: v for k, v in source_terms().items() if k != "ChEMBL"}
    monkeypatch.setattr(terms_module, "source_terms", lambda: stated)
    deck = Deck([hstim, tctim])
    kept = deck.admissible("commercial_product")
    assert tctim.id not in [c.id for c in kept.cards]
    assert {
        "candidate": tctim.id,
        "reason": "partially_admissible",
        "by": "terms_propagation@1",
    } in kept.meta["excluded"]
    assert kept.meta["operations"][-1]["operation"] == "admissible"


def test_a_use_is_one_of_the_named_ones(hstim):
    with pytest.raises(ArgumentError):
        hstim.terms("anything")


# --- Terms profiles (#94) --------------------------------------------------------------


def _tctim(**options):
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.pubchem_bioassay import FixturePubChemBioAssayClient

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(
                FixtureUniProtClient("temp_data"),
                rcsb_client=FixtureRCSBClient("temp_data"),
            ),
            chembl={},
            chembl_client=FixtureChEMBLClient("temp_data"),
            pubchem_bioassay=True,
            pubchem_bioassay_client=FixturePubChemBioAssayClient("temp_data"),
            **options,
        )
    return card


@pytest.mark.parametrize("profile", ["commercial", "non_commercial"])
def test_a_profile_keeps_the_records_whose_terms_allow_its_use(profile):
    card = _tctim(terms=profile)
    assert card.quality["terms_profile"] == {
        "profile": profile,
        "use": terms_module.PROFILES[profile],
        "rule": "terms_profile@1",
        "excluded": [],
    }
    # PubChem BioAssay is asked: its results deposited by ChEMBL are kept.
    assert any(
        r["qualifiers"].get("source") == "PubChem BioAssay"
        for r in card.relationships("has_bioactivity")
    )
    assert card.terms(terms_module.PROFILES[profile])["cards"][0]["status"] == (
        "complete"
    )


def test_a_record_of_a_depositor_without_recorded_terms_is_left_out():
    profile = terms_module.TermsProfile("commercial")
    assert profile.admits("PubChem BioAssay")  # asked, then judged record by record
    assert profile.admits_record("PubChem BioAssay", "ChEMBL")
    assert not profile.admits_record("PubChem BioAssay", "Somebody")
    assert not profile.admits_record("PubChem BioAssay", "Somebody")
    assert profile.record()["excluded_records"] == [
        {
            "source": "PubChem BioAssay",
            "depositor": "Somebody",
            "reason": "depositor_terms_not_recorded",
            "count": 2,
        }
    ]
    # A source whose terms are each record's, with no depositor known, is not asked.
    assert not profile.admits("Literature")
    assert profile.record()["excluded"] == [
        {"source": "Literature", "reason": "terms_per_record"}
    ]


def test_without_a_profile_nothing_is_excluded():
    card = _tctim()
    assert "terms_profile" not in card.quality
    assert any(
        r["qualifiers"].get("source") == "PubChem BioAssay"
        for r in card.relationships("has_bioactivity")
    )


def test_a_profile_is_one_of_the_named_ones():
    with pytest.raises(ArgumentError):
        _tctim(terms="academic")


def test_every_card_tool_takes_the_profile():
    from sabueso.tools.db.chembl import FixtureChEMBLClient
    from sabueso.tools.db.mondo import FixtureMONDOClient
    from sabueso.tools.db.pdb_ccd import FixtureCCDClient
    from sabueso.tools.db.unichem import FixtureUniChemClient

    molecule, _ = sabueso.resolve(
        "chembl:CHEMBL110",
        terms="commercial",
        chembl_client=FixtureChEMBLClient("temp_data"),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    assert molecule.quality["terms_profile"]["excluded"] == []
    disease, _ = sabueso.resolve(
        "ORPHA:868", terms="commercial", mondo_client=FixtureMONDOClient("temp_data")
    )
    assert disease.quality["terms_profile"]["profile"] == "commercial"


def test_a_database_licence_with_share_alike_binds_when_shared(monkeypatch):
    stated = {
        "Somewhere": {
            "licence": "ODbL-1.0",
            "attribution": "Somewhere",
            "statement": "https://example.org/licence",
            "reviewed": "2026-09-29",
        }
    }
    monkeypatch.setattr(terms_module, "source_terms", lambda: stated)
    answer = verdict("Somewhere", "commercial_product")
    assert (answer["verdict"], answer["obligations"]) == (
        "allowed",
        ["attribution", "share_alike"],
    )
    assert verdict("Somewhere", "internal_research")["obligations"] == []
