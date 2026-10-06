"""MONDO query receipts preserve index/release scope, original origins and credit.

Wire documents are synthetic; public card cases use declared frozen fixtures.
"""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from hashlib import sha256
from urllib.error import HTTPError, URLError

import ackredit
import pytest

import sabueso
from sabueso.core import attribution as adapter
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.mappings.mondo import map_disease
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.db import _http, _mirror, _release, mondo

OBO = b"""format-version: 1.2
data-version: releases/2026-09-01

[Term]
id: MONDO:0014221
name: synthetic disease
def: "synthetic definition" [PMID:1234]
xref: Orphanet:868 {source="MONDO:equivalentTo"}
xref: EFO:0001360
is_a: MONDO:0000001 ! disease
"""
ASSET_URL = "https://github.com/monarch-initiative/mondo/releases/download/v2026-09-01/mondo.obo"


@pytest.fixture(autouse=True)
def independent_workflow():
    _release.forget("MONDO")
    with ackredit.session("MONDO observation"):
        yield
    _release.forget("MONDO")


class Response(io.BytesIO):
    def __init__(self, payload):
        super().__init__(payload)
        self.status = 200
        self.headers = Message()


def serve(monkeypatch, *, payload=OBO, error=None, checksum=True):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    asset = {"name": "mondo.obo", "browser_download_url": ASSET_URL}
    if checksum:
        asset["digest"] = "sha256:" + (
            "0" * 64 if error == "checksum" else sha256(payload).hexdigest()
        )
    metadata = json.dumps({"tag_name": "v2026-09-01", "assets": [asset]}).encode()

    def response(request, timeout):
        calls.append(request)
        is_asset = request.full_url == ASSET_URL
        if error == "timeout" and is_asset:
            raise URLError(TimeoutError("synthetic timeout"))
        if isinstance(error, int) and is_asset:
            raise HTTPError(request.full_url, error, "synthetic", Message(), None)
        return Response(payload if is_asset else metadata)

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def lookup(identifier="MONDO:0014221", client=None):
    return mondo.get_term(identifier, client=client)


def event(result):
    (record,) = result["acquisition_trace"]["records"]
    return record


def test_native_term_scope_version_digest_and_complete_resource_bibliography(
    monkeypatch,
):
    calls = serve(monkeypatch)
    with ackredit.capture("host") as host:
        result = lookup("mondo:MONDO:0014221")
    record = event(result)
    assert result["record"] == mondo.parse_release(OBO.decode())[1]["MONDO:0014221"]
    assert record["query"] == {"mondo_id": "mondo:MONDO:0014221"}
    assert record["normalized_query"] == {"identifier": "MONDO:0014221"}
    assert record["source_version"] == {
        "value": "2026-09-01",
        "basis": "obo_header_data_version",
    }
    assert record["outcome"] == "received" and record["count"] == 1
    assert record["network_attempts"] == len(calls) == 2
    assert record["response_identity"]["hash"] == digest(
        canonical_json(result["record"])
    )
    context = record["identity_lookup"]
    assert context["indexed_term_count"] == 1
    assert context["definition_references"] == ["PMID:1234"]
    origin = context["index_origin"]
    assert origin["response_identity"]["hash"] == sha256(OBO).hexdigest()
    assert origin["asset"]["tag"] == "v2026-09-01"
    assert origin["checksum"] == {"basis": "published_asset_digest", "verified": True}
    paper = next(
        b for b in record["bibliography"] if b.get("doi") == "10.1093/genetics/iyaf215"
    )
    assert paper["year"] == 2026 and len(paper["authors"]) == 115
    assert paper["volume"] == "232" and paper["pages"] == "iyaf215"
    assert record["bibliography_gaps"] == [
        "term_definition_and_imported_terminology_citations_not_returned"
    ]
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert "iyaf215" in portable.report(format="bibtex")
    assert any(
        u["context"].get("identity_lookup") == context
        for u in host.attribution.to_dict()["uses"]
    )


def test_equivalence_is_a_query_of_stated_xrefs_not_names_or_related_terms(monkeypatch):
    calls = serve(monkeypatch)
    client = mondo.OnlineMONDOClient()
    with sabueso.attribution() as observed:
        known = client.equivalent("ORPHA:868")
        related = client.equivalent("efo:EFO:0001360")
    a, b = observed.acquisitions
    assert known["mondo"] == "MONDO:0014221" and related["mondo"] is None
    assert a["normalized_query"] == {"identifier": "Orphanet:868"}
    assert a["identity_lookup"]["equivalence_statements"] == [
        {"id": "Orphanet:868", "equivalent": True}
    ]
    assert b["outcome"] == "empty" and b["count"] == 0
    assert b["provider"]["status"] == "available" and b["access"] == "memory"
    assert b["network_attempts"] == 0 and len(calls) == 2
    assert b["retrieved_at"] == a["retrieved_at"]


