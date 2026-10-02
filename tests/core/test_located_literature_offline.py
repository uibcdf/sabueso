"""An explicit public article's located mention survives storage and rebuilding."""

from copy import deepcopy

import pytest

import sabueso
from sabueso.core.errors import ArgumentError
from sabueso.core.migration import rebuild_options
from sabueso.core.snapshot import pinned_ref
from sabueso.enrichers import ENRICHERS
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient

ARTICLE = "PMC:PMC12400196"


def resolve(articles=ARTICLE, client=None, **options):
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": articles},
        europepmc_client=client or FixtureEuropePMCClient("temp_data"),
        **options,
    )[0]


def records(card):
    return [e for e in card.quality["enrichments"] if e["source"] == "Europe PMC"]


def test_public_figure_mention_is_supported_by_its_own_source_statement():
    card = resolve()
    (rel,) = card.relationships("mentioned_in")
    assert rel["object_ref"] == "pubmed:40832834"
    assert rel["subject_ref"] == "uniprot:P60174"
    (location,) = rel["qualifiers"]["locations"]
    original = FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"][0]
    annotation = next(a for a in original["annotations"] if a["exact"] == "P60174")
    assert location["annotation"] == annotation
    assert "sentence" not in location["annotation"]
    identifier = location["source_assertion_id"]
    assert rel["source_assertion_ids"] == [identifier]
    assertion = card.source_assertion_store.get(identifier)
    assert assertion["asserted_value"]["annotation"] == annotation
    assert assertion["source"]["name"] == "Europe PMC"
    assert assertion["source"].get("version") is None
    assert assertion["acquisition"] == {"method": "database", "origin": "text_mining"}
    metadata = assertion["source_metadata"]
    assert metadata["requested_article"] == ARTICLE
    assert metadata["identity_basis"]["kind"] == "stated_uniprot_accession"
    assert metadata["identity_basis"]["tags"] == annotation["tags"]
    assert metadata["article"]["pmcid"] == "PMC12400196"
    assert metadata["article"]["fullTextIdList"] == ["PMC12400196"]
    publication = next(
        p
        for p in card.literature()["publications"]
        if p["publication_ref"] == rel["object_ref"]
    )
    assert publication["mentions"][0]["locations"] == [location]
    assert not publication["curated"] and not publication["supports"]
    publication["mentions"][0]["locations"][0]["annotation"]["exact"] = "changed"
    assert (
        card.source_assertion_store.get(identifier)["asserted_value"]["annotation"]
        == annotation
    )


def test_round_trip_refresh_and_historical_assertion_reads(tmp_path):
    card = resolve([ARTICLE, "MED:18562316"])
    before = card.to_dict()
    assert before["meta"]["schema_version"] == "0.3.11"
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(card)
    assert store.load(card.pinned_ref()).to_dict() == before
    (rel,) = card.relationships("mentioned_in")
    identifier = rel["source_assertion_ids"][0]
    historical = pinned_ref(card.id, card.snapshot_id(), identifier)
    assert rebuild_options(card)["europepmc"] == {
        "article_ids": [ARTICLE, "MED:18562316"]
    }
    refreshed, resolution = sabueso.refresh_card(
        card,
        store=store,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc_client=FixtureEuropePMCClient("temp_data"),
    )
    assert resolution is not None
    assert refreshed.relationships("mentioned_in") == card.relationships("mentioned_in")
    assert refreshed.source_assertion_store.get(
        identifier
    ) == card.source_assertion_store.get(identifier)
    assert store.source_assertion(historical) == card.source_assertion_store.get(
        identifier
    )
    assert len(store.history(card.id)) == 2
    assert card.to_dict() == before


def test_requests_are_isolated_and_empty_failure_and_not_asked_stay_distinct():
    client = FixtureEuropePMCClient("temp_data", failing={"MED:2"})
    card = resolve([ARTICLE, "MED:18562316", "MED:1", "MED:2"], client)
    outcomes = records(card)
    assert [r["status"] for r in outcomes] == ["added", "added", "error", "error"]
    assert outcomes[1]["count"] == outcomes[1]["returned_annotations"] == 0
    assert "does not establish absence" in outcomes[1]["detail"]
    assert "No saved" in outcomes[2]["detail"]
    assert "simulated" in outcomes[3]["detail"]
    row = next(
        r
        for r in card.knowledge_state()["rows"]
        if r["area"] == "relationships.mentioned_in" and r["source"] == "Europe PMC"
    )
    assert row["state"] == "partial"
    assert row["basis"]["unavailable_for"] == ["MED:1", "MED:2"]
    bare, _ = sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    row = next(
        r
        for r in bare.knowledge_state()["rows"]
        if r["area"] == "relationships.mentioned_in" and r["source"] == "Europe PMC"
    )
    assert row["state"] == "not_queried"


