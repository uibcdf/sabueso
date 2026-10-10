"""GTEx access and original credit stay separate from scientific tissue support."""

import io
import json
import os
import subprocess
import sys
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, NotArchivedError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, gtex
from sabueso.tools.db.gnomad import FixtureGnomADClient

ROWS = [
    {"tissueSiteDetailId": name, "ontologyId": "UBERON:0002037"}
    for name in ("Brain_Cerebellum", "Brain_Cerebellar_Hemisphere")
]


@pytest.fixture(autouse=True)
def independent():
    with ackredit.session("public GTEx observation"):
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
        payload = answer(request, len(calls)) if answer else {"data": ROWS}
        if isinstance(payload, Exception):
            raise payload
        return Response(payload)

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    return calls


def test_observed_native_scope_keeps_requested_dataset_separate_from_revision(
    monkeypatch,
):
    calls = serve(monkeypatch)
    with ackredit.capture("host") as host, sabueso.attribution() as run:
        result = gtex.get_tissues("gtex_v10")
    (record,) = run.acquisitions
    assert result["acquisition_trace"]["records"] == [record]
    assert result["version"] == "gtex_v10"
    assert record["source_version"] == {"value": None, "basis": "not_stated"}
    assert record["query"] == {"dataset": "gtex_v10"}
    assert parse_qs(urlsplit(calls[0].full_url).query) == {
        "datasetId": ["gtex_v10"],
        "itemsPerPage": ["250"],
    }
    assert len(calls) == record["network_attempts"] == 1
    assert record["count"] == 2 and record["outcome"] == "received"
    assert record["tissue_context"]["dataset_basis"] == "caller_request_parameter"
    assert record["tissue_context"]["completeness"] == "not_established"
    assert record["pages"][0]["tissue_ids"] == [r["tissueSiteDetailId"] for r in ROWS]
    assert record["bibliography"][-1]["id"] == "url:https://gtexportal.org/"
    assert "tissue_publications_not_queried" in record["bibliography_gaps"]
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert {i["id"] for i in portable.to_dict()["items"]} <= {
        i["id"] for i in host.attribution.to_dict()["items"]
    }
    assert "gtex_tissue_observation@1" in json.dumps(portable.to_dict())
    assert (
        len(result["record"]["tissues"]) == 2
    )  # Equal ontology terms do not merge ids.


@pytest.mark.parametrize("fixture", [False, True])
def test_valid_empty_response_is_observed_empty(monkeypatch, tmp_path, fixture):
    calls = serve(monkeypatch, lambda *args: {"data": []})
    if fixture:
        directory = tmp_path / "gtex"
        directory.mkdir()
        (directory / "tissue_site_detail_gtex_v10.json").write_text('{"data": []}')
        client = gtex.FixtureGTExClient(tmp_path, retrieved_at="original fixture time")
    else:
        client = gtex.OnlineGTExClient()
    with sabueso.attribution() as run:
        if fixture:
            assert client.tissues("gtex_v10")["record"] == []
        else:
            with pytest.raises(RecordNotFoundError):
                client.tissues("gtex_v10")
    (record,) = run.acquisitions
    assert record["outcome"] == "empty" and record["count"] == 0
    assert record["pages"][0]["outcome"] == "empty"
    assert record["provider"]["status"] == "available"
    assert len(calls) == record["network_attempts"] == (0 if fixture else 1)


@pytest.mark.parametrize("status", [404, 422])
def test_existing_http_absence_interpretation_is_explicit(monkeypatch, status):
    serve(
        monkeypatch,
        lambda request, _: HTTPError(request.full_url, status, "test", None, None),
    )
    with sabueso.attribution() as run, pytest.raises(RecordNotFoundError):
        gtex.OnlineGTExClient().tissues("gtex_v10")
    (record,) = run.acquisitions
    assert record["outcome"] == "not_found" and record["count"] == 0
    assert record["pages"] == []
    assert (
        "client_HTTP_404_422_interpretation"
        in record["tissue_context"]["absence_basis"]
    )


@pytest.mark.parametrize(
    "payload", [None, [], {}, {"data": None}, {"data": {}}, {"data": [0]}]
)
@pytest.mark.parametrize("fixture", [False, True])
def test_malformed_required_envelopes_fail_without_empty_credit(
    monkeypatch, tmp_path, payload, fixture
):
    serve(monkeypatch, lambda *args: payload)
    if fixture:
        directory = tmp_path / "gtex"
        directory.mkdir()
        (directory / "tissue_site_detail_gtex_v10.json").write_text(json.dumps(payload))
        client = gtex.FixtureGTExClient(tmp_path)
    else:
        client = gtex.OnlineGTExClient()
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        client.tissues("gtex_v10")
    (record,) = run.acquisitions
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["pages"][0]["outcome"] == "failed"
    assert record["provider"]["status"] == "not_attempted"
    assert not ackredit.get_attribution().to_dict()["items"]


