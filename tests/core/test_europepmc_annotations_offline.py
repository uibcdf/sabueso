"""Located accession mentions retain source-native locators, not scientific claims."""

import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import pytest

from sabueso.core.errors import ArgumentError, ConnectorError, RecordNotFoundError
from sabueso.tools.db import europepmc


def test_public_figure_mention_has_its_provider_and_quote_fragments():
    response = europepmc.get_annotations(
        "pmc:pmc12400196", client=europepmc.FixtureEuropePMCClient("temp_data")
    )
    assert response["query"] == {
        "article_ids": ["PMC:PMC12400196"],
        "type": "Accession Numbers",
    }
    assert response["version"] is None  # An API version is not an extractor version.
    assert response["retrieved_at"] == "2026-10-02"
    (article,) = response["record"]
    # The API returns MED for a PMC query. Neither id is replaced or inferred.
    assert (article["source"], article["extId"], article["pmcid"]) == (
        "MED",
        "40832834",
        "PMC12400196",
    )
    (mention,) = [
        a
        for a in article["annotations"]
        if a["subType"] == "UniProt" and a["exact"] == "P60174"
    ]
    assert (
        mention["section"] == "Figure (http://semanticscience.org/resource/SIO_000080)"
    )
    assert mention["provider"] == "Europe PMC"
    assert mention["id"].startswith("http://europepmc.org/article/PMC/PMC12400196#")
    assert mention["tags"] == [
        {"name": "P60174", "uri": "http://identifiers.org/uniprot:P60174"}
    ]
    assert mention["prefix"] == "Y5) and H. sapiens (Swiss-Prot entry "
    assert mention["postfix"] == "). "
    assert "sentence" not in mention


def test_no_annotations_is_preserved_without_claiming_no_mention():
    response = europepmc.get_annotations(
        "MED:18562316", client=europepmc.FixtureEuropePMCClient("temp_data")
    )
    assert response["record"] == [
        {"source": "MED", "extId": "18562316", "annotations": []}
    ]


def test_explicit_batch_normalizes_and_deduplicates_ids():
    response = europepmc.get_annotations(
        [" PMC:PMC12400196 ", "MED:18562316", "pmc:pmc12400196"],
        client=europepmc.FixtureEuropePMCClient("temp_data"),
    )
    assert len(response["record"]) == 2
    assert response["query"]["article_ids"] == ["PMC:PMC12400196", "MED:18562316"]


@pytest.mark.parametrize(
    "ids",
    [
        None,
        [],
        {},
        3,
        [3],
        [""],
        "P60174",
        "MED:0",
        "PMC:12400196",
        "MED:18562316&type=Genes",
    ],
)
def test_wrong_article_ids_are_refused_before_network_access(ids):
    with pytest.raises(ArgumentError):
        europepmc.get_annotations(ids)


def test_saved_answer_not_present_is_distinct_from_an_empty_answer():
    with pytest.raises(RecordNotFoundError, match="No saved"):
        europepmc.get_annotations(
            "MED:1", client=europepmc.FixtureEuropePMCClient("temp_data")
        )
    with pytest.raises(ConnectorError, match="simulated"):
        europepmc.get_annotations(
            "MED:18562316",
            client=europepmc.FixtureEuropePMCClient(
                "temp_data", failing={"MED:18562316"}
            ),
        )


def _answer(value):
    return io.BytesIO(json.dumps(value).encode("utf-8"))


def test_online_access_batches_explicit_ids_and_preserves_returned_ids(monkeypatch):
    seen = []
    answer = [
        {
            "source": "MED",
            "extId": "40832834",
            "pmcid": "PMC12400196",
            "annotations": [],
        }
    ]

    def fake(req, timeout, expect_json):
        seen.append(parse_qs(urlparse(req.full_url).query))
        assert timeout == 7 and expect_json is True
        return _answer(answer)

    monkeypatch.setattr(europepmc, "urlopen", fake)
    ids = ["PMC:PMC12400196", *[f"MED:{i}" for i in range(1, 10)]]
    response = europepmc.get_annotations(ids, client=europepmc.OnlineEuropePMCClient(7))
    assert [s["articleIds"][0].split(",") for s in seen] == [ids[:8], ids[8:]]
    assert all(s["type"] == ["Accession Numbers"] for s in seen)
    assert response["record"] == answer + answer
    assert response["version"] is None


@pytest.mark.parametrize(
    "answer", [[], [{"source": "MED", "extId": "1", "annotations": []}]]
)
def test_empty_online_answers_remain_answers(monkeypatch, answer):
    monkeypatch.setattr(europepmc, "urlopen", lambda *a, **kw: _answer(answer))
    assert europepmc.get_annotations("MED:1")["record"] == answer


@pytest.mark.parametrize(
    "answer", [{}, [{"annotations": {}}], [None], [{"annotations": [None]}]]
)
def test_malformed_annotation_records_are_source_errors(monkeypatch, answer):
    monkeypatch.setattr(europepmc, "urlopen", lambda *a, **kw: _answer(answer))
    with pytest.raises(ConnectorError, match="unreadable"):
        europepmc.get_annotations("MED:1")


@pytest.mark.parametrize(
    "error",
    [
        HTTPError("https://example.org", 404, "missing", {}, None),
        URLError("offline"),
        TimeoutError("slow"),
    ],
)
def test_network_failure_does_not_become_an_empty_annotation_answer(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(europepmc, "urlopen", fail)
    with pytest.raises(ConnectorError):
        europepmc.get_annotations("MED:1")
