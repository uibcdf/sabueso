"""Pinned classification inputs remain distinct from source claims and execution."""

import ackredit
import argdigest
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureUniProtClient


@pytest.fixture(scope="module")
def public_card():
    return sabueso.resolve(
        "P52270", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )[0]


def synthetic(*records, entity_type="protein"):
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": entity_type},
        quality={"enrichments": list(records)},
    )


def assertion(card, path, value, source="UniProt", version="original"):
    made = make_source_assertion(path, value, source, "synthetic", "2026-01-01")
    made["source"]["version"] = version
    card.source_assertion_store.add(made)
    return made["id"]


def select(card, area, source=None):
    answer = card.explain_knowledge_state(area, source)
    (row,) = answer["rows"]
    return answer, row


def test_every_public_row_is_explained_without_changing_classification_or_credit(
    public_card, monkeypatch
):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no acquisition")
    )
    before = public_card.to_dict()
    state = public_card.knowledge_state()
    with ackredit.session("inert state explanation"):
        credited = ackredit.get_attribution().to_dict()
        answer = public_card.explain_knowledge_state()
        assert ackredit.get_attribution().to_dict() == credited
    assert answer["status"] == "on_card" and not answer["gaps"]
    assert [r["row"] for r in answer["rows"]] == state["rows"]
    assert answer["state_rule"] == state["rule"]
    assert answer["rule"]["rule"] == "knowledge_state_explanation@2"
    assert answer["state_rule"]["rule"] == "knowledge_state@5"
    assert answer["rule"]["inputs"] == [public_card.pinned_ref()]
    answer["rows"].clear()
    assert public_card.to_dict() == before


def test_selected_field_retains_source_specific_support_alternatives_and_conflicts():
    card = synthetic()
    path = "annotations.function"
    identifiers = [
        assertion(card, path, v, s)
        for v, s in [
            ("selected", "UniProt"),
            ("selected", "Literature"),
            ("alternative", "UniProt"),
        ]
    ]
    card.set(path, "selected", identifiers[:2])
    card.selection_rules = {path: {"strategy": "synthetic"}}
    card.quality["conflicts"] = [{"field": path, "source_assertion_ids": identifiers}]
    answer, row = select(card, path, "UniProt")
    assert answer["status"] == "on_card" and row["row"]["state"] == "conflicting"
    assert [a["id"] for a in row["source_assertions"]] == identifiers[:1]
    assert {a["id"] for a in row["field"]["source_assertions"]} == set(identifiers[:2])
    assert [a["id"] for a in row["field"]["alternatives"]] == identifiers[2:]
    assert row["field"]["conflicts"] == card.quality["conflicts"]
    assert row["field"]["selection_rules"] == card.selection_rules
    assert row["source_assertions"][0]["version"] == "original"


def test_uniprot_absence_and_unqueried_curation_have_no_negative_assertion(public_card):
    _, absent = select(public_card, "annotations.function", "UniProt")
    assert absent["row"]["state"] == "not_stated"
    assert absent["classification_inputs"]["basis"] == "uniprot_field_not_stored"
    assert absent["consultation"]["negative_source_assertion"] is False
    assert absent["consultation"]["anchor"]["source_assertions"]
    assert absent["consultation"]["sources"]
    _, curation = select(public_card, "annotations.essentiality", "Literature")
    assert curation["row"]["state"] == "not_queried"
    assert curation["classification_inputs"]["basis"] == "curation_field_not_stored"
    assert "source_assertions" not in curation


def test_uniprot_predicate_count_has_exact_relationship_support():
    card = synthetic()
    anchor = assertion(card, "identifiers.uniprot", "P52270")
    card.set("identifiers.uniprot", "P52270", [anchor])
    identifier = assertion(card, "relationships.interacts_with", "uniprot:P60174")
    rel = make_relationship(
        "uniprot:P52270",
        "interacts_with",
        "uniprot:P60174",
        source_assertion_ids=[identifier],
    )
    card.relationship_store.add(rel)
    _, row = select(card, "relationships.interacts_with", "UniProt")
    assert row["row"]["count"] == 1
    assert row["classification_inputs"]["relationship_ids"] == [rel["id"]]
    assert row["relationships"][0]["source_assertions"][0]["id"] == identifier


