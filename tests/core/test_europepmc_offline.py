"""Europe PMC: the publications whose text states a protein's accession (#92).

Frozen search of 2026-09-29 for P60174: 25 of 354 articles (the 24 newest and a
preprint), temp_data/europepmc/P60174.json."""

import warnings

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient, get_mentions


def _card(**europepmc):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the saved search is a declared cut
        card, _ = sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            europepmc_client=FixtureEuropePMCClient("temp_data"),
            **europepmc,
        )
    return card


@pytest.fixture(scope="module")
def hstim():
    return _card(europepmc={})


def test_each_mentioning_article_is_a_relationship_to_the_publication(hstim):
    mentions = hstim.relationships("mentioned_in")
    assert len(mentions) == 25
    assert all(r["subject_ref"] == "uniprot:P60174" for r in mentions)
    refs = {r["object_ref"] for r in mentions}
    assert sum(ref.startswith("pubmed:") for ref in refs) == 24
    # A preprint without a PubMed id is named by its DOI, and marked.
    (preprint,) = [r for r in mentions if r["qualifiers"].get("preprint")]
    assert preprint["object_ref"].startswith("doi:10.1101/")
    q = mentions[0]["qualifiers"]
    assert (q["source"], q["mention"]) == ("Europe PMC", "uniprot_accession")
    assert {"title", "year", "open_access"} <= set(q)


def test_a_mention_is_text_mined_by_the_source_and_says_so(hstim):
    sa_id = hstim.relationships("mentioned_in")[0]["source_assertion_ids"][0]
    (sa,) = hstim.explain([sa_id])
    assert sa["acquisition"] == {"method": "database", "origin": "text_mining"}
    assert sa["source"] == "Europe PMC" and sa["version"] == "6.9"
    assert "ACCESSION_ID:P60174" in sa["source_metadata"]["query"]
    assert hstim.acquisition()["origins"]["text_mining"] == {"Europe PMC": 25}


def test_the_cut_is_reported_and_the_limit_asks_for_fewer(hstim):
    (record,) = [e for e in hstim.quality["enrichments"] if e["source"] == "Europe PMC"]
    assert (record["count"], record["total_count"], record["truncated"]) == (
        25,
        354,
        True,
    )
    assert len(_card(europepmc={"limit": 3}).relationships("mentioned_in")) == 3


def test_mentions_are_literature_never_curation(hstim):
    publications = hstim.literature()["publications"]
    mentioned = [p for p in publications if p["mentions"]]
    assert len(mentioned) == 25
    assert all(not p["curated"] for p in mentioned)
    assert all(p["title"] for p in mentioned)


def test_the_public_function_and_its_arguments():
    record = get_mentions("P60174", limit=2, client=FixtureEuropePMCClient("temp_data"))
    assert record["source"] == "Europe PMC" and record["truncated"] is True
    assert len(record["record"]["articles"]) == 2
    with pytest.raises(ArgumentError):
        _card(europepmc={"limt": 3})
