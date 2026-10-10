"""Source access is traced where it occurs, independently of stored knowledge."""

import io
import json
from contextvars import Context
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
from sabueso.tools.db import _http, europepmc, uniprot
from sabueso.tools.db.gpcrdb import FixtureGPCRdbClient
from sabueso.tools.db.klifs import FixtureKLIFSClient
from sabueso.tools.db.ncbi_taxonomy import FixtureNCBITaxonomyClient
from sabueso.tools.db.uniref import FixtureUniRefClient

ENTRY = Path("temp_data/P60174.json").read_bytes()


class Response(io.BytesIO):
    status = 200

    def __init__(self, content):
        super().__init__(content)
        self.headers = Message()


def build(**options):
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        **options,
    )


def test_default_resolution_owns_original_trace_without_collector():
    with ackredit.session("source intake"):
        card, resolution = build(
            europepmc={"article_ids": "MED:18562316"},
            europepmc_client=europepmc.FixtureEuropePMCClient("temp_data"),
        )
        trace = card.acquisition_trace
        assert trace == resolution.acquisition_trace
        assert trace["card_ref"] == card.pinned_ref()
        assert trace["coverage"]["other_sources_and_custom_clients"] == "not_observed"
        records = trace["records"]
        assert [(r["source"], r["outcome"], r["access"]) for r in records] == [
            ("UniProt", "received", "fixture"),
            ("Europe PMC", "empty", "fixture"),
        ]
        assert all(r["network_attempts"] == 0 for r in records)
        assert records[1]["retrieved_at"] == "2026-10-02"
        assert records[1]["count"] == 0
        assert all(r["provider"]["status"] == "available" for r in records)
        assert ackredit.get_attribution().to_dict()["items"]
        assert "acquisition_trace" not in card.to_dict()
        assert "_acquisition_trace" not in resolution.to_dict()
        trace["records"].clear()
        assert len(card.acquisition_trace["records"]) == 2
        assert len(resolution.acquisition_trace["records"]) == 2


def test_a_source_not_asked_receives_no_event_or_credit():
    with ackredit.session("only UniProt"):
        card, _ = build()
        assert {r["source"] for r in card.acquisition_trace["records"]} == {"UniProt"}
        ids = {item["id"] for item in ackredit.get_attribution().to_dict()["items"]}
        assert "doi:10.1093/nar/gkad1085" not in ids


def test_source_envelope_trace_is_separate_from_original_entry_version():
    response = uniprot.get_entry("P60174", client=FixtureUniProtClient("temp_data"))
    (record,) = response["acquisition_trace"]["records"]
    assert response["record"] == json.loads(ENTRY)
    assert record["source_version"] == {
        "value": response["record"]["entryAudit"]["entryVersion"],
        "basis": "entry_version",
    }
    assert str(record["source_version"]["value"]) == response["version"]
    assert record["response_identity"]["basis"] == "decoded_client_result"


def test_search_and_mentions_retain_their_distinct_version_bases():
    search = uniprot.search(
        "triosephosphate isomerase", 9606, client=FixtureUniProtClient("temp_data")
    )
    mentions = europepmc.get_mentions(
        "P60174", client=europepmc.FixtureEuropePMCClient("temp_data")
    )
    for response, operation, basis in (
        (search, "search", "database_release"),
        (mentions, "mentions", "service_version"),
    ):
        (record,) = response["acquisition_trace"]["records"]
        assert record["operation"] == operation
        assert record["source_version"] == {
            "value": response["version"],
            "basis": basis,
        }
        assert record["count"] > 0


@pytest.mark.parametrize("source", ["uniprot", "europepmc"])
def test_missing_search_fixture_is_unavailable_without_source_absence(tmp_path, source):
    with pytest.raises(ConnectorError) as caught:
        if source == "uniprot":
            uniprot.search(
                "triosephosphate isomerase", 9606, client=FixtureUniProtClient(tmp_path)
            )
        else:
            europepmc.get_mentions(
                "P60174", client=europepmc.FixtureEuropePMCClient(tmp_path)
            )
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "unavailable"
    assert record["access"] == "fixture" and record["network_attempts"] == 0
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("mode", ["replay", "reuse"])
def test_archive_reuse_has_exact_original_identity_without_another_download(
    tmp_path, monkeypatch, mode
):
    calls = []

    def serve(request, timeout):
        calls.append(request.full_url)
        return Response(ENTRY)

    monkeypatch.setattr(_http, "_urlopen", serve)
    archive = sabueso.RetrievalArchive(tmp_path / "retrievals.db")
    with archive.recording():
        original = uniprot.get_entry("P60174")
    assert len(calls) == 1
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager:
        reused = uniprot.get_entry("P60174")
    assert len(calls) == 1
    left, right = [r["acquisition_trace"]["records"][0] for r in (original, reused)]
    assert left["access"] == "network" and left["network_attempts"] == 1
    assert right["access"] == mode and right["network_attempts"] == 0
    assert left["id"] != right["id"]
    assert left["response_identity"] == right["response_identity"]
    assert left["retrieved_at"] == right["retrieved_at"]
    assert left["requests"][0]["retrieval_ref"] == right["requests"][0]["retrieval_ref"]
    assert (
        left["requests"][0]["response_sha256"]
        == right["requests"][0]["response_sha256"]
    )
    assert {k: v for k, v in original.items() if k != "acquisition_trace"} == {
        k: v for k, v in reused.items() if k != "acquisition_trace"
    }