@pytest.mark.parametrize(
    "record,state",
    [
        ({"status": "added", "count": 4}, "known"),
        ({"status": "added", "count": 4, "truncated": True}, "partial"),
        ({"status": "partial", "count": 2}, "partial"),
        ({"status": "error", "detail": "original failure"}, "unavailable"),
        ({"status": "not_found", "version": "original"}, "not_stated"),
        ({"status": "not_queried", "detail": "missing key"}, "not_queried"),
        (
            {"status": "not_applicable", "detail": "organism outside coverage"},
            "not_queried",
        ),
    ],
)
def test_request_outcomes_retain_exact_reports_and_are_not_source_claims(record, state):
    record = {"source": "ChEMBL", "identifier": "CHEMBL_SYNTHETIC", **record}
    card = synthetic(record)
    _, row = select(card, "relationships.has_bioactivity", "ChEMBL")
    assert row["row"]["state"] == state
    (report,) = row["classification_inputs"]["reports"]
    assert report["record"] == record
    assert report["locator"] == {
        "card_ref": card.pinned_ref(),
        "field_path": "quality.enrichments",
        "index": 0,
    }
    assert row["classification_inputs"]["count_field"] == "count"
    assert row["stored_knowledge_context"]["request_membership"] == "not_recorded"
    assert not row["stored_knowledge_context"]["relationships"]


def test_request_coverage_and_counts_are_scoped_to_the_declared_area():
    search = {
        "source": "Europe PMC",
        "identifier": "P52270",
        "status": "added",
        "count": 20,
        "uniprot_mention_count": 20,
    }
    annotations = {
        "source": "Europe PMC",
        "identifier": "MED:1",
        "status": "added",
        "count": 5,
        "uniprot_mention_count": 3,
        "structure_mention_count": 2,
        "data": "located_accession_annotations",
    }
    from sabueso.mappings.europepmc import ANNOTATION_MAPPING

    annotations["mapping"] = ANNOTATION_MAPPING
    card = synthetic(search, annotations)
    _, direct = select(card, "relationships.mentioned_in", "Europe PMC")
    _, structural = select(card, "relationships.structure_mentioned_in", "Europe PMC")
    assert direct["row"]["count"] == 23 and structural["row"]["count"] == 2
    assert direct["classification_inputs"]["count_field"] == "uniprot_mention_count"
    assert (
        structural["classification_inputs"]["count_field"] == "structure_mention_count"
    )
    assert structural["classification_inputs"]["enrichment_indexes"] == [1]
    search_only = synthetic(search)
    _, unqueried = select(
        search_only, "relationships.structure_mentioned_in", "Europe PMC"
    )
    assert unqueried["row"]["state"] == "not_queried"
    assert unqueried["classification_inputs"]["reports"] == []
    assert (
        "explicit article_ids"
        in unqueried["classification_inputs"]["not_queried_detail"]
    )


def test_enrichment_count_is_reported_not_reconstructed_from_related_assertions():
    card = synthetic(
        {
            "source": "ChEMBL",
            "identifier": "target",
            "status": "added",
            "count": 7,
            "version": "original",
        },
        {
            "source": "ChEMBL",
            "identifier": "other target",
            "status": "error",
            "detail": "original error",
        },
    )
    identifier = assertion(card, "relationships.has_bioactivity", "activity", "ChEMBL")
    rel = make_relationship(
        "uniprot:P52270",
        "has_bioactivity",
        "chembl:CHEMBL1",
        source_assertion_ids=[identifier],
    )
    card.relationship_store.add(rel)
    _, row = select(card, "relationships.has_bioactivity", "ChEMBL")
    assert row["row"]["count"] == 7 and row["row"]["state"] == "partial"
    assert row["row"]["basis"]["unavailable_for"] == ["other target"]
    assert len(row["stored_knowledge_context"]["relationships"]) == 1
    assert row["stored_knowledge_context"]["request_membership"] == "not_recorded"
    assert len(row["classification_inputs"]["reports"]) == 2


