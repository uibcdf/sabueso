"""OMA: orthologs of a protein, joined only through an exact match OMA states (#83).

Fixtures: the cross-references OMA states for HsTIM (P60174, exact) and TcTIM (P52270,
mapped to T. cruzi CL Brener's Q4DV43, modified), and seven of HsTIM's 3,090 orthologs:
Q4DV43, two Salmonella strains sharing TPIS_SALTY, yeast and mouse (Swiss-Prot entry
names), and a Drosophila and a bacterial protein named by RefSeq and GenBank.
"""

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.oma import FixtureOMAClient


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession="P60174", oma=None, client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        oma={} if oma is None else oma,
        oma_client=client or FixtureOMAClient("temp_data"),
    )
    return card


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "OMA"]
    return record


@pytest.fixture(scope="module")
def card(resolver):
    return _card(resolver)


def test_orthologs_are_named_by_the_identifier_their_source_states(card):
    targets = sorted(
        (r["object_ref"], r["qualifiers"]["canonical_id"])
        for r in card.relationships("ortholog_of")
    )
    assert ("uniprot:Q4DV43", "Q4DV43") in targets  # OMA's canonical id
    assert ("uniprot:P17751", "TPIS_MOUSE") in targets  # UniProt resolves the name
    assert ("uniprot:P00942", "TPIS_YEAST") in targets
    oma_named = [t for t in targets if t[0].startswith("oma:")]
    assert sorted(c for _, c in oma_named) == ["HHV80407.1", "NP_788764.1"]
    record = _record(card)
    assert (record["count"], record["uniprot_orthologs"], record["oma_orthologs"]) == (
        7,
        5,
        2,
    )
    assert record["entry_names_resolved"] == 3


def test_identical_proteins_of_two_strains_stay_two_orthologs(card):
    salmonella = [
        r
        for r in card.relationships("ortholog_of")
        if r["object_ref"] == "uniprot:Q8ZKP7"
    ]
    assert len(salmonella) == 2
    assert {r["qualifiers"]["oma_id"] for r in salmonella} == {
        "SALT104728",
        "SALTY03934",
    }


def test_the_parasite_ortholog_keeps_omas_relation(card):
    (tc,) = [
        r
        for r in card.relationships("ortholog_of")
        if r["object_ref"] == "uniprot:Q4DV43"
    ]
    assert tc["qualifiers"]["rel_type"] == "1:1"
    assert tc["qualifiers"]["species"] == "Trypanosoma cruzi (strain CL Brener)"
    assert tc["qualifiers"]["taxon_id"] == 353153


def test_an_accession_oma_maps_to_another_protein_is_not_joined(resolver):
    # P52270 is TcTIM; OMA maps it to CL Brener's Q4DV43, whose sequence differs.
    card = _card(resolver, accession="P52270")
    record = _record(card)
    assert record["status"] == "not_found"
    assert "TRYCC03899" in record["detail"] and "modified" in record["detail"]
    assert card.relationships("ortholog_of") == []


def test_options_choose_taxa_and_relation_types(resolver):
    card = _card(resolver, oma={"taxa": [353153, 10090]})
    assert sorted(r["object_ref"] for r in card.relationships("ortholog_of")) == [
        "uniprot:P17751",
        "uniprot:Q4DV43",
    ]
    assert _record(card)["filters"] == {"taxa": [353153, 10090]}
    with pytest.raises(ArgumentError):
        _card(resolver, oma={"rel_type": "one-to-one"})


def test_a_failing_source_is_an_error_not_an_absence(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver, client=FixtureOMAClient("temp_data", failing={"xref_P60174"})
        )
    assert _record(card)["status"] == "error"


def test_a_retired_entry_that_keeps_the_name_is_not_taken():
    # UniProt's search for id:TPIS_HUMAN answers the active P60174 and P00938, retired
    # (demerged into P60174 and P60175) but still named TPIS_HUMAN.
    from sabueso.tools.db.oma import active_accessions

    answer = {
        "results": [
            {
                "primaryAccession": "P60174",
                "uniProtkbId": "TPIS_HUMAN",
                "entryType": "UniProtKB reviewed (Swiss-Prot)",
            },
            {
                "primaryAccession": "P00938",
                "uniProtkbId": "TPIS_HUMAN",
                "entryType": "Inactive",
            },
            {"primaryAccession": "A1", "uniProtkbId": "TWO_ACTIVE", "entryType": "x"},
            {"primaryAccession": "A2", "uniProtkbId": "TWO_ACTIVE", "entryType": "x"},
        ]
    }
    assert active_accessions(answer, ["TPIS_HUMAN", "TWO_ACTIVE", "ABSENT"]) == {
        "TPIS_HUMAN": "P60174"
    }