@pytest.mark.parametrize("failure", ["missing", "unreadable", "simulated"])
def test_fixture_failure_never_establishes_source_absence(tmp_path, failure):
    if failure == "unreadable":
        directory = tmp_path / "gtex"
        directory.mkdir()
        (directory / "tissue_site_detail_gtex_v10.json").write_text("not json")
    client = gtex.FixtureGTExClient(
        tmp_path, failing={"gtex_v10"} if failure == "simulated" else ()
    )
    with pytest.raises(ConnectorError) as caught:
        gtex.get_tissues("gtex_v10", client=client)
    (record,) = caught.value.acquisition_trace["records"]
    assert record["outcome"] == ("unavailable" if failure == "missing" else "failed")
    assert record["count"] is None and not record["network_attempts"]
    assert record["provider"]["status"] == "not_attempted"
    assert not ackredit.get_attribution().to_dict()["items"]


@pytest.mark.parametrize("failure", ["http", "timeout", "transport"])
def test_failed_transport_retains_unknown_count_and_no_credit(monkeypatch, failure):
    def answer(request, number):
        return (
            HTTPError(request.full_url, 400, "test", None, None)
            if failure == "http"
            else TimeoutError("test")
            if failure == "timeout"
            else URLError("test")
        )

    serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        gtex.OnlineGTExClient().tissues("gtex_v10")
    (record,) = run.acquisitions
    assert record["outcome"] == "failed" and record["count"] is None
    assert record["provider"]["status"] == "not_attempted"


def test_retry_attempts_are_retained_in_one_logical_operation(monkeypatch):
    def answer(request, number):
        return (
            HTTPError(request.full_url, 503, "test", None, None)
            if number == 1
            else {"data": ROWS}
        )

    calls = serve(monkeypatch, answer)
    with sabueso.attribution() as run:
        gtex.OnlineGTExClient().tissues("gtex_v10")
    (record,) = run.acquisitions
    assert len(calls) == record["network_attempts"] == 2
    assert len(record["requests"]) == len(record["pages"]) == 1
    assert record["requests"][0]["retries"] == ["HTTP 503"]


def test_full_requested_page_does_not_establish_dataset_completeness(monkeypatch):
    rows = [{"tissueSiteDetailId": f"synthetic_{i}"} for i in range(250)]
    calls = serve(
        monkeypatch,
        lambda *args: {"data": rows, "paging_info": {"totalNumberOfItems": 400}},
    )
    with sabueso.attribution() as run:
        result = gtex.OnlineGTExClient().tissues("gtex_v10")
    (record,) = run.acquisitions
    assert len(calls) == 1 and record["count"] == len(result["record"]) == 250
    assert record["tissue_context"]["completeness"] == "not_established"
    assert record["source_version"]["value"] is None


@pytest.mark.parametrize("dataset", [None, "../foreign"])
def test_invalid_public_scope_fails_before_access(monkeypatch, dataset):
    from sabueso.core.errors import ArgumentError

    calls = serve(monkeypatch)
    with sabueso.attribution() as run, pytest.raises(ArgumentError):
        gtex.get_tissues(dataset)
    assert not calls and not run.acquisitions
    assert not ackredit.get_attribution().to_dict()["items"]


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_preserves_original_bytes_time_and_credit_context(
    monkeypatch, tmp_path, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording(), sabueso.attribution() as original:
        first = gtex.OnlineGTExClient().tissues("gtex_v10")
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with sabueso.attribution() as later:
            second = gtex.OnlineGTExClient().tissues("gtex_v10")
    a, b = original.acquisitions[0], later.acquisitions[0]
    assert first == second and len(calls) == 1
    assert b["access"] == mode and b["network_attempts"] == 0
    assert a["pages"] == b["pages"] and a["response_identity"] == b["response_identity"]
    assert a["retrieved_at"] == b["retrieved_at"]
    assert a["requests"][0]["retrieval_ref"] == b["requests"][0]["retrieval_ref"]


def test_unasked_archive_scope_has_no_absence_or_credit(monkeypatch, tmp_path):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "empty.db")
    with archive.replaying(), pytest.raises(NotArchivedError) as caught:
        gtex.get_tissues("gtex_v10")
    (record,) = caught.value.acquisition_trace["records"]
    assert not calls and record["outcome"] == "not_queried"
    assert record["count"] is None and record["pages"] == []
    assert not ackredit.get_attribution().to_dict()["items"]


