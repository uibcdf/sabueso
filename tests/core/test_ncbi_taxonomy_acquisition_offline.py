"""Taxonomy access keeps observed scope separate from absent local inputs."""

import io
import json
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, NotArchivedError, RecordNotFoundError
from sabueso.tools.db import _http, ncbi_taxonomy


@pytest.fixture(autouse=True)
def independent(monkeypatch):
    monkeypatch.delenv("SABUESO_NCBI_KEY", raising=False)
    with ackredit.session("public taxonomy acquisition"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, answer=None):
    calls = []

    def respond(request, timeout):
        calls.append(request)
        ids = [int(t) for t in request.full_url.rsplit("/", 1)[-1].split(",")]
        payload = (
            answer(request, ids, len(calls))
            if answer
            else {
                "taxonomy_nodes": [
                    {"taxonomy": {"tax_id": t, "rank": "SPECIES"}} for t in ids
                ]
            }
        )
        if isinstance(payload, Exception):
            raise payload
        return Response(payload)

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    return calls


def test_batched_generator_scope_and_original_portable_credit(monkeypatch):
    calls = serve(monkeypatch)
    with ackredit.capture("host") as host, sabueso.attribution() as run:
        result = ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa(iter([*range(1, 55), 1]))
    (record,) = run.acquisitions
    assert len(calls) == record["network_attempts"] == 2
    assert record["query"] == {"tax_ids": list(range(1, 55))}
    assert record["count"] == 54 and record["outcome"] == "received"
    assert record["completed_pages"][0]["query"]["tax_ids"] == list(range(1, 51))
    assert record["completed_pages"][1]["query"]["tax_ids"] == [51, 52, 53, 54]
    assert [r["tax_id"] for r in result["record"]] == list(range(1, 55))
    assert record["retrieved_at"] == result["retrieved_at"]
    assert record["source_version"] == {"value": None, "basis": "not_stated"}
    assert not record["incomplete"] and not record["missing"]
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert {item["id"] for item in portable.to_dict()["items"]} <= {
        item["id"] for item in host.attribution.to_dict()["items"]
    }
    assert record["bibliography"][-1]["url"] == "https://www.ncbi.nlm.nih.gov/taxonomy"
    assert "taxonomic_publications_not_queried" in record["bibliography_gaps"]


@pytest.mark.parametrize("empty", [False, True])
def test_source_omissions_are_queried_scope_not_global_absence(monkeypatch, empty):
    serve(
        monkeypatch,
        lambda *args: {
            "taxonomy_nodes": [] if empty else [{"taxonomy": {"tax_id": 1}}]
        },
    )
    with sabueso.attribution() as run:
        result = ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa([1, 2])
    (record,) = run.acquisitions
    assert record["outcome"] == ("empty" if empty else "received")
    assert record["missing"] == result["missing"] == ([1, 2] if empty else [2])
    assert record["taxonomy_context"]["unanswered_ids"] == []
    assert not record["incomplete"]


@pytest.mark.parametrize("fixture", [False, True])
def test_unasked_taxa_get_no_access_or_credit(monkeypatch, tmp_path, fixture):
    calls = serve(monkeypatch)
    client = (
        ncbi_taxonomy.FixtureNCBITaxonomyClient(tmp_path)
        if fixture
        else (ncbi_taxonomy.OnlineNCBITaxonomyClient())
    )
    with sabueso.attribution() as run:
        assert client.taxa([])["record"] == []
    assert not calls and run.acquisitions[0]["outcome"] == "not_queried"
    assert run.acquisitions[0]["provider"]["status"] == "not_attempted"
    assert not ackredit.get_attribution().to_dict()["items"]


def test_partial_batches_retain_completed_credit_and_unanswered_scope(monkeypatch):
    def answer(request, ids, number):
        if number == 2:
            return HTTPError(request.full_url, 400, "synthetic failure", None, None)
        return {"taxonomy_nodes": [{"taxonomy": {"tax_id": t}} for t in ids]}

    serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa(range(1, 52))
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    assert record["count"] == 50 and record["incomplete"]
    assert record["taxonomy_context"]["unanswered_ids"] == [51]
    assert not record["missing"] and record["provider"]["status"] == "available"


