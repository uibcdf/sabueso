"""Curated free-text claims typed by topic, never compared (uibcdf/sabueso#43).

The claims below are constructed for the tests, under placeholder DOIs, and claim
nothing about the literature.
"""

import pytest

import sabueso
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

PAPER = "doi:10.0000/constructed-claim"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


@pytest.fixture
def card(resolver):
    return sabueso.resolve("P52270", resolver=resolver)[0]


def test_a_claim_is_kept_listed_and_never_compared(card):
    record = card.add_literature_claim(
        "interface",
        "The dimer interface can be targeted selectively.",
        PAPER,
        "curator-a",
        about=["residues:15", "pdb:1SUX"],
        locator="Discussion",
        quote="selectively targeted",
    )
    assert record["outcome"] == "not_compared"
    (claim,) = card.claims()["items"]
    assert (claim["topic"], claim["about"], claim["locator"]) == (
        "interface",
        ["pdb:1SUX", "residues:15"],
        "Discussion",
    )
    (row,) = card.table("claims")
    assert row["about"] == "pdb:1SUX; residues:15"
    pubs = {p["publication_ref"]: p for p in card.literature()["publications"]}
    (curated,) = pubs[PAPER]["curated"]
    assert (curated["field_path"], curated["outcome"]) == (
        "literature.claims",
        "not_compared",
    )


def test_claims_are_filtered_by_topic(card):
    card.add_literature_claim("interface", "One.", PAPER, "a")
    card.add_literature_claim("mechanism", "Two.", PAPER, "a")
    assert card.claims()["topics"] == {"interface": 1, "mechanism": 1}
    assert [c["text"] for c in card.claims(topic="mechanism")["items"]] == ["Two."]
    # Two papers stating the same text are two claims; the same statement twice is one.
    card.add_literature_claim("mechanism", "Two.", PAPER + "-2", "a")
    again = card.add_literature_claim("mechanism", "Two.", PAPER, "a")
    assert again["outcome"] == "not_compared"
    assert card.claims()["topics"]["mechanism"] == 2


@pytest.mark.parametrize(
    "kwargs, error",
    [
        (dict(topic="gossip"), ArgumentError),
        (dict(text=""), ArgumentError),
        (dict(about=["no reference"]), SchemaError),
    ],
)
def test_malformed_claims_are_refused(card, kwargs, error):
    args = dict(topic="interface", text="A claim.") | kwargs
    with pytest.raises(error):
        card.add_literature_claim(publication=PAPER, curator="a", **args)
    assert not card.claims()["items"]


def test_claims_survive_rebuilds(resolver, card, tmp_path):
    record = card.add_literature_claim("stability", "Stable to 50 °C.", PAPER, "a")
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    rebuilt, _ = sabueso.resolve("P52270", resolver=resolver, curations=store)
    (claim,) = rebuilt.claims()["items"]
    assert claim["source_assertion_id"] == record["source_assertion_id"]
    states = {
        (r["area"], r["source"]): r["state"] for r in rebuilt.knowledge_state()["rows"]
    }
    assert states[("literature.claims", "Literature")] == "known"