@pytest.mark.parametrize("fresh_client", [False, True])
def test_index_memory_reuse_preserves_original_receipt_without_another_download(
    monkeypatch, fresh_client
):
    calls = serve(monkeypatch)
    first = mondo.OnlineMONDOClient()
    first._when = "old client clock"
    original = lookup(client=first)
    a = event(original)
    client = mondo.OnlineMONDOClient() if fresh_client else first
    client._when = "later client clock"
    reused = lookup(client=client)
    b = event(reused)
    assert b["access"] == ("mixed" if fresh_client else "memory")
    assert b["network_attempts"] == (1 if fresh_client else 0)
    assert len(calls) == (3 if fresh_client else 2)
    assert b["identity_lookup"]["index_reused"]
    assert b["identity_lookup"]["index_origin"] == a["identity_lookup"]["index_origin"]
    assert b["retrieved_at"] == a["retrieved_at"] != "later client clock"
    assert reused["retrieved_at"] == original["retrieved_at"] == b["retrieved_at"]
    assert b["identity_lookup"]["client_retrieved_at"] == b["retrieved_at"]
    assert b["identity_lookup"]["client_time_basis"] == "original_release_response"
    assert map_disease(
        original["record"], original["retrieved_at"], original["version"]
    ) == map_disease(reused["record"], reused["retrieved_at"], reused["version"])
    assert b["provider"]["status"] == "available"


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archived_release_queries_keep_original_wire_hashes_times_and_version(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "mondo.db")
    with archive.recording():
        original = lookup()
        a = event(original)
    _release.forget("MONDO")
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        reused = lookup()
        b = event(reused)
    assert b["access"] == mode and b["network_attempts"] == 0 and len(calls) == 2
    for key in (
        "normalized_query",
        "source_version",
        "retrieved_at",
        "response_identity",
    ):
        assert a[key] == b[key]
    for old, new in zip(a["requests"], b["requests"], strict=True):
        for key in ("retrieval_ref", "retrieved_at", "response_sha256"):
            assert old[key] == new[key]
    assert b["provider"]["status"] == "available"
    assert reused["retrieved_at"] == original["retrieved_at"] == b["retrieved_at"]
    assert map_disease(
        original["record"], original["retrieved_at"], original["version"]
    ) == map_disease(reused["record"], reused["retrieved_at"], reused["version"])


@pytest.mark.parametrize("identifier", ["MONDO:9999999", "efo:EFO:0001360"])
def test_received_release_absence_is_an_evaluated_lookup_in_its_original_scope(
    monkeypatch, identifier
):
    serve(monkeypatch)
    with sabueso.attribution() as run:
        if identifier.startswith("MONDO"):
            with pytest.raises(RecordNotFoundError) as caught:
                lookup(identifier)
            assert caught.value.acquisition_trace["records"] == run.acquisitions
        else:
            mondo.OnlineMONDOClient().equivalent(identifier)
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["provider"]["status"] == "available"
    assert "lookup_scope_only" in record["identity_lookup"]["absence_basis"]


@pytest.mark.parametrize("error", [404, 500, "timeout", "checksum"])
def test_download_failures_retain_received_wire_facts_without_completed_credit(
    monkeypatch, error
):
    calls = serve(monkeypatch, error=error)
    with sabueso.attribution() as run, pytest.raises(ConnectorError) as caught:
        lookup()
    (record,) = run.acquisitions
    assert record["outcome"] == "failed"
    assert record["provider"]["status"] == "not_attempted"
    assert caught.value.acquisition_trace["records"] == [record]
    assert len(calls) == (4 if error == 500 else 2)
    assert record["count"] is None
    assert _release.recall("MONDO", "v2026-09-01") is None
    if error == "checksum":
        assert not record["identity_lookup"]["index_origin"]["checksum"]["verified"]


