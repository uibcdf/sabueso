"""Structural access retains revisions, partial outcomes and original bibliography."""

import io
import json
from datetime import timedelta
from email.message import Message
from functools import partial
from pathlib import Path
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso._private.smonitor.warnings import AttributionTrackingWarning
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, rcsb


@pytest.fixture(autouse=True)
def independent_workflow():
    # Synthetic metadata in one test must not change another workflow's references.
    with ackredit.session("independent structural test"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def entry(pdb_id="1HTI"):
    return json.loads(Path(f"temp_data/rcsb/{pdb_id}.json").read_text())


def revised(pdb_id="1HTI"):
    record = entry(pdb_id)
    # Synthetic API metadata exercises zero minor revisions without changing fixtures.
    record["rcsb_accession_info"].update(
        major_revision=1, minor_revision=0, revision_date="2024-02-07T00:00:00Z"
    )
    record["rcsb_primary_citation"]["rcsb_authors"] = ["Mande, S.C.", "Hol, W.G."]
    return record


def lookup(pdb_ids, *, client=None):
    with sabueso.attribution() as run:
        result = (client or rcsb.OnlineRCSBClient()).fetch_structures(pdb_ids)
    (record,) = run.acquisitions
    return result, record


def test_fixture_entry_owns_detached_trace_and_original_citation():
    with ackredit.session("structure fixture"):
        response = rcsb.get_entry("1hti", client=rcsb.FixtureRCSBClient("temp_data"))
        (record,) = response["acquisition_trace"]["records"]
        assert response["record"] == entry()
        assert response["version"] is None
        assert record["source"] == "RCSB PDB" and record["operation"] == "structure"
        assert record["outcome"] == "received" and record["network_attempts"] == 0
        assert record["source_version"] == {"value": None, "basis": "not_stated"}
        assert (
            record["entries"][0]["primary_citation"] == entry()["rcsb_primary_citation"]
        )
        bibliography = record["bibliography"]
        description = next(
            b for b in bibliography if b["id"] == "doi:10.1093/nar/gkae1091"
        )
        assert len(description["authors"]) == 51 and description["year"] == 2025
        primary = next(
            b
            for b in bibliography
            if b.get("url") == "https://pubmed.ncbi.nlm.nih.gov/8061610/"
        )
        assert primary["title"] == entry()["rcsb_primary_citation"]["title"]
        assert "authors" not in primary
        assert any(
            "authors" in g.get("fields", []) for g in record["bibliography_gaps"]
        )
        assert record["provider"]["status"] == "available"
        assert ackredit.get_attribution().to_dict()["items"]


def test_native_revision_and_authors_are_not_a_database_release(monkeypatch):
    original, calls = revised(), []

    def serve(request, timeout):
        calls.append(json.loads(request.data))
        return Response({"data": {"entry": original}})

    monkeypatch.setattr(_http, "_urlopen", serve)
    response = rcsb.get_entry("1HTI")
    (record,) = response["acquisition_trace"]["records"]
    assert response["record"] == original
    assert record["source_version"] == {
        "value": {
            "major_revision": 1,
            "minor_revision": 0,
            "revision_date": "2024-02-07T00:00:00Z",
        },
        "basis": "entry_revision",
    }
    assert response["version"] is None  # the envelope claims no database release
    assert record["access"] == "network" and record["network_attempts"] == 1
    assert calls[0]["variables"] == {"id": "1HTI"}
    assert "minor_revision" in calls[0]["query"] and "rcsb_authors" in calls[0]["query"]
    primary = next(
        b
        for b in record["bibliography"]
        if b.get("url") == "https://pubmed.ncbi.nlm.nih.gov/8061610/"
    )
    assert primary["authors"] == original["rcsb_primary_citation"]["rcsb_authors"]
    assert record["requests"][0]["request_sha256"]
    assert record["requests"][0]["response_sha256"]


@pytest.mark.parametrize("mode", ["reuse", "replay"])
@pytest.mark.parametrize("batch", [False, True])
def test_reused_entry_or_batch_keeps_versions_bytes_and_original_retrieval(
    tmp_path, monkeypatch, mode, batch
):
    original, calls = revised(), []

    def serve(request, timeout):
        calls.append(request)
        return Response(
            {"data": {"entries": [original]} if batch else {"entry": original}}
        )

    monkeypatch.setattr(_http, "_urlopen", serve)
    archive = sabueso.RetrievalArchive(tmp_path / "structural.db")

    def read():
        if batch:
            return lookup(["1HTI"])
        response = rcsb.get_entry("1HTI")
        return response["record"], response["acquisition_trace"]["records"][0]

    with archive.recording():
        data, initial = read()
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager:
        again, reused = read()
    assert len(calls) == 1 and data == again
    assert reused["access"] == mode and reused["network_attempts"] == 0
    assert reused["id"] != initial["id"]
    for key in ("retrieved_at", "source_version", "response_identity", "entries"):
        assert reused[key] == initial[key]
    assert (
        reused["requests"][0]["retrieval_ref"]
        == initial["requests"][0]["retrieval_ref"]
    )
    assert (
        reused["requests"][0]["response_sha256"]
        == initial["requests"][0]["response_sha256"]
    )


@pytest.mark.parametrize("batch", [False, True])
def test_empty_graphql_answers_are_completed_access_not_failed_requests(
    monkeypatch, batch
):
    monkeypatch.setattr(
        _http,
        "_urlopen",
        lambda *a, **k: Response(
            {"data": {"entries": []} if batch else {"entry": None}}
        ),
    )
    with ackredit.session("empty structures"):
        if batch:
            result, record = lookup(["1HTI", "1KLG"])
            assert all(
                isinstance(value, RecordNotFoundError) for value in result.values()
            )
            assert record["completed_ids"] == ["1HTI", "1KLG"]
            assert all(e["outcome"] == "empty" for e in record["entries"])
        else:
            with pytest.raises(RecordNotFoundError) as caught:
                rcsb.get_entry("1HTI")
            (record,) = caught.value.acquisition_trace["records"]
        assert record["outcome"] == "empty" and record["count"] == 0
        assert record["retrieved_at"]
        assert (
            record["network_attempts"] == 1
            and record["provider"]["status"] == "available"
        )
        ids = {b["id"] for b in record["bibliography"]}
        assert "doi:10.1093/nar/gkae1091" in ids and not any(
            i.startswith("sabueso:rcsb-primary-citation:") for i in ids
        )


def test_missing_fixture_and_empty_query_receive_no_completed_access_credit(tmp_path):
    with ackredit.session("not available"):
        with pytest.raises(RecordNotFoundError) as caught:
            rcsb.get_entry("1HTI", client=rcsb.FixtureRCSBClient(tmp_path))
        (missing,) = caught.value.acquisition_trace["records"]
        _, batch = lookup(["1HTI"], client=rcsb.FixtureRCSBClient(tmp_path))
        result, empty = lookup([], client=rcsb.FixtureRCSBClient(tmp_path))
        assert result == {} and empty["outcome"] == "not_queried"
        for record in (missing, batch, empty):
            assert record["network_attempts"] == 0
            assert record["provider"]["status"] == "not_attempted"
        assert missing["outcome"] == batch["outcome"] == "unavailable"
        assert not ackredit.get_attribution().to_dict()["items"]


def test_one_logical_batch_preserves_received_empty_and_failed_entries(monkeypatch):
    def serve(request, timeout):
        data = json.loads(request.data)
        if "ids" in data["variables"]:
            return Response({"data": {"entries": [revised(), None]}})
        if data["variables"]["id"] == "1KLG":
            return Response({"data": {"entry": None}})
        raise URLError(TimeoutError("structure service timed out"))

    monkeypatch.setattr(_http, "_urlopen", serve)
    result, record = lookup(["1hti", "1KLG", "4UNK", "1HTI"])
    assert result["1HTI"][0] == revised()
    assert isinstance(result["1KLG"], RecordNotFoundError)
    assert isinstance(result["4UNK"], ConnectorError)
    assert record["query"] == {"pdb_ids": ["1HTI", "1KLG", "4UNK"]}
    assert record["outcome"] == "partial" and record["count"] == 1
    assert record["network_attempts"] == 3 and len(record["requests"]) == 3
    assert [e["outcome"] for e in record["entries"]] == ["received", "empty", "failed"]
    assert record["completed_ids"] == ["1HTI", "1KLG"]
    assert record["source_version"]["basis"] == "per_entry_revision"
    assert set(record["source_version"]["value"]) == {"1HTI"}
    assert record["provider"]["status"] == "available"
    json.dumps(record)  # returned exception objects never leak into the host record


def test_instance_field_fallback_is_partial_and_keeps_both_transport_answers(
    monkeypatch,
):
    calls = []

    def serve(request, timeout):
        calls.append(json.loads(request.data))
        payload = {"data": {"entry": revised()}}
        if len(calls) == 1:
            payload["errors"] = [
                {
                    "path": [
                        "entry",
                        "polymer_entities",
                        0,
                        "polymer_entity_instances",
                    ],
                    "message": "instance unavailable",
                }
            ]
        return Response(payload)

    monkeypatch.setattr(_http, "_urlopen", serve)
    response = rcsb.get_entry("1HTI")
    (record,) = response["acquisition_trace"]["records"]
    assert record["outcome"] == "partial" and record["count"] == 1
    assert record["entries"][0]["partial"] == response["record"]["_partial"]
    assert record["network_attempts"] == 2 and record["received_responses"] == 2
    assert (
        calls[0]["query"] == rcsb.STRUCTURE_QUERY
        and calls[1]["query"] == rcsb.PARTIAL_QUERY
    )
    assert (
        record["requests"][0]["response_sha256"]
        != record["requests"][1]["response_sha256"]
    )
    assert record["provider"]["status"] == "available"


def test_generator_input_is_batched_once_without_duplicate_fallback_events(monkeypatch):
    calls = []

    def serve(request, timeout):
        variables = json.loads(request.data)["variables"]
        calls.append(variables)
        return Response(
            {"data": {"entries": [{"rcsb_id": p} for p in variables["ids"]]}}
        )

    monkeypatch.setattr(_http, "_urlopen", serve)
    result, record = lookup((f"{i:04d}" for i in range(30)))
    assert len(result) == record["count"] == 30
    assert [len(c["ids"]) for c in calls] == [25, 5]
    assert record["network_attempts"] == 2 and record["outcome"] == "received"
    assert record["query"]["pdb_ids"] == list(result)


def test_failed_batch_keeps_failed_transport_and_successful_single_fallback(
    monkeypatch,
):
    def serve(request, timeout):
        variables = json.loads(request.data)["variables"]
        if "ids" in variables or variables["id"] == "1KLG":
            raise URLError(TimeoutError("source timeout"))
        return Response({"data": {"entry": revised()}})

    monkeypatch.setattr(_http, "_urlopen", serve)
    result, record = lookup(["1HTI", "1KLG"])
    assert isinstance(result["1KLG"], ConnectorError)
    assert record["outcome"] == "partial" and record["count"] == 1
    assert record["completed_ids"] == ["1HTI"]
    assert [r["outcome"] for r in record["requests"]] == [
        "failed",
        "received",
        "failed",
    ]
    assert (
        record["network_attempts"] == 3 and record["provider"]["status"] == "available"
    )


def test_wholly_failed_batch_and_replay_misses_do_not_credit_completion(
    tmp_path, monkeypatch
):
    def fail(*args, **kwargs):
        raise URLError(TimeoutError("source timeout"))

    monkeypatch.setattr(_http, "_urlopen", fail)
    with ackredit.session("failed lookup"):
        _, failed = lookup(["1HTI", "1KLG"])
        assert failed["outcome"] == "failed" and failed["network_attempts"] == 3
        archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
        with archive.replaying():
            _, absent = lookup(["1HTI", "1KLG"])
        assert absent["outcome"] == "not_queried" and absent["network_attempts"] == 0
        for record in (failed, absent):
            assert record["count"] == 0 and record["completed_ids"] == []
            assert record["provider"]["status"] == "not_attempted"
        assert not ackredit.get_attribution().to_dict()["items"]


def test_transient_retry_keeps_attempts_and_does_not_duplicate_resource_use(
    monkeypatch,
):
    calls = []

    def serve(request, timeout):
        calls.append(request)
        if len(calls) == 1:
            raise HTTPError(request.full_url, 503, "busy", Message(), None)
        return Response({"data": {"entry": revised()}})

    monkeypatch.setattr(_http, "_urlopen", serve)
    monkeypatch.setattr(rcsb, "urlopen", partial(_http.urlopen, sleep=lambda _: None))
    response = rcsb.get_entry("1HTI")
    (record,) = response["acquisition_trace"]["records"]
    assert record["network_attempts"] == 2 and record["requests"][0]["retries"] == [
        "HTTP 503"
    ]
    assert record["outcome"] == "received" and len(record["entries"]) == 1


def test_card_refresh_and_composition_keep_structural_intake_separate_from_payload(
    tmp_path,
):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"),
        rcsb_client=rcsb.FixtureRCSBClient("temp_data"),
    )
    with ackredit.session("structural workflow"), sabueso.attribution() as run:
        card, resolution = sabueso.resolve(
            "P60174", resolver=resolver, structures=["1HTI", "1KLG"]
        )
        trace = card.acquisition_trace
        assert trace == resolution.acquisition_trace
        assert trace["card_ref"] == card.pinned_ref()
        assert [r["source"] for r in trace["records"]] == ["UniProt", "RCSB PDB"]
        structural = trace["records"][1]
        assert structural["count"] == 2 and structural["network_attempts"] == 0
        assert (
            structural["entries"][0]["primary_citation"]
            == entry()["rcsb_primary_citation"]
        )
        before = len(run.acquisitions)
        packet = sabueso.compose_packet(
            sabueso.KnowledgeQuery("P60174", aspects=["structures"]), card
        )
        assert len(run.acquisitions) == before and packet.acquisition_trace is None
        assert "doi:10.1093/nar/gkae1091" in {
            b["id"] for b in packet.attribution["bibliography"]
        }
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    store.save(card)
    refreshed, resolution = sabueso.refresh_card(card, resolver=resolver, store=store)
    assert refreshed.acquisition_trace == resolution.acquisition_trace
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert refreshed.acquisition_trace["records"][1]["id"] != structural["id"]
    assert card.acquisition_trace == trace
    trace["records"][1]["entries"].clear()
    assert card.acquisition_trace["records"][1]["entries"]
    assert "acquisition_trace" not in card.to_dict()
    assert Card.from_dict(card.to_dict()).acquisition_trace is None


