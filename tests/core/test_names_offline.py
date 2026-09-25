"""UniProt's other names of a protein: synonyms, abbreviations and gene names."""

import pytest

import sabueso
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _items(card, field_path):
    node = card.get(field_path) or {}
    return node.get("value") or []


def test_names_are_mapped_with_their_kind(resolver):
    card, _ = sabueso.resolve("P60174", resolver=resolver)
    assert card.get("names.canonical_name")["value"] == "Triosephosphate isomerase"
    assert _items(card, "names.synonyms") == [
        {"name": "Methylglyoxal synthase", "kind": "alternative_name"},
        {"name": "Triose-phosphate isomerase", "kind": "alternative_name"},
    ]
    assert _items(card, "names.abbreviations") == [
        {"name": "TIM", "of": "Triosephosphate isomerase"}
    ]
    assert _items(card, "names.gene_names") == [
        {"name": "TPI1", "kind": "gene_name", "gene": 1},
        {"name": "TPI", "kind": "synonym", "gene": 1},
    ]
    # Each item is a UniProt SourceAssertion, with its ECO evidence when stated.
    node = card.get("names.gene_names")
    first = card.source_assertion_store.get(node["source_assertion_ids"][0])
    assert first["source"]["name"] == "UniProt"
    assert first["source_metadata"]["eco"][0]["source"] == "HGNC"


def test_an_abbreviation_names_the_name_it_shortens(resolver):
    card, _ = sabueso.resolve("P35372", resolver=resolver)
    assert {"name": "MOP", "of": "Mu opioid receptor"} in _items(
        card, "names.abbreviations"
    )


def test_a_name_uniprot_does_not_state_is_known_as_not_stated(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    assert card.get("names.gene_names") is None
    rows = card.knowledge_state()["rows"]
    states = {r["area"]: r["state"] for r in rows if r["source"] == "UniProt"}
    assert states["names.gene_names"] == "not_stated"
    assert states["names.synonyms"] == "not_stated"
    assert states["names.abbreviations"] == "known"


def test_a_curated_synonym_uniprot_states_corroborates_it(resolver):
    card, _ = sabueso.resolve("P60174", resolver=resolver)
    record = card.add_literature_assertion(
        "names.synonyms", {"name": "Methylglyoxal synthase"}, "pubmed:1", "curator-a"
    )
    assert record["outcome"] == "corroborates"
    # Not listed twice, and no conflict: UniProt's kind describes, it does not state.
    names = [i["name"].casefold() for i in _items(card, "names.synonyms")]
    assert names.count("methylglyoxal synthase") == 1
    assert not card.quality.get("conflicts")


def test_unique_names_lists_each_name_once(resolver):
    cards = [
        sabueso.resolve(a, resolver=resolver)[0]
        for a in ("P52270", "P60174", "P60175", "V9HWK1")
    ]
    deck = Deck(cards)
    names = deck.unique_names()
    # "Triose-phosphate isomerase" and "Triosephosphate isomerase" are one name, shown
    # in the spelling used as a canonical name.
    assert names == [
        "HEL-S-49",
        "Methylglyoxal synthase",
        "TIM",
        "TPI",
        "TPI1",
        "Triosephosphate isomerase",
        "Triosephosphate isomerase, glycosomal",
    ]
    same, carriers = deck.unique_names(return_cards=True)
    assert same == names
    by_name = dict(zip(names, carriers))
    assert by_name["TIM"] == [
        "sabueso:protein:uniprot:P52270",
        "sabueso:protein:uniprot:P60174",
        "sabueso:protein:uniprot:P60175",
    ]
    assert len(by_name["Triosephosphate isomerase"]) == 4
    # A card that carries a name twice (canonical and alternative) counts once.
    assert (
        by_name["Triosephosphate isomerase"].count("sabueso:protein:uniprot:P60174")
        == 1
    )


def test_a_curated_synonym_is_a_name(resolver):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.add_literature_assertion(
        "names.synonyms", {"name": "TcTIM"}, "pubmed:8061610", "curator-a"
    )
    assert "TcTIM" in Deck([card]).unique_names()


def test_return_cards_is_checked():
    with pytest.raises(ArgumentError):
        Deck([]).unique_names(return_cards="yes")