def test_evaluated_empty_search_retains_service_version_and_bibliography(monkeypatch):
    payload = {"version": "6.9", "hitCount": 0, "resultList": {"result": []}}
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **kw: Response(json.dumps(payload).encode())
    )
    with ackredit.session("empty"), pytest.raises(RecordNotFoundError) as caught:
        europepmc.get_mentions("P60174")
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "empty"
    assert record["access"] == "network" and record["network_attempts"] == 1
    assert record["source_version"] == {"value": "6.9", "basis": "service_version"}
    assert record["requests"][0]["response_sha256"]
    assert record["provider"]["status"] == "available"


def test_http_absence_and_unavailable_fixture_are_not_conflated(monkeypatch):
    def missing(request, timeout):
        raise HTTPError(
            request.full_url, 404, "missing", Message(), io.BytesIO(b"missing")
        )

    monkeypatch.setattr(_http, "_urlopen", missing)
    with pytest.raises(RecordNotFoundError) as online:
        uniprot.get_entry("P60174")
    with pytest.raises(RecordNotFoundError) as fixture:
        uniprot.get_entry(
            "P60174", client=FixtureUniProtClient("/tmp/nonexistent-sabueso-fixture")
        )
    network, unavailable = [
        e.value.acquisition_trace["records"][0] for e in (online, fixture)
    ]
    assert network["outcome"] == "not_found" and network["requests"][0]["status"] == 404
    assert (
        unavailable["outcome"] == "unavailable" and unavailable["access"] == "fixture"
    )
    assert unavailable["provider"]["status"] == "not_attempted"


