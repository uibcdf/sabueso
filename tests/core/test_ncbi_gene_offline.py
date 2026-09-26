"""NCBI Gene relates two entries that state their gene in different databases (#69)."""

from pathlib import Path

import pytest

import sabueso
from sabueso.core.errors import RecordNotFoundError
from sabueso.core.migration import rebuild_options
from sabueso.mappings.ncbi_gene import parse_gene, products
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)
from sabueso.tools.db.ncbi_gene import FixtureNCBIGeneClient

TCTIM = EntityQuery(
    name="triosephosphate isomerase", organism=5693, include_subtaxa=True
)


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _pair(resolution):
    (finding,) = [
        f
        for f in resolution.decision["identity_audit"]
        if f["refs"] == ["uniprot:P52270", "uniprot:Q4DV43"]
    ]
    return finding


def test_a_gene_record_lists_the_uniprot_entries_of_its_products():
    record = parse_gene(Path("temp_data/ncbi_gene/3550449.xml").read_text())
    assert record["gene_id"] == "3550449"
    assert record["locus_tag"] == "Tc00.1047053508647.200"
    assert record["tax_id"] == 5693
    assert record["uniprot"] == {"swiss_prot": ["P52270"], "trembl": ["Q4DV43"]}
    assert products(record) == ["P52270", "Q4DV43"]
    missing = "<Entrezgene-Set><Error>GeneId 1 not found.</Error></Entrezgene-Set>"
    assert parse_gene(missing) is None
    with pytest.raises(RecordNotFoundError):
        FixtureNCBIGeneClient("temp_data").gene("1")


def test_without_ncbi_gene_the_loci_are_not_comparable(resolver):
    _, resolution = sabueso.resolve(TCTIM, resolver=resolver)
    basis = _pair(resolution)["basis"]
    assert basis["gene_loci"] == "not_comparable"
    assert "gene_products" not in basis


def test_ncbi_gene_lists_both_entries_as_products_of_one_gene(resolver):
    card, resolution = sabueso.resolve(
        TCTIM,
        resolver=resolver,
        ncbi_gene=True,
        ncbi_gene_client=FixtureNCBIGeneClient("temp_data"),
    )
    finding = _pair(resolution)
    # A strain variant of one gene, not a close paralog: flagged, never merged.
    assert finding["finding"] == "possibly_same_as"
    assert finding["basis"]["gene_products"] == [
        {
            "database": "NCBI Gene",
            "id": "3550449",
            "lists": ["P52270", "Q4DV43"],
            "retrieved_at": "fixture",
        }
    ]
    assert "gene_loci" not in finding["basis"]
    (link,) = resolution.identity_links
    assert link["qualifiers"]["basis"]["gene_products"][0]["id"] == "3550449"
    assert {"name": "NCBI Gene", "record": "3550449", "retrieved_at": "fixture"} in (
        resolution.decision["sources"]
    )
    # The resolver passed in is not changed, and a refresh asks NCBI Gene again.
    assert resolver.ncbi_gene is None
    assert rebuild_options(card)["ncbi_gene"] is True


def test_an_unanswered_gene_request_is_recorded_and_changes_nothing(resolver):
    _, resolution = sabueso.resolve(
        TCTIM,
        resolver=resolver,
        ncbi_gene=True,
        ncbi_gene_client=FixtureNCBIGeneClient("temp_data", failing={"3550449"}),
    )
    assert _pair(resolution)["basis"]["gene_loci"] == "not_comparable"
    (source,) = [s for s in resolution.decision["sources"] if s["name"] == "NCBI Gene"]
    assert source["outcome"].startswith("error")
