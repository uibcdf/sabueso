"""PDB mentions carry a source-stated entry association, never protein identity."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.migration import rebuild_options
from sabueso.core.snapshot import pinned_ref
from sabueso.mappings.europepmc import (
    ANNOTATION_MAPPING,
    STRUCTURE_MENTION_RULE,
    map_annotations,
    structure_associations,
)
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient

ARTICLE = "PMC:PMC12400196"


def response():
    return FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"]


class Answer:
    def __init__(self, record):
        self.record = record

    def annotations(self, articles):
        return {"record": deepcopy(self.record), "retrieved_at": "fixture"}


def resolve(record=None, **options):
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        europepmc={"article_ids": ARTICLE},
        europepmc_client=Answer(record)
        if record is not None
        else FixtureEuropePMCClient("temp_data"),
        **options,
    )[0]


def outcome(card):
    return next(r for r in card.quality["enrichments"] if r["source"] == "Europe PMC")


def row(card, predicate):
    return next(
        r
        for r in card.knowledge_state()["rows"]
        if r["area"] == f"relationships.{predicate}" and r["source"] == "Europe PMC"
    )


def mapping():
    entry = json.loads(Path("temp_data/P60174.json").read_text())
    return map_protein(entry, "fixture")


def test_public_methods_mention_has_both_source_statements_and_a_named_rule():
    card = resolve()
    (rel,) = card.relationships("structure_mentioned_in")
    assert rel["subject_ref"] == "uniprot:P60174"
    assert rel["object_ref"] == "pubmed:40832834"
    q = rel["qualifiers"]
    assert q["structure_ref"] == "pdb:2JK2"
    context = q["structure_context"]
    assert context["protein_ref"] == "uniprot:P60174"
    assert context["scope"] == "entry_association"
    (struct_rel_id,) = context["relationship_ids"]
    struct_rel = card.relationship_store.get(struct_rel_id)
    assert struct_rel["predicate"] == "has_structure"
    assert context["source_assertion_ids"] == struct_rel["source_assertion_ids"]
    (mention_id,) = rel["source_assertion_ids"]
    mention = card.source_assertion_store.get(mention_id)
    annotation = next(a for a in response()[0]["annotations"] if a["exact"] == "2jk2")
    assert mention["subject_ref"] == "pdb:2JK2"
    assert mention["field_path"] == "relationships.mentioned_in"
    assert mention["asserted_value"]["annotation"] == annotation
    assert (
        mention["source_metadata"]["identity_basis"]["kind"] == "stated_pdb_accession"
    )
    assert mention["acquisition"] == {"method": "database", "origin": "text_mining"}
    assert q["locations"] == [
        {"annotation": annotation, "source_assertion_id": mention_id}
    ]
    assert rel["derivation"]["rule"] == STRUCTURE_MENTION_RULE
    assert set(rel["derivation"]["inputs"]) == {
        mention_id,
        struct_rel_id,
        *context["source_assertion_ids"],
    }
    assert all(
        a["field_path"] != "relationships.structure_mentioned_in"
        for a in card.source_assertion_store.to_list()
    )
    assert all(
        a["found"] for a in card.explain([mention_id, *context["source_assertion_ids"]])
    )
    pub = next(
        p
        for p in card.literature()["publications"]
        if p["publication_ref"] == rel["object_ref"]
    )
    (view,) = pub["structure_mentions"]
    assert view["structure_context"] == context
    assert view["derivation"] == rel["derivation"]
    assert len(pub["mentions"]) == 1
    assert not pub["curated"] and not pub["supports"]
    view["locations"][0]["annotation"]["exact"] = "changed"
    assert mention["asserted_value"]["annotation"] == annotation
    record = outcome(card)
    assert record["mapping"] == ANNOTATION_MAPPING
    assert record["count"] == record["annotation_count"] == 2
    assert record["uniprot_mention_count"] == record["structure_mention_count"] == 1
    assert len(record["unlinked_pdb_mentions"]) == 3
    assert {r["structure_ref"] for r in record["unlinked_pdb_mentions"]} == {"pdb:7QON"}
    assert {r["reason"] for r in record["unlinked_pdb_mentions"]} == {
        "no_supported_has_structure_on_card"
    }
    assert (
        row(card, "mentioned_in")["count"]
        == row(card, "structure_mentioned_in")["count"]
        == 1
    )


@pytest.mark.parametrize(
    "change",
    [
        "foreign_subject",
        "foreign_value_subject",
        "foreign_object",
        "wrong_field",
        "dangling_support",
        "derived_only",
    ],
)
def test_unstated_or_unrelated_structure_links_do_not_ground_mentions(change):
    mapped = mapping()
    rel = next(
        r
        for r in mapped["relationships"]
        if r["predicate"] == "has_structure" and r["object_ref"] == "pdb:2JK2"
    )
    assertion = next(
        a
        for a in mapped["source_assertions"]
        if a["id"] == rel["source_assertion_ids"][0]
    )
    if change == "foreign_subject":
        assertion["subject_ref"] = "uniprot:Q9C401"
    elif change == "foreign_value_subject":
        assertion["asserted_value"]["subject_ref"] = "uniprot:Q9C401"
    elif change == "foreign_object":
        assertion["asserted_value"]["object_ref"] = "pdb:7QON"
    elif change == "wrong_field":
        assertion["field_path"] = "identifiers.uniprot"
    else:
        rel["source_assertion_ids"] = (
            ["missing"] if change == "dangling_support" else []
        )
        rel["derivation"] = {"rule": "synthetic@1", "inputs": []}
    associated = structure_associations([mapped], "P60174")
    assert "pdb:2JK2" not in associated
    result = map_annotations(response(), "P60174", "fixture", ARTICLE, associated)
    assert not any(
        r["predicate"] == "structure_mentioned_in" for r in result["relationships"]
    )
    assert any(
        u["structure_ref"] == "pdb:2JK2" for u in result["unlinked_pdb_mentions"]
    )


@pytest.mark.parametrize("change", ["name", "uri", "tag", "subtype", "expanded"])
def test_pdb_identity_requires_the_printed_code_and_exact_native_tag(change):
    record = response()
    annotation = next(a for a in record[0]["annotations"] if a["exact"] == "2jk2")
    if change == "name":
        annotation["exact"] = "human TIM"
    elif change == "uri":
        annotation["tags"][0]["uri"] = "https://example.org/pdbe/pdb:2jk2"
    elif change == "tag":
        annotation["tags"][0]["name"] = "7qon"
    elif change == "subtype":
        annotation["subType"] = "Gene_Proteins"
    else:
        annotation["exact"] = "pdb_00002jk2"
    card = resolve(record)
    assert not card.relationships("structure_mentioned_in")
    assert row(card, "structure_mentioned_in")["state"] == "not_stated"
    assert row(card, "structure_mentioned_in")["count"] == 0
    assert row(card, "mentioned_in")["state"] == "known"


def test_structural_sources_accumulate_without_whole_entry_identity():
    # A synthetic annotation in memory exercises the public 1HTI mappings; it is
    # deliberately not saved as a provider fixture or claimed as a real occurrence.
    record = response()
    annotation = next(a for a in record[0]["annotations"] if a["exact"] == "2jk2")
    annotation["exact"] = "1hti"
    annotation["tags"] = [
        {"name": "1HTI", "uri": "https://identifiers.org/pdbe/pdb:1hti"}
    ]
    card = resolve(record, structures=["1HTI"])
    (rel,) = card.relationships("structure_mentioned_in")
    context = rel["qualifiers"]["structure_context"]
    assert context["structure_ref"] == "pdb:1HTI"
    assert {a["source"] for a in card.explain(context["source_assertion_ids"])} == {
        "UniProt",
        "RCSB PDB",
    }
    assert context["scope"] == "entry_association"
    assert not card.relationships("same_as", "pdb:1HTI")
    # Structural source terms cannot license a paper's attached fragments.
    unknown = card.terms("redistribution")["cards"][0]["unknown"]
    assert any(i.get("id") == rel["id"] for i in unknown)
    assert any(
        i["kind"] == "literature_location"
        and i["predicate"] == "structure_mentioned_in"
        for i in unknown
    )


def test_historical_direct_only_requests_do_not_claim_pdb_was_queried():
    card = resolve()
    record = outcome(card)
    record.pop("mapping")
    record.pop("uniprot_mention_count")
    record["count"] = 1  # A historical mapping only counted direct UniProt mentions.
    assert row(card, "structure_mentioned_in")["state"] == "not_queried"
    assert row(card, "mentioned_in")["count"] == 1
    card = resolve(terms="commercial")
    assert row(card, "structure_mentioned_in")["state"] == "not_queried"
    assert outcome(card)["mapping"] == ANNOTATION_MAPPING


def test_a_pdb_mention_does_not_count_as_a_direct_protein_mention():
    record = response()
    record[0]["annotations"] = [
        a for a in record[0]["annotations"] if a["subType"] == "PDBe"
    ]
    card = resolve(record)
    assert not card.relationships("mentioned_in")
    assert row(card, "mentioned_in")["state"] == "not_stated"
    assert row(card, "mentioned_in")["count"] == 0
    assert row(card, "structure_mentioned_in")["state"] == "known"
    assert row(card, "structure_mentioned_in")["count"] == 1
    publication = next(
        p
        for p in card.literature()["publications"]
        if p["publication_ref"] == "pubmed:40832834"
    )
    assert not publication["mentions"]
    assert len(publication["structure_mentions"]) == 1


def test_structure_context_round_trip_and_refresh_preserve_historical_support(tmp_path):
    card = resolve()
    before = card.to_dict()
    (rel,) = card.relationships("structure_mentioned_in")
    historical_relationship = pinned_ref(card.id, card.snapshot_id(), rel["id"])
    historical_assertions = {
        identifier: pinned_ref(card.id, card.snapshot_id(), identifier)
        for identifier in rel["source_assertion_ids"]
        + rel["qualifiers"]["structure_context"]["source_assertion_ids"]
    }
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(card)
    assert store.load(card.pinned_ref()).to_dict() == before
    assert rebuild_options(card)["europepmc"] == {"article_ids": [ARTICLE]}
    refreshed, _ = sabueso.refresh_card(
        card,
        store=store,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc_client=FixtureEuropePMCClient("temp_data"),
    )
    assert refreshed.relationships("structure_mentioned_in") == [rel]
    assert store.relationship(historical_relationship) == rel
    for identifier, pin in historical_assertions.items():
        assert store.source_assertion(pin) == card.source_assertion_store.get(
            identifier
        )
    assert card.to_dict() == before
    for identifier in rel["derivation"]["inputs"]:
        assert card.explain([identifier]) == refreshed.explain([identifier])


def test_different_occurrences_keep_all_rule_inputs_locations_and_terms():
    record = response()

    class DifferentAnswers:
        def annotations(self, articles):
            answer = deepcopy(record)
            if articles == ["MED:40832834"]:
                annotation = next(
                    a for a in answer[0]["annotations"] if a["exact"] == "2jk2"
                )
                annotation["section"] = "Table"
            return {"record": answer, "retrieved_at": "fixture"}

    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": [ARTICLE, "MED:40832834"]},
        europepmc_client=DifferentAnswers(),
    )
    (rel,) = card.relationships("structure_mentioned_in")
    assert len(rel["source_assertion_ids"]) == 2
    assert set(rel["source_assertion_ids"]) <= set(rel["derivation"]["inputs"])
    assert len(rel["qualifier_conflicts"]["locations"]) == 2
    pub = next(
        p
        for p in card.literature()["publications"]
        if p["publication_ref"] == rel["object_ref"]
    )
    assert (
        pub["structure_mentions"][0]["qualifier_conflicts"]
        == rel["qualifier_conflicts"]
    )
    unknown = card.terms("redistribution")["cards"][0]["unknown"]
    assert {
        i["id"]
        for i in unknown
        if i["kind"] == "literature_location"
        and i["predicate"] == "structure_mentioned_in"
    } == set(rel["source_assertion_ids"])