class Answer:
    def __init__(self, record):
        self.record = record

    def annotations(self, articles):
        return {
            "record": deepcopy(self.record),
            "retrieved_at": "fixture",
            "version": None,
        }


@pytest.mark.parametrize("change", ["name", "tag", "type", "uri"])
def test_names_other_tags_and_wrong_namespaces_never_establish_identity(change):
    record = FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"]
    annotation = next(a for a in record[0]["annotations"] if a["exact"] == "P60174")
    if change == "name":
        annotation["exact"] = "triosephosphate isomerase"
    elif change == "tag":
        annotation["tags"][0]["name"] = "Q9C401"
    elif change == "type":
        annotation["type"] = "Gene_Proteins"
    else:
        annotation["tags"][0]["uri"] = "http://example.org/uniprot:P60174"
    card = resolve(client=Answer(record))
    assert not card.relationships("mentioned_in")
    assert records(card)[0]["returned_annotations"] == 7
    assert records(card)[0]["uniprot_annotation_count"] == 0


@pytest.mark.parametrize(
    "answer",
    [
        [{"source": "MED", "extId": "1", "annotations": []}],
        [
            {
                "source": "MED",
                "extId": "wrong",
                "pmcid": "PMC12400196",
                "annotations": [],
            }
        ],
        [
            {
                "source": "MED",
                "extId": "40832834",
                "pmcid": "PMC12400196",
                "annotations": [None],
            }
        ],
    ],
)
def test_unrelated_or_unreadable_response_is_reported_as_failure(answer):
    card = resolve(client=Answer(answer))
    assert not card.relationships("mentioned_in")
    assert records(card)[0]["status"] == "error"


@pytest.mark.parametrize(
    "options",
    [
        {"article_ids": []},
        {"article_ids": "P60174"},
        {"article_ids": ARTICLE, "limit": 3},
        {"articles": ARTICLE},
    ],
)
def test_wrong_article_options_are_refused(options):
    with pytest.raises(ArgumentError):
        sabueso.resolve("P60174", europepmc=options)


def test_terms_of_fragments_are_unknown_and_profiles_do_not_fetch_them():
    from sabueso.core.terms import retention, verdict

    # Service attribution still governs bibliography. Raw responses may include
    # article fragments, so an archive cannot promise unrestricted sharing.
    assert verdict("Europe PMC", "redistribution")["verdict"] == "allowed"
    assert retention("Europe PMC")["licence"] == "PUBLICATION-TERMS"
    assert retention("Europe PMC")["share"] == "unknown"
    card = resolve()
    report = card.terms("redistribution")
    assert report["sources"]["Europe PMC Annotations"]["verdict"] == "unknown"
    assert report["sources"]["Europe PMC Annotations"]["reason"] == "terms_per_record"
    assert any(
        item["kind"] == "literature_location" for item in report["cards"][0]["unknown"]
    )

    class NoFetch:
        def annotations(self, articles):
            pytest.fail(
                "A terms profile must exclude unknown article terms before fetching"
            )

    card = resolve(client=NoFetch(), terms="commercial")
    assert not card.relationships("mentioned_in")
    assert records(card)[0]["status"] == "not_queried"
    assert "terms_per_record" in records(card)[0]["detail"]
    assert rebuild_options(card)["europepmc"] == {"article_ids": [ARTICLE]}
    assert rebuild_options(card)["terms"] == "commercial"
    refreshed, _ = sabueso.refresh_card(
        card,
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc_client=NoFetch(),
    )
    assert records(refreshed)[0]["status"] == "not_queried"


def test_declared_enricher_keeps_explicit_article_requests_out_of_automatic_search():
    enricher = next(e for e in ENRICHERS if e.option == "europepmc")
    assert enricher.default_request == {}
    assert enricher.areas == (
        "relationships.mentioned_in",
        "relationships.structure_mentioned_in",
    )
    from sabueso.core.migration import _enrichment_options
    from sabueso.enrichers import options_by_source

    assert options_by_source()[("Europe PMC", "located_accession_annotations")] == {
        "europepmc"
    }
    assert "europepmc" in _enrichment_options(resolve().to_dict())
    # A schema migration cannot invent the articles to ask for.
    from sabueso.core.migration import within_line_gaps

    assert not any(
        g["path"].endswith(".locations")
        for g in within_line_gaps(resolve().to_dict(), "0.3.10", "0.3.11")
    )