@pytest.mark.parametrize(
    "mode", ["offline", "replay_missing", "fixture_missing", "simulated"]
)
def test_unasked_unavailable_and_simulated_failure_remain_distinct(tmp_path, mode):
    client = (
        mondo.FixtureMONDOClient(
            tmp_path, failing={"MONDO:0014221"} if mode == "simulated" else ()
        )
        if mode.startswith("fixture") or mode == "simulated"
        else None
    )
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    manager = (
        _mirror.using(tmp_path, mode="offline")
        if mode == "offline"
        else archive.replaying()
    )
    with manager, sabueso.attribution() as run, pytest.raises(ConnectorError) as caught:
        lookup(client=client)
    (record,) = run.acquisitions
    assert caught.value.acquisition_trace["records"] == [record]
    assert record["outcome"] == (
        "not_queried"
        if mode in ("offline", "replay_missing")
        else "unavailable"
        if mode == "fixture_missing"
        else "failed"
    )
    assert (
        record["network_attempts"] == 0
        and record["provider"]["status"] == "not_attempted"
    )


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"])
def test_fixture_equivalence_empty_and_missing_term_do_not_establish_global_absence(
    tmp_path,
    line_ending,
):
    directory = tmp_path / "mondo"
    directory.mkdir()
    payload = OBO.replace(b"\n", line_ending)
    (directory / "mondo.obo").write_bytes(payload)
    client = mondo.FixtureMONDOClient(tmp_path, retrieved_at="original fixture time")
    with sabueso.attribution() as run:
        client.equivalent("EFO:0001360")
        with pytest.raises(RecordNotFoundError):
            client.term("MONDO:9999999")
    a, b = run.acquisitions
    assert a["outcome"] == "empty" and a["provider"]["status"] == "available"
    assert b["outcome"] == "unavailable" and b["provider"]["status"] == "not_attempted"
    assert all(r["identity_lookup"]["index_scope"] == "fixture_subset" for r in (a, b))
    assert all(
        r["identity_lookup"]["index_origin"]["response_identity"]["hash"]
        == sha256(payload).hexdigest()
        for r in (a, b)
    )
    assert all(
        r["retrieved_at"] == "original fixture time" and r["network_attempts"] == 0
        for r in (a, b)
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"<html>not an OBO file</html>",
        OBO.replace(b"data-version: releases/2026-09-01\n", b""),
    ],
)
def test_unexpected_document_and_unknown_version_are_not_promoted(monkeypatch, payload):
    serve(monkeypatch, payload=payload, checksum=False)
    with sabueso.attribution() as run:
        if payload.startswith(b"<html>"):
            with pytest.raises(ConnectorError):
                lookup()
        else:
            lookup()
    (record,) = run.acquisitions
    assert record["source_version"] == {"value": None, "basis": "not_stated"}
    if payload.startswith(b"<html>"):
        assert (
            record["outcome"] == "failed"
            and record["provider"]["status"] == "not_attempted"
        )
        assert record["count"] is None
    else:
        assert (
            record["outcome"] == "received"
            and record["provider"]["status"] == "available"
        )
    assert record["identity_lookup"]["index_origin"]["checksum"]["verified"] is None


def test_resolution_original_science_saved_trace_and_readers_remain_independent(
    tmp_path, monkeypatch
):
    client = mondo.FixtureMONDOClient("temp_data", retrieved_at="original observation")
    with sabueso.attribution() as run:
        card, resolution = resolve_disease_card("ORPHA:868", mondo_client=client)
        unknown, unresolved = sabueso.resolve("efo:EFO:0001360", mondo_client=client)
    assert card is not None and unknown is None and unresolved.status == "not_found"
    assert [r["operation"] for r in resolution.acquisition_trace["records"]] == [
        "equivalent",
        "term",
    ]
    assert resolution.acquisition_trace == card.acquisition_trace
    assert unresolved.acquisition_trace["records"][0]["outcome"] == "empty"
    original, trace = card.to_dict(), deepcopy(card.acquisition_trace)
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(card)
    serialized = json.dumps(trace)
    before = ackredit.get_attribution().to_dict()
    monkeypatch.setattr(
        client, "term", lambda *args: pytest.fail("reader acquired a source")
    )
    with sabueso.attribution() as reader:
        loaded = store.load(pin)
        portable = json.loads(serialized)
        Card.from_dict(original)
        for record in portable["records"]:
            ackredit.Attribution.from_dict(record["provider"]["attribution"]).report(
                format="bibtex"
            )
    assert loaded.to_dict() == original and loaded.acquisition_trace is None
    assert not reader.acquisitions and ackredit.get_attribution().to_dict() == before
    assert len(run.acquisitions) == 3