def test_selected_field_precedes_request_reports_without_changing_the_rule():
    card = synthetic({"source": "ClinVar", "status": "error"})
    path = "annotations.clinical_variants"
    identifier = assertion(card, path, [{"accession": "synthetic"}], "ClinVar")
    card.set(path, [{"accession": "synthetic"}], [identifier])
    _, row = select(card, path, "ClinVar")
    assert row["row"]["state"] == "known"
    assert row["classification_inputs"]["basis"] == "selected_field"
    assert "reports" not in row["classification_inputs"]


@pytest.mark.parametrize("missing_all", [False, True])
def test_missing_selected_support_is_partial_even_if_no_field_row_survives(missing_all):
    card = synthetic()
    path = "annotations.clinical_variants"
    identifier = assertion(card, path, ["synthetic"], "ClinVar")
    card.set(path, ["synthetic"], [identifier, "SA_missing"])
    if missing_all:
        card.source_assertion_store.store.pop(identifier)
    answer = card.explain_knowledge_state(path)
    assert answer["status"] == "partial"
    assert any(g["reason"] == "missing_source_assertion" for g in answer["gaps"])
    assert bool(answer["unclassified_fields"]) == missing_all


def test_nonprotein_records_and_missing_source_names_follow_original_classification():
    card = synthetic(
        {"status": "not_found"},
        {"source": "ChEMBL", "status": "added", "count": 1},
        entity_type="small_molecule",
    )
    answer = card.explain_knowledge_state()
    assert [r["row"] for r in answer["rows"]] == card.knowledge_state()["rows"]
    unknown = next(r for r in answer["rows"] if r["row"]["source"] == "unknown")
    assert unknown["classification_inputs"]["reports"][0]["record"] == {
        "status": "not_found"
    }


def test_a_relationship_that_loses_all_support_does_not_hide_behind_not_stated():
    card = synthetic()
    anchor = assertion(card, "identifiers.uniprot", "P52270")
    card.set("identifiers.uniprot", "P52270", [anchor])
    rel = make_relationship(
        "uniprot:P52270",
        "interacts_with",
        "uniprot:P60174",
        source_assertion_ids=["SA_missing"],
    )
    card.relationship_store.add(rel)
    answer, row = select(card, "relationships.interacts_with", "UniProt")
    assert row["row"]["state"] == "not_stated"  # unchanged classification rule
    assert answer["status"] == "partial"
    (unknown,) = answer["unclassified_relationships"]
    assert unknown["relationship"]["relationship"]["id"] == rel["id"]
    assert unknown["relationship"]["source_assertions"][0]["found"] is False


def test_missing_conflict_support_is_reported_without_discarding_groups():
    card = synthetic()
    path = "annotations.function"
    identifier = assertion(card, path, "synthetic")
    card.set(path, "synthetic", [identifier])
    card.quality["conflicts"] = [
        {"field": path, "source_assertion_ids": [[identifier], ["SA_missing"]]}
    ]
    answer, row = select(card, path, "UniProt")
    assert answer["status"] == "partial" and row["row"]["state"] == "conflicting"
    assert row["field"]["conflicts"] == card.quality["conflicts"]
    assert any(not a["found"] for a in row["field"]["context_source_assertions"])