def test_saved_versions_and_citations_render_without_new_credit(monkeypatch):
    response = rcsb.get_entry("1HTI", client=rcsb.FixtureRCSBClient("temp_data"))
    saved = json.dumps(response["acquisition_trace"])
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: pytest.fail("saved reading cannot load provider"),
    )
    with ackredit.session("reader"), sabueso.attribution() as reader:
        (record,) = json.loads(saved)["records"]
        attribution = ackredit.Attribution.from_dict(record["provider"]["attribution"])
        assert "10.1093/nar/gkae1091" in attribution.report(format="bibtex")
        assert "8061610" in attribution.report(format="csl-json")
        assert (
            not reader.acquisitions
            and not ackredit.get_attribution().to_dict()["items"]
        )


def test_different_primary_metadata_is_retained_within_one_workflow(monkeypatch):
    with ackredit.capture("different source versions") as workflow:
        fixture = rcsb.get_entry("1HTI", client=rcsb.FixtureRCSBClient("temp_data"))
        monkeypatch.setattr(
            _http, "_urlopen", lambda *a, **k: Response({"data": {"entry": revised()}})
        )
        online = rcsb.get_entry("1HTI")
        for response in (fixture, online):
            assert (
                response["acquisition_trace"]["records"][0]["provider"]["status"]
                == "available"
            )
    forms = [
        item
        for item in workflow.attribution.to_dict()["items"]
        if item.get("url") == "https://pubmed.ncbi.nlm.nih.gov/8061610/"
    ]
    assert len(forms) == 2 and len({item["id"] for item in forms}) == 2
    assert sorted("authors" in item for item in forms) == [False, True]


def test_provider_failure_preserves_entry_and_host_citations(monkeypatch):
    def broken():
        raise ImportError("broken provider")

    monkeypatch.setattr(adapter, "_load_backend", broken)
    with pytest.warns(AttributionTrackingWarning):
        response = rcsb.get_entry("1HTI", client=rcsb.FixtureRCSBClient("temp_data"))
    assert response["record"] == entry()
    (record,) = response["acquisition_trace"]["records"]
    assert record["outcome"] == "received" and record["provider"]["status"] == "failed"
    assert any(
        b.get("url") == "https://pubmed.ncbi.nlm.nih.gov/8061610/"
        for b in record["bibliography"]
    )


def test_custom_rcsb_client_is_not_inferred_as_observed_access():
    class Custom:
        def fetch_structure(self, pdb_id):
            return entry(), "original"

    with ackredit.session("custom lookup"):
        response = rcsb.get_entry("1HTI", client=Custom())
        assert response["acquisition_trace"]["records"] == []
        assert (
            response["acquisition_trace"]["coverage"][
                "other_sources_and_custom_clients"
            ]
            == "not_observed"
        )
        assert not ackredit.get_attribution().to_dict()["items"]
