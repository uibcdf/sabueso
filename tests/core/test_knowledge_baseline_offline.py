"""The showcase knowledge baseline, end to end on frozen responses.

``docs/content/showcase/knowledge_baseline.ipynb`` runs this flow against live services.
This test runs the same steps offline, with the saved responses in ``temp_data``, so that
the public API it relies on keeps working: resolution by name and organism, the cards and
their SourceAssertions and what they do not know, identity findings, structures and
predicted models, oligomer, bioactivities and ligand decks, literature, a curated
literature assertion, a comparison of the two proteins, and pinned citation and storage.
"""

import warnings
from collections import Counter

import pytest
import pyunitwizard as puw

import sabueso
from sabueso._private.smonitor.warnings import CuratedDisagreementWarning
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient
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
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldClient("temp_data"),
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
    # The state as built, kept to cite it after the curation of test 7 (section 10).
    cards["HsTIM as built"] = Card.from_dict(cards["HsTIM"].to_dict())
    return cards, resolutions, decks


def test_1_resolution_by_name_and_organism(baseline):
    cards, resolutions, _ = baseline
    assert cards["TcTIM"].id == "sabueso:protein:uniprot:P52270"
    assert cards["HsTIM"].id == "sabueso:protein:uniprot:P60174"
    assert resolutions["HsTIM"].decision["rules"] == ["preference:prefer_reviewed@1"]
    assert resolutions["HsTIM"].alternatives  # kept, never silently dropped
    for card in cards.values():
        sources = {e["source"] for e in card.quality["enrichments"]}
        assert {"RCSB PDB", "ChEMBL", "PDBe-KB", "InterPro", "AlphaFold DB"} <= sources
    findings = {
        tuple(f["refs"]): f["finding"]
        for f in resolutions["HsTIM"].decision["identity_audit"]
    }
    assert findings[("uniprot:P60174", "uniprot:V9HWK1")] == "possibly_same_as"
    assert findings[("uniprot:P60174", "uniprot:U3KPS5")] == "same_gene"


def test_2_values_are_traced_to_what_sources_state(baseline):
    hstim = baseline[0]["HsTIM"]
    mass = hstim.quantity("sequence.molecular_weight")
    assert puw.get_value(mass, to_unit="kDa") == pytest.approx(26.669)
    (sa_id,) = hstim.get("annotations.subunit")["source_assertion_ids"]
    assertion = hstim.source_assertion_store.get(sa_id)
    assert assertion["source"]["name"] == "UniProt"
    assert {"PubMed"} <= {e.get("source") for e in assertion["source_metadata"]["eco"]}


def test_3_what_a_card_does_not_know(baseline):
    tctim = baseline[0]["TcTIM"]
    states = {(r["area"], r["source"]): r for r in tctim.knowledge_state()["rows"]}
    function = states[("annotations.function", "UniProt")]
    assert (function["state"], function["release"]) == ("not_stated", "120")
    assert states[("relationships.functionally_associated_with", "STRING")][
        "state"
    ] == ("not_queried")


def test_4_structures_fragments_and_models(baseline):
    cards = baseline[0]
    assert len(cards["TcTIM"].structures()["items"]) == 7
    view = cards["HsTIM"].structures()
    assert "pdb:1KLG" in view["excluded"]  # an HLA-DR complex with a TIM peptide
    (model,) = cards["TcTIM"].predicted_structures()["items"]
    assert (model["coverage"], model["sequence_matches"]) == (1.0, True)
    isoforms = {m["isoform"] for m in cards["HsTIM"].predicted_structures()["items"]}
    assert isoforms == {None, "P60174-3", "P60174-4"}


def test_5_oligomer_and_interface(baseline):
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


def test_6_bioactivities_and_shared_ligands(baseline):
    cards, _, decks = baseline
    classes = Counter(i["class"] for i in cards["TcTIM"].bioactivities()["items"])
    assert classes["active"] > 0 and classes["inactive"] > 0
    comparison = cards["TcTIM"].compare_ligands(
        decks["TcTIM"], cards["HsTIM"], decks["HsTIM"]
    )
    assert len(comparison["shared"]) == 14


def test_7_literature(baseline):
    tctim = baseline[0]["TcTIM"]
    pubs = {p["publication_ref"]: p for p in tctim.literature()["publications"]}
    assert pubs["pubmed:9761683"]["primary_citation_of"] == ["pdb:1TCD"]
    assert "HOMODIMERIZATION" in pubs["pubmed:9761683"]["cited_by"][0]["scope"]


def test_8_a_claim_read_in_a_paper_is_compared_not_imposed(baseline):
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


def test_9_the_two_proteins_side_by_side(baseline):
    cards = baseline[0]
    diff = cards["TcTIM"].compare_knowledge(
        cards["HsTIM"], residue_map={12: 12, 14: 14, 96: 96, 168: 166}
    )
    assert diff["fields"]["features_positional.active_site"]["status"] == "same"
    assert diff["fields"]["annotations.function"]["status"] == "only_other"
    assert "interpro:IPR000652" in diff["relationships"]["classified_in"]["both"]


def test_10_cite_store_and_read_back_exactly(baseline, tmp_path):
    cards = baseline[0]
    store = sabueso.KnowledgeStore(tmp_path / "baseline.db")
    before = store.save(cards["HsTIM as built"], note="as built")
    after = store.save(cards["HsTIM"], note="with the curated claims")
    assert before != after
    assert [h["note"] for h in store.history(cards["HsTIM"].id)] == [
        "as built",
        "with the curated claims",
    ]
    assert not store.load(before).quality.get("curation")
    assert store.load(after).quality["curation"]
    store.save(cards["TcTIM"])
    shared = store.relationships(object_ref="interpro:IPR000652")
    assert {r["card"].split("@")[0] for r in shared} == {
        cards["TcTIM"].id,
        cards["HsTIM"].id,
    }
    deck_ref = store.save_deck(Deck([cards["TcTIM"], cards["HsTIM"]]), "tims")
    assert store.load_deck(deck_ref).ids() == [cards["TcTIM"].id, cards["HsTIM"].id]


def test_11_store_and_read_back_as_jsonl(baseline, tmp_path):
    cards = {k: v for k, v in baseline[0].items() if k in ("TcTIM", "HsTIM")}
    path = tmp_path / "baseline.jsonl"
    save_deck_jsonl(Deck(list(cards.values()), meta={"purpose": "showcase"}), path)
    loaded = load_deck_jsonl(path)
    assert loaded.ids() == [c.id for c in cards.values()]
    assert loaded.meta == {"purpose": "showcase"}
    again = loaded.cards[1]
    assert again.quality.get("curation") == cards["HsTIM"].quality.get("curation")
