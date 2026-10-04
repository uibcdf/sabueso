"""ChEMBL records paginated access, original documents and partial failures."""

import io
import json
from datetime import timedelta
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso.core.errors import ConnectorError, RecordNotFoundError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import _http, chembl


@pytest.fixture(autouse=True)
def independent_workflow():
    with ackredit.session("chemical access test"):
        yield


class Response(io.BytesIO):
    status = 200

    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode())
        self.headers = Message()


def serve(monkeypatch, *, fail=None, empty=False):
    calls = []
    monkeypatch.setattr(chembl, "PAGE_SIZE", 1)
    monkeypatch.setattr(_http.time, "sleep", lambda _: None)

    def response(request, timeout):
        path = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        params = parse_qs(urlsplit(request.full_url).query)
        offset = int(params.get("offset", [0])[0])
        calls.append((path, offset))
        if fail and fail(path, offset, len(calls)):
            raise HTTPError(request.full_url, 500, "server failed", Message(), None)
        if path == "status.json":
            return Response({"chembl_db_version": "ChEMBL_37"})
        if path == "activity.json":
            records = (
                []
                if empty
                else [
                    {
                        "activity_id": offset + 1,
                        "assay_chembl_id": "CHEMBL1",
                        "document_chembl_id": "CHEMBL2",
                    }
                ]
            )
            return Response(
                {
                    "activities": records,
                    "page_meta": {
                        "total_count": 2 if not empty else 0,
                        "next": "page2" if offset == 0 and not empty else None,
                    },
                }
            )
        if path == "assay.json":
            return Response({"assays": [{"assay_chembl_id": "CHEMBL1"}]})
        if path == "document.json":
            return Response(
                {
                    "documents": [
                        {
                            "document_chembl_id": "CHEMBL2",
                            "doi": "10.1234/synthetic",
                            "title": "Synthetic test document",
                            "year": 2020,
                        }
                    ]
                }
            )
        if path == "molecule.json":
            return Response(
                {"molecules": [] if empty else [{"molecule_chembl_id": "CHEMBL25"}]}
            )
        if path == "drug_indication.json":
            return Response({"drug_indications": []})
        return Response({"target_chembl_id": "CHEMBL4880"})

    monkeypatch.setattr(_http, "_urlopen", response)
    return calls


def test_paginated_query_keeps_native_release_pages_and_document_metadata(monkeypatch):
    calls = serve(monkeypatch)
    result = chembl.get_bioactivities("CHEMBL4880", limit=2)
    (record,) = result["acquisition_trace"]["records"]
    assert len(result["record"]["activities"]) == 2
    assert record["query"] == {"target": "CHEMBL4880", "limit": 2}
    assert record["outcome"] == "received" and record["count"] == 2
    assert record["total_count"] == 2 and record["truncated"] is False
    assert record["source_version"]["value"] == "ChEMBL_37"
    assert record["source_version"]["origin"] == "status_response"
    assert [p["query"]["offset"] for p in record["completed_pages"]] == [0, 1]
    assert record["network_attempts"] == len(calls) == 6
    assert all(r.get("response_sha256") for r in record["requests"])
    doc = next(b for b in record["bibliography"] if b.get("doi") == "10.1234/synthetic")
    assert doc["title"] == "Synthetic test document" and "authors" not in doc
    assert record["bibliography_gaps"][0]["fields"] == ["authors"]
    assert record["provider"]["status"] == "available"
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert "Synthetic test document" in portable.report(format="text")


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_keeps_versions_hashes_and_original_retrieval(
    tmp_path, monkeypatch, mode
):
    calls = serve(monkeypatch)
    archive = sabueso.RetrievalArchive(tmp_path / "retrieval.db")
    with archive.recording():
        first = chembl.get_bioactivities("CHEMBL4880", limit=2)
    manager = (
        archive.replaying() if mode == "replay" else archive.reusing(timedelta(days=1))
    )
    with manager:
        second = chembl.get_bioactivities("CHEMBL4880", limit=2)
    assert first["record"] == second["record"] and len(calls) == 6
    one, two = (
        first["acquisition_trace"]["records"][0],
        second["acquisition_trace"]["records"][0],
    )
    assert two["access"] == mode and two["network_attempts"] == 0
    for key in (
        "retrieved_at",
        "source_version",
        "response_identity",
        "pages",
        "bibliography",
    ):
        assert one[key] == two[key]
    assert [r["retrieval_ref"] for r in one["requests"]] == [
        r["retrieval_ref"] for r in two["requests"]
    ]


def test_recovered_500_and_capping_are_explicit(monkeypatch):
    serve(monkeypatch, fail=lambda p, o, n: p == "activity.json" and n == 2)
    result = chembl.get_bioactivities("CHEMBL4880", limit=1)
    (record,) = result["acquisition_trace"]["records"]
    page = next(r for r in record["requests"] if "activity.json" in r["url"])
    assert page["network_attempts"] == 2 and page["retries"] == ["HTTP 500"]
    assert record["truncated"] is True and record["total_count"] == 2


