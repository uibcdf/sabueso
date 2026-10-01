"""UniRef: a protein's sequence clusters and related entries, never merged (#103).

Fixtures: UniProt's UniRef clusters of TcTIM (P52270) and the members of
UniRef90_P52270 (release 2026_03), and the UniProt entry of T. cruzi CL Brener's TIM
(Q4DV43), the genome-strain entry of the same protein.
"""

import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.uniref import FixtureUniRefClient, _next


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(FixtureUniProtClient("temp_data"))


def _card(resolver, accession="P52270", client=None):
    card, _ = sabueso.resolve(
        accession,
        resolver=resolver,
        uniref=True,
        uniref_client=client or FixtureUniRefClient("temp_data"),
    )
    return card


@pytest.fixture(scope="module")
def tctim(resolver):
    return _card(resolver)


def _record(card):
    (record,) = [e for e in card.quality["enrichments"] if e.get("data") == "uniref"]
    return record


def test_the_entry_states_its_clusters(tctim):
    assert tctim.get("identifiers.uniref")["value"] == {
        "uniref100": "UniRef100_P52270",
        "uniref90": "UniRef90_P52270",
        "uniref50": "UniRef50_P04789",
    }
    assert _record(tctim)["version"] == "2026_03"


def test_the_genome_strain_entry_is_related_never_the_same(tctim):
    (strain,) = [
        r
        for r in tctim.relationships("clustered_with")
        if r["object_ref"] == "uniprot:Q4DV43"
    ]
    q = strain["qualifiers"]
    assert (q["cluster"], q["identity_level"], q["taxon_id"]) == (
        "UniRef90_P52270",
        0.9,
        353153,
    )
    assert (q["uniref100"], q["same_uniref100"]) == ("UniRef100_Q4DV43", False)
    assert tctim.relationships("same_as", object_ref="uniprot:Q4DV43") == []
    record = _record(tctim)
    assert (record["count"], record["uniprot_members"], record["uniparc_members"]) == (
        6,
        1,
        5,
    )


def test_sequences_in_the_same_uniref100_cluster_are_marked(tctim):
    same = sorted(
        r["object_ref"]
        for r in tctim.relationships("clustered_with")
        if r["qualifiers"].get("same_uniref100")
    )
    assert same == ["uniparc:UPI0000112D88", "uniparc:UPI0001753D16"]


def test_sequence_differences_of_two_entries_of_equal_length(resolver, tctim):
    strain, _ = sabueso.resolve("Q4DV43", resolver=resolver)
    view = tctim.sequence_differences(strain)
    assert view["rule"]["rule"] == "equal_length_positions@1"
    assert view["lengths"] == [251, 251]
    assert [(d["position"], d["residues"]) for d in view["differences"]] == [
        (90, ["S", "K"]),
        (161, ["S", "A"]),
        (162, ["R", "H"]),
        (201, ["T", "A"]),
    ]
    assert view["identical"] is False


def test_sequences_of_different_lengths_are_not_compared(resolver, tctim):
    human, _ = sabueso.resolve("P60174", resolver=resolver)
    view = tctim.sequence_differences(human)
    assert view["basis"] == "different_lengths"
    assert "differences" not in view


def test_a_failing_source_is_an_error_not_an_absence(resolver):
    with pytest.warns(EnrichmentFailedWarning):
        card = _card(
            resolver,
            client=FixtureUniRefClient("temp_data", failing={"clusters_P52270"}),
        )
    assert _record(card)["status"] == "error"


def test_pages_are_followed_through_the_link_header():
    link = '<https://rest.uniprot.org/uniref/X/members?cursor=abc&size=500>; rel="next"'
    assert (
        _next(link) == "https://rest.uniprot.org/uniref/X/members?cursor=abc&size=500"
    )
    assert _next(None) is None