def test_multiple_occurrences_and_duplicate_annotations_keep_individual_support():
    record = FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"]
    first = next(a for a in record[0]["annotations"] if a["exact"] == "P60174")
    second = {
        **deepcopy(first),
        "id": "https://example.org/annotation/second",
        "section": "Methods",
        "prefix": "The entry ",
    }
    record[0]["annotations"].extend([second, deepcopy(first)])
    card = resolve(client=Answer(record))
    (rel,) = card.relationships("mentioned_in")
    assert len(rel["source_assertion_ids"]) == 2
    assert len(rel["qualifiers"]["locations"]) == 2
    assert records(card)[0]["uniprot_annotation_count"] == 2
    for location in rel["qualifiers"]["locations"]:
        (explanation,) = card.explain([location["source_assertion_id"]])
        assert explanation["asserted_value"]["annotation"] == location["annotation"]


def test_bibliographic_support_does_not_license_attached_fragments():
    card = resolve()
    from sabueso.mappings.europepmc import map_mentions

    mapped = map_mentions(
        {"articles": [{"source": "MED", "id": "40832834", "pmid": "40832834"}]},
        "P60174",
        "fixture",
        "6.9",
    )
    for assertion in mapped["source_assertions"]:
        card.source_assertion_store.add(assertion)
    for relationship in mapped["relationships"]:
        card.relationship_store.add(relationship)
    report = card.terms("redistribution")
    assert report["sources"]["Europe PMC"]["verdict"] == "allowed"
    assert report["sources"]["Europe PMC Annotations"]["verdict"] == "unknown"
    (unknown_location,) = [
        item
        for item in report["cards"][0]["unknown"]
        if item["kind"] == "literature_location" and item["predicate"] == "mentioned_in"
    ]
    assert unknown_location["object_ref"] == "pubmed:40832834"
    assert report["cards"][0]["objects"]["pubmed:40832834"]["status"] == "partial"
    assert not any(
        item["kind"] == "relationship"
        for item in report["cards"][0]["unknown"]
        if item["object_ref"] == "pubmed:40832834"
        and item["predicate"] == "mentioned_in"
    )


def test_different_located_answers_remain_visible_in_literature_and_terms():
    original = FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"]

    class DifferentAnswers:
        def annotations(self, articles):
            record = deepcopy(original)
            if articles == ["MED:40832834"]:
                annotation = next(
                    a for a in record[0]["annotations"] if a["exact"] == "P60174"
                )
                annotation["section"] = "Methods"
            return {"record": record, "retrieved_at": "fixture", "version": None}

    card = resolve([ARTICLE, "MED:40832834"], DifferentAnswers())
    (rel,) = card.relationships("mentioned_in")
    assert len(rel["source_assertion_ids"]) == 2
    assert len(rel["qualifier_conflicts"]["locations"]) == 2
    publication = next(
        p
        for p in card.literature()["publications"]
        if p["publication_ref"] == rel["object_ref"]
    )
    assert (
        publication["mentions"][0]["qualifier_conflicts"] == rel["qualifier_conflicts"]
    )
    locations = [
        item
        for item in card.terms("redistribution")["cards"][0]["unknown"]
        if item["kind"] == "literature_location" and item["predicate"] == "mentioned_in"
    ]
    assert {item["id"] for item in locations} == set(rel["source_assertion_ids"])


def test_missing_locator_parts_stay_unstated_and_full_text_ids_ground_the_request():
    record = FixtureEuropePMCClient("temp_data").annotations([ARTICLE])["record"]
    record[0].pop("pmcid")
    annotation = next(a for a in record[0]["annotations"] if a["exact"] == "P60174")
    for key in ("id", "section", "provider", "prefix", "postfix"):
        annotation[key] = None
    card = resolve(client=Answer(record))
    (rel,) = card.relationships("mentioned_in")
    assert "pmcid" not in rel["qualifiers"]["article"]
    assert rel["qualifiers"]["article"]["fullTextIdList"] == ["PMC12400196"]
    assert rel["qualifiers"]["locations"][0]["annotation"] == annotation
    assert records(card)[0]["status"] == "added"