def test_provider_failure_does_not_replace_original_term(monkeypatch):
    serve(monkeypatch)
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with pytest.warns(Warning):
        result = lookup()
    assert result["record"]["id"] == "MONDO:0014221"
    assert event(result)["provider"]["status"] == "failed"


def test_custom_client_does_not_gain_fabricated_access():
    class CustomClient:
        def term(self, identifier):
            return {
                "record": {"id": identifier},
                "retrieved_at": "supplied",
                "version": None,
            }

    result = lookup(client=CustomClient())
    assert result["acquisition_trace"]["records"] == []
    assert result["record"] == {"id": "MONDO:0014221"}


def test_preexisting_index_without_a_receipt_retains_explicit_origin_gaps(monkeypatch):
    calls = serve(monkeypatch)
    _release.keep("MONDO", "v2026-09-01", mondo.parse_release(OBO.decode()))
    record = event(lookup())
    assert len(calls) == 1 and record["network_attempts"] == 1
    assert record["access"] == "mixed" and record["retrieved_at"] is None
    assert record["retrieved_at_basis"] == "original_release_time_not_observed"
    assert record["source_version"]["basis"] == "cached_index_declared_version"
    assert record["identity_lookup"]["index_origin"] is None
    assert record["identity_lookup"]["index_scope"] == "unobserved_cached_index"


def test_warm_index_can_be_queried_offline_without_fabricating_a_download(
    monkeypatch, tmp_path
):
    calls = serve(monkeypatch)
    client = mondo.OnlineMONDOClient()
    a = event(lookup(client=client))
    with _mirror.using(tmp_path, mode="offline"):
        b = event(lookup(client=client))
    assert b["access"] == "memory" and b["network_attempts"] == 0
    assert len(calls) == 2 and b["retrieved_at"] == a["retrieved_at"]
    assert b["provider"]["status"] == "available"


def test_unsupported_native_namespace_retains_original_return_without_completed_credit(
    monkeypatch,
):
    serve(monkeypatch)
    with sabueso.attribution() as run:
        result = mondo.OnlineMONDOClient().equivalent("unknown:1234")
    (record,) = run.acquisitions
    assert result["query"] is None and result["mondo"] is None
    assert record["outcome"] == "unobserved" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"


def test_concurrent_fixture_queries_keep_each_original_scope_in_host_capture(tmp_path):
    clients = []
    for name, when in (
        ("first", "original first time"),
        ("second", "original second time"),
    ):
        directory = tmp_path / name / "mondo"
        directory.mkdir(parents=True)
        (directory / "mondo.obo").write_bytes(OBO)
        clients.append(mondo.FixtureMONDOClient(directory.parent, retrieved_at=when))
    with ackredit.capture("host") as host, sabueso.attribution() as run:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [
                pool.submit(copy_context().run, client.equivalent, identifier)
                for client, identifier in zip(
                    clients, ("ORPHA:868", "EFO:0001360"), strict=True
                )
            ]
            results = [job.result() for job in jobs]
    assert results[0]["mondo"] == "MONDO:0014221" and results[1]["mondo"] is None
    assert {
        (r["normalized_query"]["identifier"], r["retrieved_at"], r["outcome"])
        for r in run.acquisitions
    } == {
        ("Orphanet:868", "original first time", "received"),
        ("EFO:0001360", "original second time", "empty"),
    }
    uses = host.attribution.to_dict()["uses"]
    assert {u["context"]["normalized_query"]["identifier"] for u in uses} == {
        "Orphanet:868",
        "EFO:0001360",
    }


@pytest.mark.parametrize("route", ["wire", "fixture"])
@pytest.mark.parametrize(
    "payload", [b"<html>not an ontology</html>", b"format-version: 1.2\n\xff"]
)
def test_invalid_release_documents_are_connector_failures_never_missing_records(
    monkeypatch, tmp_path, route, payload
):
    if route == "wire":
        serve(monkeypatch, payload=payload)
        client = None
    else:
        directory = tmp_path / "mondo"
        directory.mkdir()
        (directory / "mondo.obo").write_bytes(payload)
        client = mondo.FixtureMONDOClient(tmp_path)
    with sabueso.attribution() as run, pytest.raises(ConnectorError) as caught:
        lookup(client=client)
    (record,) = run.acquisitions
    assert not isinstance(caught.value, RecordNotFoundError)
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"
    assert (
        record["identity_lookup"]["index_origin"]["response_identity"]["hash"]
        == sha256(payload).hexdigest()
    )
    assert _release.recall("MONDO", "v2026-09-01") is None