def test_historical_pin_restores_original_reports_and_exact_item_support(
    public_card, tmp_path
):
    public_card = Card.from_dict(public_card.to_dict())
    public_card.quality["enrichments"] = [
        {"source": "ChEMBL", "status": "added", "count": 2, "version": "original"}
    ]
    store = sabueso.KnowledgeStore(tmp_path / "states.db")
    pin = store.save(public_card)
    expected = public_card.explain_knowledge_state()
    later = Card.from_dict(public_card.to_dict())
    later.quality["enrichments"] = [{"source": "ChEMBL", "status": "error"}]
    store.save(later)
    actual = store.load(pin).explain_knowledge_state()
    assert actual == expected
    for row in actual["rows"]:
        links = (
            row.get("relationships")
            or (row.get("stored_knowledge_context") or {}).get("relationships")
            or []
        )
        for link in links:
            assert store.relationship(link["relationship_ref"]) == link["relationship"]
            for assertion in link["source_assertions"]:
                assert (
                    store.source_assertion(assertion["source_assertion_ref"])[
                        "asserted_value"
                    ]
                    == assertion["asserted_value"]
                )
        field = row.get("field") or (row.get("consultation") or {}).get("anchor") or {}
        for assertion in field.get("source_assertions") or []:
            assert (
                store.source_assertion(assertion["source_assertion_ref"])[
                    "asserted_value"
                ]
                == assertion["asserted_value"]
            )
        for report in row["classification_inputs"].get("reports") or []:
            locator = report["locator"]
            assert (
                store.load(locator["card_ref"]).quality["enrichments"][locator["index"]]
                == report["record"]
            )


@pytest.mark.parametrize(
    "versions,expected",
    [(("120", "121"), "120; 121"), (("120", None), "120"), ((None, None), None)],
)
def test_multiple_uniprot_versions_keep_original_support_and_historical_release_scope(
    versions, expected, tmp_path
):
    cards = []
    for order in ((0, 1), (1, 0)):
        card = synthetic()
        ids = []
        for i in order:
            made = make_source_assertion(
                "identifiers.uniprot",
                "P52270",
                "UniProt",
                f"synthetic-record-{i}",
                "2026-01-01",
            )
            made["source"]["version"] = versions[i]
            card.source_assertion_store.add(made)
            ids.append(made["id"])
        card.set("identifiers.uniprot", "P52270", ids)
        cards.append(card)
    assert cards[0].knowledge_state() == cards[1].knowledge_state()
    card = cards[0]
    before = card.to_dict()
    answer, row = select(card, "annotations.function", "UniProt")
    assert row["row"]["release"] == expected and row["row"]["state"] == "not_stated"
    assert {
        a["version"] for a in row["consultation"]["anchor"]["source_assertions"]
    } == set(versions)
    store = sabueso.KnowledgeStore(tmp_path / "versions.db")
    pin = store.save(card)
    assert (
        store.load(pin).explain_knowledge_state("annotations.function", "UniProt")
        == answer
    )
    assert card.to_dict() == before and card.pinned_ref() == pin


@pytest.mark.parametrize("argument", ["knowledge_area", "knowledge_source"])
@pytest.mark.parametrize("invalid", ["", "  ", 7, [], {}])
def test_selectors_refuse_invalid_shapes(public_card, argument, invalid):
    with pytest.raises(ArgumentError):
        public_card.explain_knowledge_state(**{argument: invalid})


def test_unknown_selectors_are_not_on_card_not_absence_and_arguments_are_digested(
    public_card,
):
    answer = public_card.explain_knowledge_state("unknown area", "unknown source")
    assert (
        answer["status"] == "not_on_card"
        and answer["reason"] == "no_matching_state_row"
    )
    assert not answer["rows"]
    assert public_card.explain_knowledge_state(
        " annotations.subunit ", " UniProt "
    ) == public_card.explain_knowledge_state("annotations.subunit", "UniProt")
    with pytest.raises(argdigest.UnknownArgumentError):
        public_card.explain_knowledge_state(surprise=True)
    with pytest.raises(StorageError):
        Card().explain_knowledge_state()
