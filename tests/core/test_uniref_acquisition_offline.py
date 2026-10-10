"""UniRef pages, limits and original attribution remain detached from knowledge."""

import io
import json
import os
import subprocess
import sys
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, NotArchivedError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, uniref


@pytest.fixture(autouse=True)
def independent():
    with ackredit.session("public UniRef observation"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload, release="2026_03", next_url=None):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()
        if release is not None:
            self.headers["X-UniProt-Release"] = release
        if next_url:
            self.headers["Link"] = f'<{next_url}>; rel="next"'


def serve(monkeypatch, answers):
    calls = []
    iterator = iter(answers)

    def respond(request, timeout):
        calls.append(request.full_url)
        answer = next(iterator)
        if isinstance(answer, Exception):
            raise answer
        return Response(*answer)

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    return calls


NEXT = uniref.API + "/UniRef90_P52270/members?cursor=next"


@pytest.mark.parametrize(
    "releases,value,basis",
    [
        (("2026_03", "2026_03"), "2026_03", "X-UniProt-Release"),
        (("2026_03", "2026_04"), None, "conflicting_pages"),
        (("2026_03", None), None, "partly_not_stated"),
        ((None, None), None, "not_stated"),
    ],
)
def test_each_page_revision_is_preserved_without_inventing_coherence(
    monkeypatch, releases, value, basis
):
    calls = serve(
        monkeypatch,
        [
            ({"results": [{"id": "first"}]}, releases[0], NEXT),
            ({"results": [{"id": "second"}]}, releases[1]),
        ],
    )
    with ackredit.capture("host") as host, sabueso.attribution() as run:
        result = uniref.OnlineUniRefClient().members("UniRef90_P52270")
    (record,) = run.acquisitions
    assert result["version"] == releases[-1]
    assert result["record"] == [{"id": "first"}, {"id": "second"}]
    assert record["source"] == "UniProt" and record["operation"] == "uniref_members"
    assert record["source_version"] == {"value": value, "basis": basis}
    assert [p["source_version"]["value"] for p in record["pages"]] == list(releases)
    assert [p["url"] for p in record["pages"]] == calls
    assert record["network_attempts"] == 2 and record["count"] == 2
    assert record["cluster_context"]["received_rows"] == 2
    assert record["cluster_context"]["continuation"] is None
    assert "never_entity_identity" in record["cluster_context"]["identity_basis"]
    assert record["bibliography"][-1]["url"] == uniref.API
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert "uniref_page_observation@1" in json.dumps(portable.to_dict())
    assert {i["id"] for i in portable.to_dict()["items"]} <= {
        i["id"] for i in host.attribution.to_dict()["items"]
    }


@pytest.mark.parametrize("last_count,next_url", [(1, NEXT), (3, None), (2, None)])
def test_member_limit_distinguishes_received_and_returned_rows(
    monkeypatch, last_count, next_url
):
    monkeypatch.setattr(uniref, "MAX_MEMBERS", 3)
    calls = serve(
        monkeypatch,
        [
            ({"results": [{"id": "first"}]}, "2026_03", NEXT),
            ({"results": [{"id": i} for i in range(last_count)]}, "2026_03", next_url),
            ({"results": [{"id": "last"}]}, "2026_03"),
        ],
    )
    with sabueso.attribution() as run:
        result = uniref.OnlineUniRefClient().members("UniRef90_P52270")
    (record,) = run.acquisitions
    assert len(result["record"]) == record["count"] == 3
    received = 4 if last_count == 3 else 3
    assert record["cluster_context"]["received_rows"] == received
    assert record["truncated"] is result["truncated"] is (last_count == 3)
    assert len(calls) == (3 if last_count == 1 else 2)


def test_limit_with_remaining_link_is_explicit(monkeypatch):
    monkeypatch.setattr(uniref, "MAX_MEMBERS", 1)
    calls = serve(monkeypatch, [({"results": [{"id": "kept"}]}, "2026_03", NEXT)])
    with sabueso.attribution() as run:
        result = uniref.OnlineUniRefClient().members("UniRef90_P52270")
    (record,) = run.acquisitions
    assert len(calls) == 1 and result["truncated"] and record["incomplete"]
    assert record["cluster_context"]["continuation"] == NEXT


def test_search_continuation_is_observed_without_expanding_original_request(
    monkeypatch,
):
    calls = serve(
        monkeypatch, [({"results": [{"id": "UniRef90_P52270"}]}, "2026_03", NEXT)]
    )
    result = uniref.get_clusters("P52270")
    (record,) = result["acquisition_trace"]["records"]
    assert len(calls) == 1 and record["truncated"]
    assert record["cluster_context"]["scope"] == "single_search_response"
    assert record["cluster_context"]["page_size"] == 10


