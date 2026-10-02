"""Public located mentions are explainable through exact stored support."""

from copy import deepcopy

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.quantities import seal
from sabueso.core.relationship_store import make_relationship
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient

PUBLICATION = "pubmed:40832834"
ARTICLE = "PMC:PMC12400196"


def card():
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": ARTICLE},
        europepmc_client=FixtureEuropePMCClient("temp_data"),
    )[0]


def test_explanation_reads_both_legs_and_rejected_occurrences_without_mutation():
    subject = card()
    before = subject.to_dict()
    answer = subject.explain_literature(PUBLICATION)
    assert answer["status"] == "on_card"
    assert answer["rule"]["rule"] == "literature_explanation@1"
    assert answer["rule"]["inputs"] == [subject.pinned_ref()]
    links = {row["relationship"]["predicate"]: row for row in answer["links"]}
    assert set(links) == {"mentioned_in", "structure_mentioned_in"}
    (context,) = links["structure_mentioned_in"]["structure_contexts"]
    assert context["context"]["scope"] == "entry_association"
    (structural,) = context["relationships"]
    assert structural["relationship"]["predicate"] == "has_structure"
    assert structural["relationship"]["object_ref"] == "pdb:2JK2"
    assert all(a["found"] for a in context["source_assertions"])
    (raw,) = links["structure_mentioned_in"]["source_assertions"]
    assert raw["subject_ref"] == "pdb:2JK2"
    assert (
        raw["asserted_value"]["annotation"]["section"]
        == "Methods (http://purl.org/orb/Methods)"
    )
    assert raw["acquisition"] == {"method": "database", "origin": "text_mining"}
    assert len(answer["unlinked_pdb_mentions"]) == 3
    assert {r["structure_ref"] for r in answer["unlinked_pdb_mentions"]} == {"pdb:7QON"}
    assert {r["reason"] for r in answer["unlinked_pdb_mentions"]} == {
        "no_supported_has_structure_on_card"
    }
    answer["links"][0]["relationship"]["qualifiers"]["source"] = "mutated output"
    assert subject.to_dict() == before


def test_explanation_and_item_reads_keep_the_historical_pin(tmp_path):
    subject = card()
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(subject)
    expected = subject.explain_literature(PUBLICATION)
    later = Card.from_dict(subject.to_dict())
    later.meta["later_observation"] = True
    store.save(later)
    loaded = store.load(pin)
    assert loaded.explain_literature(PUBLICATION) == expected
    for link in expected["links"]:
        assert store.relationship(link["relationship_ref"]) == link["relationship"]
        for sa in link["source_assertions"]:
            assert (
                store.source_assertion(sa["source_assertion_ref"])["asserted_value"]
                == sa["asserted_value"]
            )


@pytest.mark.parametrize("which", ["assertion", "relationship"])
def test_missing_stored_context_is_partial_never_an_invented_chain(which):
    data = card().to_dict()
    link = next(
        r
        for r in data["relationship_store"]
        if r["predicate"] == "structure_mentioned_in"
    )
    context = link["qualifiers"]["structure_context"]
    key = "source_assertion_store" if which == "assertion" else "relationship_store"
    identifier = context[
        "source_assertion_ids" if which == "assertion" else "relationship_ids"
    ][0]
    data[key] = [r for r in data[key] if r["id"] != identifier]
    # Deliberately construct a broken-support card while sealing its actual quantities.
    data["quantities"] = seal(data)
    answer = Card.from_dict(data).explain_literature(PUBLICATION)
    assert (answer["status"], answer["reason"]) == ("partial", "missing_stored_support")


def test_primary_citation_measurement_and_curated_support_are_distinct_routes():
    # Synthetic citation associations on the public card, not provider responses.
    subject = card()
    structural = subject.relationships("has_structure")[0]
    structural["qualifiers"]["primary_citation"] = {"pubmed": "18562316"}
    subject.relationship_store.add(
        make_relationship(
            "uniprot:P60174",
            "has_bioactivity",
            "chembl:test",
            qualifiers={"document": {"pubmed": "18562316"}},
            source_assertion_ids=structural["source_assertion_ids"],
        )
    )
    record = subject.add_literature_claim(
        "other",
        "A synthetic intake statement for explanation testing.",
        "pubmed:18562316",
        "simulated curator",
    )
    answer = subject.explain_literature("pubmed:18562316")
    assert {r["relationship"]["predicate"] for r in answer["links"]} >= {
        "has_structure",
        "has_bioactivity",
    }
    assert record["source_assertion_id"] in {
        r["id"] for r in answer["source_assertions"]
    }


def test_qualifier_alternatives_are_retained_and_explained():
    subject = card()
    rel = subject.relationships("structure_mentioned_in")[0]
    context = deepcopy(rel["qualifiers"]["structure_context"])
    context["recorded_alternative"] = "synthetic context alternative"
    rel["qualifier_conflicts"] = {"structure_context": [context]}
    answer = subject.explain_literature(PUBLICATION)
    link = next(
        r
        for r in answer["links"]
        if r["relationship"]["predicate"] == "structure_mentioned_in"
    )
    assert len(link["structure_contexts"]) == 2
    assert link["relationship"]["qualifier_conflicts"]["structure_context"] == [context]


def test_well_formed_missing_reference_is_not_on_card_and_typo_is_refused():
    subject = card()
    answer = subject.explain_literature("pubmed:999999999")
    assert answer["status"] == "not_on_card"
    assert answer["publication"] is None and not answer["links"]
    with pytest.raises(ArgumentError):
        subject.explain_literature("pubemd:40832834")
