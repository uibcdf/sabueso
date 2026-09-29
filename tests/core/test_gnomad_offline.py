"""gnomAD: population frequencies of a human gene's variants (#83).

Fixture: 15 of the 1,668 gnomAD (gnomad_r4) variants of TPI1: protein changes on the
canonical transcript ENST00000396705 and on ENST00000229270 (UniProt's isoform 3), and
non-coding ones.
"""

import collections

import pytest

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient

FIELD = "annotations.population_variants"


@pytest.fixture(scope="module")
def card():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P60174",
        resolver=resolver,
        gnomad={},
        gnomad_client=FixtureGnomADClient("temp_data"),
    )
    return card


def test_frequencies_are_kept_as_gnomad_states_them(card):
    e105d = next(v for v in card.get(FIELD)["value"] if v["hgvs_p"] == "p.Glu105Asp")
    assert e105d["exome"] == {
        "ac": 393,
        "an": 1461876,
        "af": pytest.approx(2.688e-4, rel=1e-3),
    }
    assert e105d["genome"]["ac"] == 16
    assert (e105d["location"], e105d["numbering"]) == (
        {"start": 105, "end": 105},
        "uniprot",
    )


def test_isoform_changes_are_placed_through_uniprots_isoform_map(card):
    variants = card.get(FIELD)["value"]
    counts = collections.Counter(v.get("not_placed", "placed") for v in variants)
    # ENST00000229270 is UniProt's isoform P60174-3, which replaces Met1 by 38 residues.
    # A change in those residues has no canonical counterpart; one past them does.
    assert counts == {"placed": 8, "isoform_specific_position": 6}
    frameshift = next(v for v in variants if v["hgvs_p"] == "p.Pro40ThrfsTer24")
    assert frameshift["location"] == {"start": 3, "end": 3}
    assert frameshift["placed_via"] == {
        "rule": "uniprot_isoform_map@1",
        "isoform": "P60174-3",
        "isoform_position": 40,
    }
    (record,) = [e for e in card.quality["enrichments"] if e["source"] == "gnomAD"]
    assert (record["count"], record["without_protein_change"]) == (14, 3)


def test_gnomad_does_not_cover_a_parasite_protein():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    card, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        gnomad={},
        gnomad_client=FixtureGnomADClient("temp_data"),
    )
    states = {
        (r["area"], r["source"]): r["state"] for r in card.knowledge_state()["rows"]
    }
    assert states[(FIELD, "gnomAD")] == "not_queried"