@pytest.mark.parametrize("failure", ["timeout", "malformed", "404"])
def test_later_page_failure_retains_completed_scope_but_returns_no_partial_science(
    monkeypatch, failure
):
    second = (
        TimeoutError("test")
        if failure == "timeout"
        else (
            HTTPError(NEXT, 404, "test", None, None)
            if failure == "404"
            else ({"results": None}, "2026_04")
        )
    )
    serve(monkeypatch, [({"results": [{"id": "kept"}]}, "2026_03", NEXT), second])
    error = RecordNotFoundError if failure == "404" else ConnectorError
    with sabueso.attribution() as run, pytest.raises(error):
        uniref.OnlineUniRefClient().members("UniRef90_P52270")
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["incomplete"]
    assert record["count"] == 1 and len(record["completed_pages"]) == 1
    assert record["cluster_context"]["returned_rows"] is None
    assert record["cluster_context"]["continuation"] == NEXT
    assert record["terminal_outcome"] == ("not_found" if failure == "404" else "failed")
    assert record["provider"]["status"] == "available"


@pytest.mark.parametrize("payload", [None, [], {}, {"record": None}, {"record": [0]}])
def test_malformed_fixture_is_failure_not_empty_or_absence(tmp_path, payload):
    directory = tmp_path / "uniref"
    directory.mkdir()
    (directory / "clusters_P52270.json").write_text(json.dumps(payload))
    with pytest.raises(ConnectorError) as caught:
        uniref.get_clusters("P52270", client=uniref.FixtureUniRefClient(tmp_path))
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["pages"][0]["outcome"] == "failed"
    assert record["provider"]["status"] == "not_attempted"


@pytest.mark.parametrize("failure", ["missing", "unreadable", "simulated"])
def test_fixture_failure_does_not_claim_provider_absence(tmp_path, failure):
    if failure == "unreadable":
        directory = tmp_path / "uniref"
        directory.mkdir()
        (directory / "clusters_P52270.json").write_text("invalid json")
    client = uniref.FixtureUniRefClient(
        tmp_path, failing={"clusters_P52270"} if failure == "simulated" else ()
    )
    with pytest.raises(ConnectorError) as caught:
        uniref.get_clusters("P52270", client=client)
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == ("unavailable" if failure == "missing" else "failed")
    assert record["count"] is None and record["network_attempts"] == 0
    assert not ackredit.get_attribution().to_dict()["items"]


def test_empty_native_page_is_empty_not_unasked(monkeypatch):
    serve(monkeypatch, [({"results": []}, None)])
    result = uniref.get_clusters("P52270")
    (record,) = result["acquisition_trace"]["records"]
    assert result["record"]["clusters"] == []
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["provider"]["status"] == "available"


def test_transient_retry_does_not_duplicate_pages(monkeypatch):
    calls = serve(
        monkeypatch,
        [
            HTTPError(uniref.API, 503, "test", None, None),
            ({"results": []}, "2026_03"),
        ],
    )
    result = uniref.get_clusters("P52270")
    (record,) = result["acquisition_trace"]["records"]
    assert len(calls) == record["network_attempts"] == 2
    assert len(record["pages"]) == len(record["requests"]) == 1
    assert record["requests"][0]["retries"] == ["HTTP 503"]


@pytest.mark.parametrize("truncated", [False, True])
def test_fixture_subset_never_claims_complete_native_pagination(tmp_path, truncated):
    directory = tmp_path / "uniref"
    directory.mkdir()
    (directory / "members_X.json").write_text(
        json.dumps(
            {
                "version": "fixture label",
                "record": [],
                "truncated": truncated,
            }
        )
    )
    with sabueso.attribution() as run:
        result = uniref.FixtureUniRefClient(tmp_path).members("X")
    (record,) = run.acquisitions
    assert result["record"] == [] and record["outcome"] == "empty"
    assert record["source_version"] == {
        "value": "fixture label",
        "basis": "fixture_declared_release",
    }
    assert record["truncated"] is truncated
    assert record["cluster_context"]["completeness"] == "not_established"


def test_later_empty_page_with_failure_does_not_claim_complete_absence(monkeypatch):
    serve(monkeypatch, [({"results": []}, "2026_03", NEXT), TimeoutError("test")])
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        uniref.OnlineUniRefClient().members("UniRef90_P52270")
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["count"] == 0
    assert record["terminal_outcome"] == "failed" and record["incomplete"]


def test_native_total_header_is_separate_from_returned_rows(monkeypatch):
    response = Response({"results": [{"id": "one"}]})
    response.headers["X-Total-Results"] = "123"
    monkeypatch.setattr(_http, "_urlopen", lambda *args, **kwargs: response)
    result = uniref.get_clusters("P52270")
    (record,) = result["acquisition_trace"]["records"]
    assert record["count"] == 1 and record["pages"][0]["total_count_header"] == "123"