def build(client, *, exon_usage=True):
    return sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        gtex=True,
        gtex_client=client,
        exon_usage=exon_usage,
        gnomad_client=FixtureGnomADClient("temp_data"),
    )[0]


def test_card_mapping_keeps_selected_support_separate_from_acquired_rows():
    client = gtex.FixtureGTExClient("temp_data", retrieved_at="original")

    class Custom:
        def tissues(self, dataset):
            # Read the same fixture without the observation decorator.
            return gtex.FixtureGTExClient.tissues.__wrapped__(client, dataset)

    observed = build(client)
    custom = build(Custom())
    assert observed.to_dict() == custom.to_dict()
    assert observed.pinned_ref() == custom.pinned_ref()
    record = next(
        r for r in observed.acquisition_trace["records"] if r["source"] == "GTEx"
    )
    assert record["count"] == 54
    assert len(observed.get("annotations.tissue_terms")["value"]) == 49
    assert not any(r["source"] == "GTEx" for r in custom.acquisition_trace["records"])
    assert (
        custom.acquisition_trace["coverage"]["other_sources_and_custom_clients"]
        == "not_observed"
    )
    record["pages"].clear()
    assert next(
        r for r in observed.acquisition_trace["records"] if r["source"] == "GTEx"
    )["pages"]


def test_prerequisite_gate_creates_no_gtex_operation_or_credit():
    card = build(gtex.FixtureGTExClient("temp_data"), exon_usage=False)
    assert (
        next(r for r in card.quality["enrichments"] if r["source"] == "GTEx")["status"]
        == "not_queried"
    )
    assert not any(r["source"] == "GTEx" for r in card.acquisition_trace["records"])
    assert "url:https://gtexportal.org/" not in {
        i["id"] for i in ackredit.get_attribution().to_dict()["items"]
    }


def test_missing_fixture_card_is_unavailable_not_absent(tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    with pytest.warns(EnrichmentFailedWarning):
        card = build(gtex.FixtureGTExClient(tmp_path))
    outcome = next(r for r in card.quality["enrichments"] if r["source"] == "GTEx")
    assert outcome["status"] == "error" and "unavailable" in outcome["detail"]
    state = next(r for r in card.knowledge_state()["rows"] if r["source"] == "GTEx")
    assert state["state"] == "unavailable" and state["count"] is None
    assert card.get("annotations.tissue_terms") is None
    assert (
        next(r for r in card.acquisition_trace["records"] if r["source"] == "GTEx")[
            "outcome"
        ]
        == "unavailable"
    )


def test_independent_saved_reader_uses_original_pins_and_portable_credit(tmp_path):
    card = build(gtex.FixtureGTExClient("temp_data", retrieved_at="original"))
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(card)
    saved = {"pin": pin, "card": card.to_dict(), "trace": card.acquisition_trace}
    sidecar = tmp_path / "original.json"
    sidecar.write_text(json.dumps(saved))
    command = """
import json,sys
from pathlib import Path
import ackredit,sabueso
from sabueso.core import attribution,source_acquisition
from sabueso.core.card import Card
from sabueso.tools.db import _http,gtex
def forbidden(*args,**kwargs):
    raise RuntimeError('Saved reader must not acquire, derive or add credit')
sabueso.resolve=sabueso.refresh_card=_http._urlopen=forbidden
attribution._credit=source_acquisition._credit=forbidden
gtex.FixtureGTExClient.tissues=gtex.OnlineGTExClient.tissues=forbidden
for name in ('variant_tissue_usage','isoform_tissue_usage','knowledge_state'):
    setattr(Card,name,forbidden)
sabueso.__version__='999.reader'
path=Path(sys.argv[1]); saved=json.loads(path.read_text())
with ackredit.session('independent saved reader'),sabueso.attribution() as run:
    before=ackredit.get_attribution().to_dict()
    card=sabueso.KnowledgeStore(path.parent/'knowledge.db').load(saved['pin'])
    assert card.to_dict()==saved['card'] and card.acquisition_trace is None
    assert saved['trace']['card_ref']==card.pinned_ref()
    record=next(r for r in saved['trace']['records'] if r['source']=='GTEx')
    assert record['producer']['version']!='999.reader'
    portable=ackredit.Attribution.from_dict(record['provider']['attribution'])
    assert 'gtexportal.org' in portable.report(format='bibtex')
    assert ackredit.get_attribution().to_dict()==before
    assert not run.acquisitions and not run.records
print('Original pins, scientific support and portable credit verified without fresh operations')
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
