"""GTEx: the ontology terms of the tissues a card's pext names (#102).

Fixture: GTEx Portal API v2, the tissue site details of gtex_v10 (54 tissues), with the
fields Sabueso reads. With gnomAD's pext of TPI1 (49 GTEx v10 tissues).
"""

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.mappings.gtex import tissue_key
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient
from sabueso.tools.db.gtex import FixtureGTExClient, get_tissues


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession="P60174", **options):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        gtex=True,
        gtex_client=FixtureGTExClient("temp_data"),
        gnomad_client=FixtureGnomADClient("temp_data"),
        **options,
    )
    return card


@pytest.fixture(scope="module")
def card(resolver):
    return _card(resolver, gnomad={}, exon_usage=True)


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "GTEx"]
    return record


def test_the_key_rule_joins_gtex_ids_as_gnomad_writes_them():
    assert tissue_key("Muscle_Skeletal") == "muscle_skeletal"
    assert (
        tissue_key("Brain_Spinal_cord_cervical_c-1") == "brain_spinal_cord_cervical_c_1"
    )
    assert (
        tissue_key("Cells_EBV-transformed_lymphocytes")
        == "cells_ebv_transformed_lymphocytes"
    )


def test_every_pext_tissue_has_the_term_gtex_states(card):
    record = _record(card)
    assert (record["status"], record["version"], record["count"]) == (
        "added",
        "gtex_v10",
        49,
    )
    assert record["tissues_not_in_gtex"] == []
    terms = {t["gtex_id"]: t for t in card.get("annotations.tissue_terms")["value"]}
    assert terms["Muscle_Skeletal"]["ontology_id"] == "UBERON:0011907"
    # A cell line takes an EFO term, as GTEx states.
    assert terms["Cells_Cultured_fibroblasts"]["ontology_id"] == "EFO:0002009"
    # GTEx tissues gnomAD's pext does not name (bladder, cervix...) are not kept.
    assert "Bladder" not in terms


def test_the_views_name_each_tissue_and_its_term(card):
    for view in (card.variant_tissue_usage(), card.isoform_tissue_usage()):
        block = view["tissue_terms"]
        assert block["rule"]["rule"] == "gtex_tissue_key@1"
        assert block["tissues_without_term"] == []
        assert block["terms"]["testis"] == {
            "gtex_id": "Testis",
            "name": "Testis",
            "ontology_id": "UBERON:0000473",
        }


def test_two_tissues_sharing_a_term_stay_two_tissues(card):
    terms = card.isoform_tissue_usage()["tissue_terms"]["terms"]
    assert terms["brain_cerebellum"]["ontology_id"] == "UBERON:0002037"
    assert terms["brain_cerebellar_hemisphere"]["ontology_id"] == "UBERON:0002037"


def test_each_term_is_gtex_s_statement_with_its_release(card):
    ids = card.get("annotations.tissue_terms")["source_assertion_ids"]
    made = card.source_assertion_store.get(ids[0])
    assert made["source"]["name"] == "GTEx"
    assert made["source"]["version"] == "gtex_v10"


def test_without_the_pext_gtex_is_not_asked(resolver):
    record = _record(_card(resolver))
    assert record["status"] == "not_found"
    assert "exon_usage=True" in record["detail"]


def test_a_parasite_protein_is_not_applicable(resolver):
    record = _record(_card(resolver, "P52270"))
    assert record["status"] == "not_applicable"


def test_a_failed_request_is_an_error(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "P60174",
            resolver=resolver,
            exon_usage=True,
            gnomad_client=FixtureGnomADClient("temp_data"),
            gtex=True,
            gtex_client=FixtureGTExClient("temp_data", failing={"gtex_v10"}),
        )
    assert _record(card)["status"] == "error"
    assert card.get("annotations.tissue_terms") is None


def test_get_tissues_returns_gtex_s_table():
    record = get_tissues("gtex_v10", client=FixtureGTExClient("temp_data"))
    assert record["source"] == "GTEx"
    assert len(record["record"]["tissues"]) == 54
