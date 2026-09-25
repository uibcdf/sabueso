"""Exact organism relations and ranks from NCBI Taxonomy (uibcdf/sabueso#67).

Fixtures are NCBI Datasets taxon records (2026-09-25) for T. cruzi (5693), its strain
CL Brener (353153), Homo sapiens (9606) and all their ancestors.
"""

import json
from pathlib import Path

import pytest

import sabueso
from sabueso.core.deck import Deck
from sabueso.core.identity_audit import compare
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.ncbi_taxonomy import FixtureNCBITaxonomyClient, get_taxon


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _card(resolver, accession, client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        taxonomy=True,
        taxonomy_client=client or FixtureNCBITaxonomyClient("temp_data"),
    )
    return card


def test_the_card_states_ranks_and_ancestors(resolver):
    card = _card(resolver, "P52270")
    taxonomy = card.get("annotations.taxonomy")["value"]
    assert (taxonomy["tax_id"], taxonomy["rank"]) == (5693, "species")
    ranks = {a["rank"]: a["name"] for a in taxonomy["ancestors"] if a["rank"]}
    assert ranks["genus"] == "Trypanosoma" and ranks["family"] == "Trypanosomatidae"
    (sa_id,) = card.get("annotations.taxonomy")["source_assertion_ids"]
    source = card.source_assertion_store.get(sa_id)["source"]
    assert (source["name"], source["record_id"]) == ("NCBI Taxonomy", "5693")


def _taxon(tax_id):
    return json.loads(Path(f"temp_data/ncbi_taxonomy/{tax_id}.json").read_text("utf-8"))


def _basis(ref, tax_id, name, ancestors, sequence="MKTAYIAK"):
    return {
        "ref": ref,
        "taxon_id": tax_id,
        "organism": name,
        "lineage": [],
        "ancestor_ids": ancestors,
        "gene_loci": [],
        "sequence": sequence,
        "md5": None,
    }


def test_a_strain_and_its_species_are_related_exactly():
    strain, species = _taxon(353153), _taxon(5693)
    found = compare(
        _basis("a", 5693, "Trypanosoma cruzi", species["lineage"]),
        _basis("b", 353153, "Trypanosoma cruzi strain CL Brener", strain["lineage"]),
    )
    assert (found["finding"], found["organisms"]) == (
        "possibly_same_as",
        "ncbi_lineage",
    )
    # NCBI's answer is final: names that look related do not override it.
    human = _taxon(9606)
    assert (
        compare(
            _basis("a", 5693, "Trypanosoma cruzi", species["lineage"]),
            _basis("b", 9606, "Trypanosoma cruzi extended", human["lineage"]),
        )
        is None
    )
    # Without NCBI ancestors on both, names decide, and the finding says so.
    found = compare(
        _basis("a", 5693, "Trypanosoma cruzi", None),
        _basis("b", 353153, "Trypanosoma cruzi (strain CL Brener)", None),
    )
    assert found["organisms"] == "names"


def test_decks_group_by_rank(resolver):
    tc, hs = _card(resolver, "P52270"), _card(resolver, "P60174")
    plain, _ = sabueso.resolve("P60175", resolver=resolver)
    groups = Deck([tc, hs, plain]).group_by_rank("genus")
    assert {k: g.ids() for k, g in groups.items()} == {
        "Trypanosoma": [tc.id],
        "Homo": [hs.id],
        None: [plain.id],
    }
    assert groups["Homo"].meta["operations"][-1] == {
        "operation": "group_by_rank",
        "parameters": {"rank": "genus", "value": "Homo"},
    }


def test_knowledge_states(resolver, tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    def state(card):
        rows = [
            r
            for r in card.knowledge_state()["rows"]
            if r["area"] == "annotations.taxonomy" and r["source"] == "NCBI Taxonomy"
        ]
        assert len(rows) == 1  # one row, not one from the field and one from the source
        return rows[0]["state"]

    assert state(_card(resolver, "P52270")) == "known"
    plain, _ = sabueso.resolve("P52270", resolver=resolver)
    assert state(plain) == "not_queried"
    assert state(_card(resolver, "P52270", FixtureNCBITaxonomyClient(tmp_path))) == (
        "not_stated"
    )
    with pytest.warns(EnrichmentFailedWarning):
        failed = _card(
            resolver, "P52270", FixtureNCBITaxonomyClient("temp_data", failing={5693})
        )
    assert state(failed) == "unavailable"


def test_source_access_returns_the_raw_taxon():
    record = get_taxon("353153", client=FixtureNCBITaxonomyClient("temp_data"))
    assert (record["source"], record["kind"], record["record"]["rank"]) == (
        "NCBI Taxonomy",
        "taxon",
        "STRAIN",
    )
    assert 5693 in record["record"]["lineage"]