def test_missing_members_fixture_never_installs_partial_cluster_support(tmp_path):
    from pathlib import Path

    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    directory = tmp_path / "uniref"
    directory.mkdir()
    (directory / "clusters_P52270.json").write_bytes(
        Path("temp_data/uniref/clusters_P52270.json").read_bytes()
    )
    with pytest.warns(EnrichmentFailedWarning):
        card = build(uniref.FixtureUniRefClient(tmp_path))
    records = [
        r
        for r in card.acquisition_trace["records"]
        if r["operation"].startswith("uniref_")
    ]
    assert [r["outcome"] for r in records] == ["received", "unavailable"]
    assert card.get("identifiers.uniref") is None
    assert card.relationships("clustered_with") == []
    state = [
        r for r in card.knowledge_state()["rows"] if r["area"] == "identifiers.uniref"
    ]
    assert state and all(
        r["state"] == "unavailable" and r["count"] is None for r in state
    )


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archived_pages_keep_original_response_hashes_and_times(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch, [({"results": []}, "2026_03")])
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording():
        original = uniref.get_clusters("P52270")
    context = (
        archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying()
    )
    with context:
        restored = uniref.get_clusters("P52270")
    first = original["acquisition_trace"]["records"][0]
    record = restored["acquisition_trace"]["records"][0]
    assert len(calls) == 1 and record["network_attempts"] == 0
    assert record["access"] == mode and record["retrieved_at"] == first["retrieved_at"]
    assert (
        record["requests"][0]["response_sha256"]
        == first["requests"][0]["response_sha256"]
    )
    assert record["pages"] == first["pages"]


def test_unarchived_request_is_not_queried(tmp_path):
    with (
        sabueso.RetrievalArchive(tmp_path / "archive.db").replaying(),
        pytest.raises(NotArchivedError) as caught,
    ):
        uniref.get_clusters("P52270")
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == "not_queried" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"


def build(client, **options):
    return sabueso.resolve(
        "P52270",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        uniref=True,
        uniref_client=client,
        **options,
    )[0]


def test_observation_keeps_exact_scientific_assertions_relationships_and_pin():
    class Unobserved:
        def __init__(self):
            self.client = uniref.FixtureUniRefClient(
                "temp_data", retrieved_at="original"
            )

        def clusters(self, accession):
            return uniref.FixtureUniRefClient.clusters.__wrapped__(
                self.client, accession
            )

        def members(self, cluster_id):
            return uniref.FixtureUniRefClient.members.__wrapped__(
                self.client, cluster_id
            )

    card = build(uniref.FixtureUniRefClient("temp_data", retrieved_at="original"))
    custom = build(Unobserved())
    assert (
        card.to_dict() == custom.to_dict() and card.pinned_ref() == custom.pinned_ref()
    )
    records = [
        r
        for r in card.acquisition_trace["records"]
        if r["operation"].startswith("uniref_")
    ]
    assert [r["operation"] for r in records] == ["uniref_clusters", "uniref_members"]
    assert all(
        r["source_version"]["basis"] == "fixture_declared_release" for r in records
    )
    assert not any(
        r["operation"].startswith("uniref_")
        for r in custom.acquisition_trace["records"]
    )
    assert card.relationships("same_as", object_ref="uniprot:Q4DV43") == []


def test_unasked_cluster_operations_have_no_observation_or_resource_credit():
    card, _ = sabueso.resolve(
        "P52270", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )
    assert not any(
        r["operation"].startswith("uniref_") for r in card.acquisition_trace["records"]
    )
    assert "url:https://rest.uniprot.org/uniref" not in {
        item["id"] for item in ackredit.get_attribution().to_dict()["items"]
    }


def test_independent_saved_reader_restores_original_credit_without_new_operations(
    tmp_path,
):
    card = build(uniref.FixtureUniRefClient("temp_data", retrieved_at="original"))
    pin = sabueso.KnowledgeStore(tmp_path / "knowledge.db").save(card)
    saved = {"pin": pin, "card": card.to_dict(), "trace": card.acquisition_trace}
    sidecar = tmp_path / "original.json"
    sidecar.write_text(json.dumps(saved))
    command = """
import json,sys
from pathlib import Path
import ackredit,sabueso
from sabueso.core import attribution,source_acquisition
from sabueso.core.card import Card
from sabueso.tools.db import _http,uniref
def forbidden(*args,**kwargs):
    raise RuntimeError('Saved reader must not acquire, derive or add credit')
sabueso.resolve=sabueso.refresh_card=_http._urlopen=forbidden
attribution._credit=source_acquisition._credit=forbidden
for cls in (uniref.FixtureUniRefClient,uniref.OnlineUniRefClient):
    cls.clusters=cls.members=forbidden
Card.sequence_differences=Card.knowledge_state=forbidden
sabueso.__version__='999.reader'
path=Path(sys.argv[1]); saved=json.loads(path.read_text())
with ackredit.session('independent reader'),sabueso.attribution() as run:
    before=ackredit.get_attribution().to_dict()
    card=sabueso.KnowledgeStore(path.parent/'knowledge.db').load(saved['pin'])
    assert card.to_dict()==saved['card'] and card.acquisition_trace is None
    assert saved['trace']['card_ref']==card.pinned_ref()
    records=[r for r in saved['trace']['records'] if r['operation'].startswith('uniref_')]
    assert len(records)==2
    for record in records:
        assert record['producer']['version']!='999.reader'
        portable=ackredit.Attribution.from_dict(record['provider']['attribution'])
        assert 'rest.uniprot.org/uniref' in portable.report(format='bibtex')
    assert ackredit.get_attribution().to_dict()==before
    assert not run.acquisitions and not run.records
"""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", command, str(sidecar)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(sidecar.read_text()) == saved
