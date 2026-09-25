"""Organism identity, gene loci and orthology groups on protein cards (uibcdf/sabueso#54)."""

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient


@pytest.fixture(scope="module")
def cards():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    return {
        acc: sabueso.resolve(acc, resolver=resolver)[0] for acc in ("P52270", "P60174")
    }


def _value(card, path):
    node = card.get(path)
    return None if node is None else node["value"]


def test_the_taxon_and_lineage_are_stated_by_uniprot(cards):
    tc, hs = cards["P52270"], cards["P60174"]
    assert _value(tc, "annotations.taxon_id") == 5693
    assert _value(hs, "annotations.taxon_id") == 9606
    lineage = _value(tc, "annotations.lineage")
    assert lineage[0] == "Eukaryota" and "Trypanosomatida" in lineage
    assert "Trypanosoma cruzi" not in lineage  # the organism itself is not repeated
    for path in ("annotations.taxon_id", "annotations.lineage"):
        (sa_id,) = tc.get(path)["source_assertion_ids"]
        assertion = tc.source_assertion_store.get(sa_id)
        assert assertion["source"]["name"] == "UniProt"
        assert assertion["source"]["version"] == "120"


def test_gene_loci_are_identity_anchors(cards):
    tc, hs = cards["P52270"], cards["P60174"]
    loci = _value(tc, "identifiers.gene_loci")
    # A reviewed entry can gather the loci of several strain genomes.
    assert {"database": "TriTrypDB", "id": "TcCLB.508647.200"} in loci
    assert len({x["id"] for x in loci}) == len(loci) > 1
    assert _value(hs, "identifiers.gene_loci") == [
        {"database": "NCBI Gene", "id": "7167"},
        {"database": "HostDB", "id": "ENSG00000111669"},
    ]


def test_orthology_groups_are_classifications_as_stated(cards):
    def groups(card):
        return {
            r["object_ref"]: r["qualifiers"]
            for r in card.relationship_store.to_list()
            if r["predicate"] == "classified_in"
            and r["object_ref"].split(":")[0] in ("orthodb", "eggnog")
        }

    hs = groups(cards["P60174"])
    assert set(hs) == {"orthodb:9472880at2759", "eggnog:KOG1643"}
    assert hs["eggnog:KOG1643"]["scope"] == "Eukaryota"
    # UniProt states no orthology group for TcTIM: nothing is invented, and nothing
    # reads as "not an ortholog".
    assert groups(cards["P52270"]) == {}


def test_decks_filter_and_group_by_lineage(cards):
    unknown = Card(meta={"card_id": "sabueso:protein:uniprot:Q00000"})
    deck = Deck([cards["P52270"], cards["P60174"], unknown])
    trypanosomatids = deck.in_lineage("Trypanosomatida")
    assert trypanosomatids.ids() == ["sabueso:protein:uniprot:P52270"]
    assert trypanosomatids.meta["lineage_not_stated"] == [unknown.id]
    assert deck.in_lineage("Eukaryota").ids() == [
        "sabueso:protein:uniprot:P52270",
        "sabueso:protein:uniprot:P60174",
    ]
    assert deck.in_lineage("Homo sapiens").ids() == ["sabueso:protein:uniprot:P60174"]
    groups = deck.group_by("annotations.taxon_id")
    assert {k: g.ids() for k, g in groups.items()} == {
        5693: ["sabueso:protein:uniprot:P52270"],
        9606: ["sabueso:protein:uniprot:P60174"],
        None: [unknown.id],
    }
