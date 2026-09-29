"""How each statement entered (#92): imported from a database, curated from a
publication, or extracted from a text by a named tool or model."""

import json
import warnings

import pytest

from sabueso.core.card import Card
from sabueso.core.errors import SchemaError
from sabueso.core.source_assertion_store import (
    acquisition_of,
    make_acquisition,
    make_source_assertion,
)


@pytest.fixture(scope="module")
def hstim():
    import sabueso
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.diseases import FixtureDISEASESClient

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        card, _ = sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            diseases={"channels": ["knowledge", "textmining"]},
            diseases_client=FixtureDISEASESClient("temp_data"),
        )
    card.add_literature_assertion(
        "annotations.subunit", "Homodimer.", "pubmed:18562316", "a curator"
    )
    return card


def test_every_statement_says_how_it_entered(hstim):
    report = hstim.acquisition()
    assert set(report["methods"]) == {"database", "curation"}
    assert report["methods"]["curation"] == {"Literature": 1}
    assert report["methods"]["database"]["UniProt"] > 0
    assert report["extractions"] == []


def test_a_database_that_states_its_record_was_mined_from_text_says_so(hstim):
    # DISEASES's text-mining channel: imported from a database, mined from text.
    report = hstim.acquisition()
    assert set(report["origins"]) == {"text_mining"}
    assert set(report["origins"]["text_mining"]) == {"DISEASES"}
    by_channel = {}
    for rel in hstim.relationships("associated_with"):
        for sa_id in rel["source_assertion_ids"]:
            sa = hstim.source_assertion_store.get(sa_id)
            by_channel.setdefault(rel["qualifiers"]["channel"], set()).add(
                json.dumps(sa["acquisition"], sort_keys=True)
            )
    assert by_channel["textmining"] == {
        '{"method": "database", "origin": "text_mining"}'
    }
    assert by_channel["knowledge"] == {'{"method": "database"}'}


def test_explain_says_how_a_statement_entered(hstim):
    curated = hstim.source_assertion_store.find_by_field("annotations.subunit")
    ids = [sa["id"] for sa in curated]
    methods = {e["acquisition"]["method"] for e in hstim.explain(ids)}
    assert methods == {"database", "curation"}


def test_an_extraction_names_its_tool_and_version():
    record = make_acquisition(
        "rule_extraction", tool="a tagger", version="1.2", configuration={"x": 1}
    )
    assert record == {
        "method": "rule_extraction",
        "tool": "a tagger",
        "version": "1.2",
        "configuration": {"x": 1},
    }
    with pytest.raises(SchemaError):
        make_acquisition("model_extraction", tool="a model")  # no version
    with pytest.raises(SchemaError):
        make_acquisition("database", tool="a tagger")
    with pytest.raises(SchemaError):
        make_acquisition("curation", origin="text_mining")
    with pytest.raises(SchemaError):
        make_acquisition("guessing")


def test_extracted_statements_are_counted_by_extractor_and_never_as_curated():
    card = Card.from_dict(
        json.loads(
            open(
                "temp_data/frozen_cards/schema_0.3.6__P60174.json", encoding="utf-8"
            ).read()
        )
    )
    sa = make_source_assertion(
        "annotations.subunit",
        "Homodimer.",
        "A text-mining source",
        "PMC1",
        "2026-09-29",
        source_type="literature",
        acquisition=make_acquisition("rule_extraction", tool="a tagger", version="1"),
    )
    card.source_assertion_store.add(sa)
    report = card.acquisition()
    assert report["extractions"] == [
        {
            "method": "rule_extraction",
            "tool": "a tagger",
            "version": "1",
            "validated": False,
            "count": 1,
        }
    ]
    assert "curation" not in report["methods"]


def test_a_card_stored_before_acquisition_was_recorded_says_not_recorded():
    card = Card.from_dict(
        json.loads(
            open(
                "temp_data/frozen_cards/schema_0.3.6__P60174.json", encoding="utf-8"
            ).read()
        )
    )
    assert set(card.acquisition()["methods"]) == {"not_recorded"}
    (sa,) = card.source_assertion_store.to_list()[:1]
    assert acquisition_of(sa) == {"method": "not_recorded"}


def test_a_packet_reports_how_its_sources_statements_entered(hstim):
    from sabueso.core.packets import _provenance

    diseases = _provenance(hstim)["sources"]["DISEASES"]["acquisition"]
    assert set(diseases) == {"database", "database (text_mining)"}
    assert _provenance(hstim)["sources"]["Literature"]["acquisition"] == {"curation": 1}
