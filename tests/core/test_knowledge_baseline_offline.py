"""The showcase knowledge baseline, end to end on frozen responses.

``docs/content/showcase/knowledge_baseline.ipynb`` runs this flow against live services.
This test runs the same steps offline, with the saved responses in ``temp_data``, so that
the public API it relies on keeps working: resolution by name and organism, the cards and
their SourceAssertions, structures, oligomer, bioactivities and ligand decks, literature,
a curated literature assertion, and storage.
"""

import warnings
from collections import Counter

import pytest
import pyunitwizard as puw

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.core.deck import Deck
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient
from sabueso.tools.deck.storage import load_deck_jsonl, save_deck_jsonl

TIM = "triosephosphate isomerase"


@pytest.fixture(scope="module")
def baseline():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    chembl = FixtureChEMBLClient("temp_data")
    options = dict(
        resolver=resolver,
        structures="all",
        interfaces=True,
        family_sites=True,
        ligand_sites=True,
        chembl={},
        chembl_client=chembl,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    cards, resolutions = {}, {}
    with warnings.catch_warnings():
        # Structures without a saved RCSB response are recorded as not found.
        warnings.simplefilter("ignore")
        for label, organism in (("TcTIM", 5693), ("HsTIM", 9606)):
            query = EntityQuery(name=TIM, organism=organism)
            cards[label], resolutions[label] = sabueso.resolve(query, **options)
    decks = {
        label: sabueso.ligand_deck(
            card, chembl_client=chembl, ccd_client=FixtureCCDClient("temp_data")
        )
        for label, card in cards.items()
    }
    return cards, resolutions, decks


def test_1_resolution_by_name_and_organism(baseline):
    cards, resolutions, _ = baseline
    assert cards["TcTIM"].id == "sabueso:protein:uniprot:P52270"
    assert cards["HsTIM"].id == "sabueso:protein:uniprot:P60174"
    assert resolutions["HsTIM"].decision["rules"] == ["preference:prefer_reviewed@1"]
    assert resolutions["HsTIM"].alternatives  # kept, never silently dropped
    for card in cards.values():
        sources = {e["source"] for e in card.quality["enrichments"]}
        assert {"RCSB PDB", "ChEMBL", "PDBe-KB", "InterPro"} <= sources


def test_2_values_are_traced_to_what_sources_state(baseline):
    hstim = baseline[0]["HsTIM"]
    mass = hstim.quantity("sequence.molecular_weight")
    assert puw.get_value(mass, to_unit="kDa") == pytest.approx(26.669)
    (sa_id,) = hstim.get("annotations.subunit")["source_assertion_ids"]
    assertion = hstim.source_assertion_store.get(sa_id)
    assert assertion["source"]["name"] == "UniProt"
    assert {"PubMed"} <= {e.get("source") for e in assertion["source_metadata"]["eco"]}


def test_3_structures_and_fragments(baseline):
    cards = baseline[0]
    assert len(cards["TcTIM"].structures()["items"]) == 7
    view = cards["HsTIM"].structures()
    assert "pdb:1KLG" in view["excluded"]  # an HLA-DR complex with a TIM peptide


def test_4_oligomer_and_interface(baseline):
    cards = baseline[0]
    classes = {
        label: {i["partner_ref"]: i["class"] for i in card.oligomer()["interfaces"]}
        for label, card in cards.items()
    }
    assert classes["TcTIM"] == {
        "uniprot:P52270": "homomeric",
        "uniprot:P04789": "chimera",
    }
    assert classes["HsTIM"]["uniprot:P60174"] == "homomeric"
    assert set(classes["HsTIM"].values()) == {"homomeric", "fragment_complex"}


def test_5_bioactivities_and_shared_ligands(baseline):
    cards, _, decks = baseline
    classes = Counter(i["class"] for i in cards["TcTIM"].bioactivities()["items"])
    assert classes["active"] > 0 and classes["inactive"] > 0
    comparison = cards["TcTIM"].compare_ligands(
        decks["TcTIM"], cards["HsTIM"], decks["HsTIM"]
    )
    assert len(comparison["shared"]) == 14


def test_6_literature(baseline):
    tctim = baseline[0]["TcTIM"]
    pubs = {p["ref"]: p for p in tctim.literature()["publications"]}
    assert pubs["pubmed:9761683"]["primary_citation_of"] == ["pdb:1TCD"]
    assert "HOMODIMERIZATION" in pubs["pubmed:9761683"]["cited_by"][0]["scope"]


def test_7_a_claim_read_in_a_paper_is_compared_not_imposed(baseline):
    hstim = baseline[0]["HsTIM"]
    field = "features_positional.natural_variant"
    before = [dict(i) for i in hstim.get(field)["value"]]
    with pytest.warns(CuratedDisagreementWarning):
        record = hstim.add_literature_assertion(
            field,
            {
                "start": 105,
                "substitution": {"original": "E", "alternatives": ["D"]},
                "description": "alters a conserved water network at the dimer interface",
            },
            publication="pubmed:18562316",
            curator="showcase",
            locator="Title",
        )
    assert record["outcome"] == "differs"
    assert all(item in hstim.get(field)["value"] for item in before)  # nothing lost


def test_8_store_and_read_back(baseline, tmp_path):
    cards = baseline[0]
    path = tmp_path / "baseline.jsonl"
    save_deck_jsonl(Deck(list(cards.values()), meta={"purpose": "showcase"}), path)
    loaded = load_deck_jsonl(path)
    assert loaded.ids() == [c.id for c in cards.values()]
    assert loaded.meta == {"purpose": "showcase"}
    again = loaded.cards[1]
    assert again.quality.get("curation") == cards["HsTIM"].quality.get("curation")