@pytest.mark.parametrize("stage", ["second_page", "assays", "version"])
def test_partial_pages_survive_the_original_exception_and_credit_only_received_access(
    monkeypatch, stage
):
    serve(
        monkeypatch,
        fail=lambda p, o, n: (
            (p == "activity.json" and o == 1)
            if stage == "second_page"
            else p == "assay.json"
            if stage == "assays"
            else p == "status.json"
        ),
    )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        chembl.OnlineChEMBLClient().bioactivities("CHEMBL4880", limit=2)
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["incomplete"] is True
    assert record["count"] == (1 if stage == "second_page" else 2)
    assert record["provider"]["status"] == "available"
    assert record["source_version"]["value"] is None
    assert record["requests"][-1]["network_attempts"] == 3
    assert record["requests"][-1]["outcome"] == "failed"
    if stage == "version":
        assert record["documents"]["CHEMBL2"]["doi"] == "10.1234/synthetic"


@pytest.mark.parametrize(
    "error,outcome", [(404, "not_found"), (500, "failed"), ("timeout", "failed")]
)
def test_terminal_absence_and_failure_remain_distinct(monkeypatch, error, outcome):
    monkeypatch.setattr(_http.time, "sleep", lambda _: None)

    def response(request, timeout):
        if error == "timeout":
            raise URLError(TimeoutError("slow"))
        raise HTTPError(request.full_url, error, "failed", Message(), None)

    monkeypatch.setattr(_http, "_urlopen", response)
    expected = RecordNotFoundError if error == 404 else ConnectorError
    with sabueso.attribution() as run, pytest.raises(expected):
        chembl.OnlineChEMBLClient().bioactivities("CHEMBL4880")
    (record,) = run.acquisitions
    assert record["outcome"] == outcome
    assert record["count"] == 0 if error == 404 else "count" in record
    assert record["provider"]["status"] == (
        "available" if error == 404 else "not_attempted"
    )


def test_empty_answer_unavailable_fixture_and_offline_unqueried(monkeypatch, tmp_path):
    serve(monkeypatch, empty=True)
    empty = chembl.get_bioactivities("CHEMBL4880")
    assert empty["acquisition_trace"]["records"][0]["outcome"] == "empty"
    missing = chembl.get_molecules(
        ["CHEMBL25"], client=chembl.FixtureChEMBLClient(tmp_path)
    )
    assert missing["record"]["molecules"] == {}
    assert missing["acquisition_trace"]["records"][0]["outcome"] == "unavailable"
    archive = sabueso.RetrievalArchive(tmp_path / "missing.db")
    with (
        archive.replaying(),
        sabueso.attribution() as run,
        pytest.raises(ConnectorError),
    ):
        chembl.OnlineChEMBLClient().bioactivities("CHEMBL4880")
    assert run.acquisitions[0]["outcome"] == "not_queried"


def test_fixture_card_and_all_client_operations_are_observed_without_changing_serialization(
    tmp_path,
):
    client = chembl.FixtureChEMBLClient("temp_data")
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        chembl={"limit": 1},
        chembl_client=client,
    )
    record = next(
        r for r in card.acquisition_trace["records"] if r["source"] == "ChEMBL"
    )
    assert record["access"] == "fixture" and record["count"] == 1
    assert "acquisition_trace" not in card.to_dict()
    with sabueso.attribution() as run:
        client.molecules(i for i in ["CHEMBL25", "CHEMBL25"])
        client.indications(["CHEMBL25"])
        client.indications_for(["EFO:0000305"])
        client.assay_activities(["CHEMBL1"])
    assert [r["operation"] for r in run.acquisitions] == [
        "molecules",
        "indications",
        "indications_for",
        "assay_activities",
    ]
    assert run.acquisitions[0]["query"]["chembl_ids"] == ["CHEMBL25"]
    saved = json.dumps(run.acquisitions)
    before = ackredit.get_attribution().to_dict()
    assert json.loads(saved)[0]["source"] == "ChEMBL"
    assert ackredit.get_attribution().to_dict() == before


def test_empty_logical_batch_is_not_queried_and_cache_basis_is_explicit(monkeypatch):
    serve(monkeypatch)
    client = chembl.OnlineChEMBLClient()
    client.version()
    with sabueso.attribution() as run:
        client.molecules([])
        client.molecules(iter(["CHEMBL25"]))
    assert run.acquisitions[0]["outcome"] == "not_queried"
    assert run.acquisitions[0]["provider"]["status"] == "not_attempted"
    assert run.acquisitions[1]["source_version"]["origin"] == "client_release_cache"