def test_failed_request_is_retained_without_successful_resource_credit(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError(TimeoutError("source timed out"))

    monkeypatch.setattr(_http, "_urlopen", fail)
    with ackredit.session("failure"):
        card, resolution = sabueso.resolve("P60174")
        assert card is None and resolution.status == "error"
        (record,) = resolution.acquisition_trace["records"]
        assert record["outcome"] == "failed" and record["network_attempts"] == 1
        assert record["requests"][0]["outcome"] == "failed"
        assert record["provider"]["status"] == "not_attempted"
        assert not ackredit.get_attribution().to_dict()["items"]


def test_offline_request_is_not_a_download_or_source_failure(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("replay must not reach the network")

    monkeypatch.setattr(_http, "_urlopen", no_network)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.replaying(), sabueso.attribution() as run:
        card, resolution = sabueso.resolve("P60174")
    assert card is None
    (record,) = run.acquisitions
    assert record["outcome"] == "not_queried"
    assert record["network_attempts"] == 0
    assert record["requests"][0]["route"] == "not_reached"
    assert resolution.acquisition_trace["records"] == run.acquisitions


def test_partial_batch_failure_retains_completed_transport_without_completion_claim(
    monkeypatch,
):
    calls = []

    def serve(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            return Response(b"[]")
        raise URLError(TimeoutError("second batch failed"))

    monkeypatch.setattr(_http, "_urlopen", serve)
    with pytest.raises(ConnectorError) as caught:
        europepmc.get_annotations([f"MED:{i}" for i in range(1, 11)])
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "failed"
    assert record["received_responses"] == 1 and record["network_attempts"] == 2
    assert [r["outcome"] for r in record["requests"]] == ["received", "failed"]
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("failure", ["http", "unreadable"])
def test_retries_keep_original_transport_identities(monkeypatch, failure):
    calls = []

    def serve(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            if failure == "http":
                raise HTTPError(request.full_url, 503, "busy", Message(), None)
            return Response(b"unreadable answer")
        return Response(ENTRY)

    monkeypatch.setattr(_http, "_urlopen", serve)
    monkeypatch.setattr(
        uniprot, "urlopen", partial(_http.urlopen, sleep=lambda _: None)
    )
    response = uniprot.get_entry("P60174")
    (record,) = response["acquisition_trace"]["records"]
    assert record["outcome"] == "received" and record["network_attempts"] == 2
    assert record["requests"][0]["retries"] == [
        "HTTP 503" if failure == "http" else "unreadable_body"
    ]
    if failure == "unreadable":
        assert len(record["requests"]) == 2
        assert (
            record["requests"][0]["response_sha256"]
            != record["requests"][1]["response_sha256"]
        )


def test_provider_failure_preserves_source_result_and_host_trace(monkeypatch):
    original, _ = build()

    def broken():
        raise ImportError("broken provider")

    monkeypatch.setattr(adapter, "_load_backend", broken)
    with pytest.warns(AttributionTrackingWarning):
        card, resolution = build()
    assert card.to_dict() == original.to_dict()
    (record,) = card.acquisition_trace["records"]
    assert record["outcome"] == "received" and record["provider"]["status"] == "failed"
    assert record["response_identity"] and record["bibliography"]
    assert resolution.acquisition_trace == card.acquisition_trace


def test_nested_collectors_and_context_isolation():
    client = FixtureUniProtClient("temp_data")
    with sabueso.attribution() as outer:
        with sabueso.attribution() as inner:
            client.fetch_entry("P60174")
        Context().run(client.fetch_entry, "P60174")
    assert len(outer.acquisitions) == len(inner.acquisitions) == 1
    assert outer.acquisitions == inner.acquisitions
    assert not outer.records and not inner.records
    outer.acquisitions[0]["query"].clear()
    assert outer.acquisitions[0]["query"]


def test_saved_original_trace_reading_never_loads_provider_or_changes_knowledge(
    monkeypatch,
):
    card, _ = build()
    original = card.acquisition_trace
    saved = json.dumps(original)
    knowledge = card.to_dict()
    monkeypatch.setattr(sabueso, "__version__", "999.reader")
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: pytest.fail("saved reading must not load provider"),
    )
    with ackredit.session("saved reader"), sabueso.attribution() as reader:
        restored = Card.from_dict(knowledge)
        assert restored.acquisition_trace is None
        assert json.loads(saved) == original
        for record in json.loads(saved)["records"]:
            assert "999.reader" != record["producer"]["version"]
            ackredit.Attribution.from_dict(record["provider"]["attribution"]).report(
                format="bibtex"
            )
        assert not ackredit.get_attribution().to_dict()["items"]
    assert not reader.acquisitions and not reader.records
    assert restored.to_dict() == knowledge


def test_custom_client_coverage_is_explicit_without_inventing_observation():
    class Custom:
        def fetch_entry(self, accession):
            return json.loads(ENTRY), "original"

    with ackredit.session("custom client"):
        response = uniprot.get_entry("P60174", client=Custom())
        assert response["acquisition_trace"]["records"] == []
        assert (
            response["acquisition_trace"]["coverage"][
                "other_sources_and_custom_clients"
            ]
            == "not_observed"
        )
        assert not ackredit.get_attribution().to_dict()["items"]


def test_refresh_retains_new_access_and_pins_the_final_card():
    card, _ = build()
    original = card.acquisition_trace
    refreshed, resolution = sabueso.refresh_card(
        card, resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    assert refreshed.acquisition_trace == resolution.acquisition_trace
    assert refreshed.acquisition_trace["card_ref"] == refreshed.pinned_ref()
    assert (
        refreshed.acquisition_trace["records"][0]["id"] != original["records"][0]["id"]
    )
    assert card.acquisition_trace == original


def test_one_call_packet_keeps_acquisitions_that_composition_does_not_repeat():
    query = sabueso.KnowledgeQuery("P60174", aspects=["identity"])
    clients = {
        "taxonomy_client": FixtureNCBITaxonomyClient("temp_data"),
        "uniref_client": FixtureUniRefClient("temp_data"),
        "klifs_client": FixtureKLIFSClient("temp_data"),
        "gpcrdb_client": FixtureGPCRdbClient("temp_data"),
    }
    with ackredit.session("one call packet"), sabueso.attribution() as run:
        packet = sabueso.knowledge_packet(
            query, resolver=EntityResolver(FixtureUniProtClient("temp_data")), **clients
        )
    assert len(run.records) == 1
    assert [(r["source"], r["operation"]) for r in run.acquisitions] == [
        ("UniProt", "entry"),
        ("NCBI Taxonomy", "taxa"),
        ("NCBI Taxonomy", "taxa"),
        ("UniProt", "uniref_clusters"),
    ]
    assert run.acquisitions[-1]["outcome"] == "unavailable"
    trace = packet.acquisition_trace
    assert trace["packet_snapshot_id"] == packet.snapshot_id()
    assert trace["card_refs"]["subject"] == packet.entities["subject"]["ref"]
    assert trace["records"] == run.acquisitions
    assert sabueso.KnowledgePacket(packet.to_dict()).acquisition_trace is None
    card, _ = build(**query.options(), **clients)
    composed = sabueso.compose_packet(query, card)
    assert composed.acquisition_trace is None
    assert composed.to_dict() == packet.to_dict()


def test_card_pin_recording_failure_preserves_completed_resolution(monkeypatch):
    def unavailable(self):
        raise RuntimeError("pin unavailable")

    monkeypatch.setattr(Card, "pinned_ref", unavailable)
    with pytest.warns(AttributionTrackingWarning):
        card, resolution = build()
    assert card is not None and resolution.status == "resolved"
    assert card.acquisition_trace["records"]
    assert "pin unavailable" in card.acquisition_trace["recording_error"]
    assert "card_ref" not in card.acquisition_trace