@pytest.mark.parametrize("partly_available", [False, True])
def test_missing_fixtures_are_unavailable_not_source_absence(
    tmp_path, partly_available
):
    if partly_available:
        directory = tmp_path / "ncbi_taxonomy"
        directory.mkdir()
        (directory / "1.json").write_text('{"tax_id": 1}', encoding="utf-8")
    with sabueso.attribution() as run:
        result = ncbi_taxonomy.FixtureNCBITaxonomyClient(tmp_path, "original").taxa(
            [1, 2]
        )
    (record,) = run.acquisitions
    assert record["outcome"] == ("partial" if partly_available else "unavailable")
    assert record["taxonomy_context"]["unavailable_ids"] == result["missing"]
    assert record["missing"] == [] and record["retrieved_at"] == "original"
    assert record["incomplete"] and not record["network_attempts"]
    assert record["provider"]["status"] == (
        "available" if partly_available else "not_attempted"
    )


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_original_answers_preserve_dates_hashes_and_batches(
    tmp_path, monkeypatch, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording(), sabueso.attribution() as original:
        first = ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa([1, 2])
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with sabueso.attribution() as reused:
            second = ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa([2, 1])
    a, b = original.acquisitions[0], reused.acquisitions[0]
    assert first == second and len(calls) == 1
    assert b["access"] == mode and not b["network_attempts"]
    assert a["pages"] == b["pages"] and a["response_identity"] == b["response_identity"]
    assert a["retrieved_at"] == b["retrieved_at"]
    assert a["requests"][0]["retrieval_ref"] == b["requests"][0]["retrieval_ref"]


def test_offline_archive_miss_has_no_biological_absence_or_credit(
    tmp_path, monkeypatch
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with (
        archive.replaying(),
        sabueso.attribution() as run,
        pytest.raises(NotArchivedError),
    ):
        ncbi_taxonomy.OnlineNCBITaxonomyClient().taxa([1])
    (record,) = run.acquisitions
    assert not calls and record["outcome"] == "not_queried"
    assert record["taxonomy_context"]["unanswered_ids"] == [1]
    assert record["missing"] == [] and not ackredit.get_attribution().to_dict()["items"]


@pytest.mark.parametrize("failed", [False, True])
def test_keys_stay_outside_errors_traces_and_archives(tmp_path, monkeypatch, failed):
    secret = "synthetic taxonomy key"

    def answer(request, ids, number):
        assert request.get_header("Api-key") == secret
        if failed:
            return HTTPError(request.full_url, 400, secret, None, None)
        return {"taxonomy_nodes": [{"taxonomy": {"tax_id": 1}}]}

    serve(monkeypatch, answer)
    archive = sabueso.RetrievalArchive(tmp_path / "keys.db")
    with archive.recording(), sabueso.attribution() as run:
        client = ncbi_taxonomy.OnlineNCBITaxonomyClient(api_key=secret)
        if failed:
            with pytest.raises(ConnectorError) as caught:
                client.taxa([1])
            assert secret not in str(caught.value)
        else:
            client.taxa([1])
    assert secret not in json.dumps(run.acquisitions)
    assert secret.encode() not in (tmp_path / "keys.db").read_bytes()


def test_public_result_and_failure_keep_detached_original_trace(tmp_path):
    client = ncbi_taxonomy.FixtureNCBITaxonomyClient("temp_data", "original")
    result = ncbi_taxonomy.get_taxon("9606", client=client)
    (record,) = result["acquisition_trace"]["records"]
    assert record["source"] == "NCBI Taxonomy" and record["access"] == "fixture"
    assert result["record"]["tax_id"] == 9606 and result["version"] is None
    with pytest.raises(ConnectorError) as caught:
        ncbi_taxonomy.get_taxon(
            "9606", client=ncbi_taxonomy.FixtureNCBITaxonomyClient(tmp_path)
        )
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


def test_source_stated_empty_taxon_remains_not_found(monkeypatch):
    serve(monkeypatch, lambda *args: {"taxonomy_nodes": []})
    with pytest.raises(RecordNotFoundError) as caught:
        ncbi_taxonomy.get_taxon("1", client=ncbi_taxonomy.OnlineNCBITaxonomyClient())
    assert caught.value.acquisition_trace["records"][0]["outcome"] == "empty"


def test_custom_client_does_not_claim_observation():
    class Custom:
        def taxa(self, ids):
            return {
                "record": [{"tax_id": 1}],
                "retrieved_at": "original",
                "missing": [],
            }

    with sabueso.attribution() as run:
        result = ncbi_taxonomy.get_taxon("1", client=Custom())
    assert not result["acquisition_trace"]["records"] and not run.acquisitions
    assert (
        result["acquisition_trace"]["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )
