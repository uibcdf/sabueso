"""DISEASES channel origins and NCBI disease lookups: scopes, integrity and credit."""

import io
import json
from copy import deepcopy
from datetime import timedelta
from email.message import Message
from hashlib import sha256
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import ackredit
import pytest

import sabueso
from sabueso._private.smonitor.warnings import AttributionTrackingWarning
from sabueso.core import attribution as adapter
from sabueso.core.errors import ConnectorError, OfflineError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.tools.db import _http, _mirror, _release, clinvar, diseases, medgen

TSV = b"ENSP1\tG\tDOID:1\tD\tMedlinePlus\tCURATED\t5\n"


@pytest.fixture(autouse=True)
def independent(monkeypatch):
    _release.forget("DISEASES")
    monkeypatch.delenv("SABUESO_CACHE_DIR", raising=False)
    monkeypatch.delenv("SABUESO_NCBI_KEY", raising=False)
    with ackredit.session("public disease lookup observation"):
        yield
    _release.forget("DISEASES")


class Response(io.BytesIO):
    def __init__(self, payload, modified=None):
        super().__init__(payload)
        self.status = 200
        self.headers = Message()
        if modified:
            self.headers["Last-Modified"] = modified


def serve(monkeypatch, answer, modified=None):
    calls = []
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)

    def respond(request, timeout):
        calls.append(request)
        value = answer(request, len(calls)) if callable(answer) else answer
        if isinstance(value, Exception):
            raise value
        return Response(
            value if isinstance(value, bytes) else json.dumps(value).encode(), modified
        )

    monkeypatch.setattr(_http, "_urlopen", respond)
    return calls


def ncbi(source, *, empty=False, missing_version=False):
    def answer(request, number):
        path = urlsplit(request.full_url).path.rsplit("/", 1)[-1]
        if path == "einfo.fcgi":
            field = "dbbuild" if source == "ClinVar" else "lastupdate"
            return {
                "einforesult": {
                    "dbinfo": [{} if missing_version else {field: "2026/10/01"}]
                }
            }
        if path == "esearch.fcgi":
            return {
                "esearchresult": {
                    "count": "0" if empty else "1",
                    "idlist": [] if empty else ["1"],
                }
            }
        row = (
            {
                "uid": "1",
                "accession": "VCV000000001",
                "accession_version": "3",
                "germline_classification": {
                    "description": "Conflicting classifications of pathogenicity",
                    "review_status": "criteria provided",
                    "trait_set": [],
                },
            }
            if source == "ClinVar"
            else {"conceptid": "C1"}
        )
        return {"result": {"uids": ["1"], "1": row}}

    return answer


def online(source, **kwargs):
    return (
        clinvar.OnlineClinVarClient(**kwargs)
        if source == "ClinVar"
        else medgen.OnlineMedGenClient(**kwargs)
    )


def ask(source, client, ids=None, limit=1):
    return (
        client.variants(ids if ids is not None else ["7167"], limit=limit)
        if source == "ClinVar"
        else client.concepts(ids if ids is not None else ["MEDGEN:C1"])
    )


def fixture(source, path="temp_data"):
    return {
        "ClinVar": clinvar.FixtureClinVarClient,
        "MedGen": medgen.FixtureMedGenClient,
        "DISEASES": diseases.FixtureDISEASESClient,
    }[source](path, retrieved_at="original fixture")


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
def test_native_queries_versions_identity_and_host_credit(monkeypatch, source):
    calls = serve(monkeypatch, ncbi(source))
    with ackredit.capture("host") as host, sabueso.attribution() as run:
        result = ask(
            source,
            online(source),
            iter(["7167", "7167"])
            if source == "ClinVar"
            else iter(["MEDGEN:C1", "C1"]),
        )
    (record,) = run.acquisitions
    assert len(calls) == 3 and record["outcome"] == "received" and record["count"] == 1
    assert record["source_version"] == {
        "value": "2026/10/01",
        "basis": "ncbi_database_build"
        if source == "ClinVar"
        else "ncbi_database_lastupdate",
    }
    assert len(record["completed_pages"]) == 3 and record["network_attempts"] == 3
    assert record["provider"]["status"] == "available"
    portable = ackredit.Attribution.from_dict(record["provider"]["attribution"])
    assert {item["id"] for item in portable.to_dict()["items"]} <= {
        item["id"] for item in host.attribution.to_dict()["items"]
    }
    if source == "ClinVar":
        assert result["record"][0]["germline_classification"]["description"].startswith(
            "Conflicting"
        )
        assert record["association_context"]["variant_versions"] == [
            {"uid": "1", "accession": "VCV000000001", "accession_version": "3"}
        ]
        assert record["bibliography"][-1]["doi"] == "10.1093/nar/gkt1113"
    else:
        assert result["record"] == {"C1": "1"}
        assert record["association_context"]["identity_pairs"] == [
            {"concept_id": "C1", "uid": "1"}
        ]
        assert record["bibliography"][-1]["year"] == 2012


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
@pytest.mark.parametrize("empty", [False, True])
def test_empty_answers_and_unknown_versions_are_explicit(monkeypatch, source, empty):
    serve(monkeypatch, ncbi(source, empty=empty, missing_version=True))
    with sabueso.attribution() as run:
        result = ask(source, online(source))
    (record,) = run.acquisitions
    assert record["outcome"] == ("empty" if empty else "received")
    assert record["source_version"] == {"value": None, "basis": "not_stated"}
    assert record["count"] == len(result["record"])


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
@pytest.mark.parametrize(
    "defect",
    [
        "missing_info",
        "missing_search",
        "bad_count",
        "missing_summary",
        "missing_uid",
        "duplicate_uid",
        "native_error",
    ],
)
def test_protocol_failures_never_become_scientific_absence(monkeypatch, source, defect):
    good = ncbi(source)

    def broken(request, number):
        value = good(request, number)
        if defect == "missing_info" and number == 1:
            return {}
        if number == 2:
            if defect == "missing_search":
                return {}
            if defect == "bad_count":
                value["esearchresult"]["count"] = "0"
            if defect == "native_error":
                value["esearchresult"]["ERROR"] = "invalid search"
        if number == 3:
            if defect == "missing_summary":
                return {}
            if defect == "missing_uid":
                value["result"]["uids"] = []
            if defect == "duplicate_uid":
                value["result"]["uids"] = ["1", "1"]
        return value

    serve(monkeypatch, broken)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask(source, online(source))
    (record,) = run.acquisitions
    assert (
        record["outcome"] in ("failed", "partial")
        and record["terminal_outcome"] == "failed"
    )
    assert record["pages"][-1]["outcome"] == "unobserved"
    assert record["incomplete"]


def test_clinvar_cap_and_overlapping_genes_are_counted_per_gene(monkeypatch):
    base = ncbi("ClinVar")

    def answer(request, number):
        value = base(request, number)
        if "esearchresult" in value:
            value["esearchresult"]["count"] = "7"
        return value

    serve(monkeypatch, answer)
    with sabueso.attribution() as run:
        result = ask("ClinVar", online("ClinVar"), ["7167", "1"], limit=1)
    (record,) = run.acquisitions
    assert result["total_count"] == record["total_count"] == 14
    assert len(result["record"]) == record["count"] == 2 and record["truncated"]
    assert [
        row["uid"] for row in record["association_context"]["variant_versions"]
    ] == ["1", "1"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("uid", "2"),
        ("uid", None),
        ("germline_classification", []),
        ("variation_set", ["invalid"]),
        ("germline_classification", {"trait_set": ["invalid"]}),
    ],
)
def test_invalid_clinvar_summary_shapes_are_connector_failures(
    monkeypatch, field, value
):
    base = ncbi("ClinVar")

    def answer(request, number):
        payload = base(request, number)
        if number == 3:
            payload["result"]["1"][field] = value
        return payload

    serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask("ClinVar", online("ClinVar"))
    assert run.acquisitions[0]["terminal_outcome"] == "failed"


@pytest.mark.parametrize("defect", ["ambiguous", "capped", "missing_concept"])
def test_medgen_refuses_ambiguous_or_incomplete_identity(monkeypatch, defect):
    base = ncbi("MedGen")

    def answer(request, number):
        value = base(request, number)
        if defect == "ambiguous" and number == 2:
            return {"esearchresult": {"count": "2", "idlist": ["1", "2"]}}
        if defect == "ambiguous" and number == 3:
            return {
                "result": {
                    "uids": ["1", "2"],
                    "1": {"conceptid": "C1"},
                    "2": {"conceptid": "C1"},
                }
            }
        if defect == "capped" and number == 2:
            return {
                "esearchresult": {
                    "count": "1001",
                    "idlist": [str(i) for i in range(1000)],
                }
            }
        if defect == "missing_concept" and number == 3:
            value["result"]["1"] = {}
        return value

    serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask("MedGen", online("MedGen"))
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["terminal_outcome"] == "failed"
    if defect == "ambiguous":
        assert len(record["association_context"]["identity_pairs"]) == 2
    elif defect == "capped":
        assert record["truncated"] and record["total_count"] == 1001


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_archive_reuse_retains_original_pages_dates_and_response_identity(
    tmp_path, monkeypatch, source, mode
):
    calls = serve(monkeypatch, ncbi(source))
    archive = sabueso.RetrievalArchive(tmp_path / "archive.db")
    with archive.recording(), sabueso.attribution() as original:
        first = ask(source, online(source))
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with sabueso.attribution() as reused:
            second = ask(source, online(source))
    (a,) = original.acquisitions
    (b,) = reused.acquisitions
    assert len(calls) == 3 and first == second
    assert b["access"] == mode and b["network_attempts"] == 0
    assert a["pages"] == b["pages"] and a["retrieved_at"] == b["retrieved_at"]
    assert [r["retrieval_ref"] for r in a["requests"]] == [
        r["retrieval_ref"] for r in b["requests"]
    ]


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
@pytest.mark.parametrize("failed", [False, True])
def test_ncbi_personal_keys_do_not_enter_trace_archive_or_errors(
    tmp_path, monkeypatch, source, failed
):
    secret = "synthetic key/+?&"
    good = ncbi(source)

    def answer(request, number):
        if failed:
            return HTTPError(request.full_url, 400, request.full_url, None, None)
        return good(request, number)

    calls = serve(monkeypatch, answer)
    archive = sabueso.RetrievalArchive(tmp_path / "keys.db")
    with archive.recording(), sabueso.attribution() as run:
        if failed:
            with pytest.raises(ConnectorError) as caught:
                ask(source, online(source, api_key=secret))
            assert secret not in str(caught.value) and "synthetic+key" not in str(
                caught.value
            )
        else:
            ask(source, online(source, api_key=secret))
    assert parse_qs(urlsplit(calls[0].full_url).query)["api_key"] == [secret]
    serialized = json.dumps(run.acquisitions)
    assert secret not in serialized and "synthetic+key" not in serialized
    assert b"synthetic+key" not in (tmp_path / "keys.db").read_bytes()
    if not failed:
        with archive.replaying(), sabueso.attribution() as replay:
            ask(source, online(source, api_key="another synthetic key"))
        assert replay.acquisitions[0]["access"] == "replay" and len(calls) == 3


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
def test_ncbi_later_batch_failure_keeps_original_completed_rows(monkeypatch, source):
    base = ncbi(source)
    if source == "ClinVar":
        monkeypatch.setattr(clinvar, "BATCH", 1)
    else:
        monkeypatch.setattr(medgen, "BATCH", 1)

    def answer(request, number):
        if number == 4:
            return TimeoutError("later batch failed")
        if source == "ClinVar" and number == 2:
            return {"esearchresult": {"count": "2", "idlist": ["1", "2"]}}
        return base(request, number)

    serve(monkeypatch, answer)
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask(
            source,
            online(source),
            ["7167"] if source == "ClinVar" else ["C1", "C2"],
            limit=2,
        )
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["count"] == 1
    assert record["provider"]["status"] == "available"


def test_diseases_channel_receipt_and_memory_reuse_keep_original_time(monkeypatch):
    clock = ["2026-10-01T00:00:00+00:00"]
    monkeypatch.setattr(_http, "_clock", lambda: clock[0])
    calls = serve(monkeypatch, TSV, "Thu, 01 Oct 2026 00:00:00 GMT")
    client = diseases.OnlineDISEASESClient()
    with sabueso.attribution() as original:
        first = client.associations(iter(["ENSP1.4"]), iter(["knowledge"]))
    clock[0] = "2026-10-02T00:00:00+00:00"
    with sabueso.attribution() as repeated:
        second = client.associations(["ENSP1"], ["knowledge"])
    (a,) = original.acquisitions
    (b,) = repeated.acquisitions
    assert first == second and second["retrieved_at"] == "2026-10-01T00:00:00+00:00"
    assert (
        len(calls) == 2
        and b["access"] == "mixed"
        and b["pages"][0]["access"] == "memory"
    )
    assert a["pages"][0]["index_origin"] == b["pages"][0]["index_origin"]
    assert (
        a["pages"][0]["index_origin"]["response_identity"]["hash"]
        == sha256(TSV).hexdigest()
    )
    assert b["source_version"]["value"] == {"knowledge": "2026-10-01"}
    assert b["normalized_query"] == {"proteins": ["ENSP1"], "channels": ["knowledge"]}
    assert len(b["bibliography"][-1]["authors"]) == 4


def test_diseases_disk_cache_origin_is_not_invented(tmp_path, monkeypatch):
    serve(monkeypatch, TSV, "Thu, 01 Oct 2026 00:00:00 GMT")
    client = diseases.OnlineDISEASESClient(cache_dir=tmp_path)
    client.associations(["ENSP1"], ["knowledge"])
    _release.forget("DISEASES")
    with sabueso.attribution() as run:
        client.associations(["ENSP1"], ["knowledge"])
    (record,) = run.acquisitions
    assert (
        record["pages"][0]["access"] == "disk"
        and record["pages"][0]["index_origin"] is None
    )
    assert (
        record["retrieved_at"] is None
        and record["retrieved_at_basis"] == "original_channel_time_not_observed"
    )
    assert record["association_context"]["client_time_basis"].startswith(
        "query_clock_fallback"
    )


@pytest.mark.parametrize("mode", ["reuse", "replay"])
def test_diseases_archive_keeps_raw_file_receipt(tmp_path, monkeypatch, mode):
    calls = serve(monkeypatch, TSV, "Thu, 01 Oct 2026 00:00:00 GMT")
    archive = sabueso.RetrievalArchive(tmp_path / "diseases.db")
    with archive.recording(), sabueso.attribution() as original:
        first = diseases.OnlineDISEASESClient().associations(["ENSP1"], ["knowledge"])
    _release.forget("DISEASES")
    with archive.reusing(timedelta(days=1)) if mode == "reuse" else archive.replaying():
        with sabueso.attribution() as run:
            second = diseases.OnlineDISEASESClient().associations(
                ["ENSP1"], ["knowledge"]
            )
    (a,) = original.acquisitions
    (b,) = run.acquisitions
    assert len(calls) == 1 and first == second and b["access"] == mode
    assert (
        a["pages"][0]["index_origin"]["retrieved_at"]
        == b["pages"][0]["index_origin"]["retrieved_at"]
    )


def test_diseases_partial_channels_and_bad_tsv_do_not_report_absence(monkeypatch):
    serve(
        monkeypatch,
        lambda request, number: TSV if number == 1 else b"<html>service error</html>",
    )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        diseases.OnlineDISEASESClient().associations(
            ["ENSP1"], ["knowledge", "experiments"]
        )
    (record,) = run.acquisitions
    assert record["outcome"] == "partial" and record["count"] == 1
    assert (
        record["terminal_outcome"] == "failed" and len(record["completed_pages"]) == 1
    )


@pytest.mark.parametrize("source", ["ClinVar", "MedGen", "DISEASES"])
def test_missing_fixtures_are_unavailable_not_evaluated_empty(tmp_path, source):
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        client = fixture(source, tmp_path)
        if source == "DISEASES":
            client.associations(["ENSP1"])
        else:
            ask(source, client)
    (record,) = run.acquisitions
    assert (
        record["outcome"] == "unavailable"
        and record["provider"]["status"] == "not_attempted"
    )


@pytest.mark.parametrize("source", ["ClinVar", "MedGen", "DISEASES"])
def test_fixture_queries_counts_and_subset_absence(source):
    client = fixture(source)
    with sabueso.attribution() as run:
        if source == "DISEASES":
            result = client.associations(iter(["ENSP00000229270"]), iter(["knowledge"]))
        else:
            result = ask(
                source,
                client,
                ["7167"] if source == "ClinVar" else ["C1860808"],
                limit=2,
            )
    (record,) = run.acquisitions
    assert record["outcome"] == "received" and record["network_attempts"] == 0
    assert (
        record["association_context"]["scope"] == "fixture_subset"
        if source != "DISEASES"
        else record["pages"][0]["index_origin"]["scope"] == "fixture_subset"
    )
    assert record["count"] == (
        sum(map(len, result["record"].values()))
        if source == "DISEASES"
        else len(result["record"])
    )
    assert record["provider"]["status"] == "available" and record["bibliography_gaps"]


@pytest.mark.parametrize("source", ["ClinVar", "MedGen", "DISEASES"])
def test_offline_calls_are_not_queried(monkeypatch, source):
    monkeypatch.setattr(_mirror, "offline", lambda: True)
    with sabueso.attribution() as run, pytest.raises(OfflineError):
        if source == "DISEASES":
            diseases.OnlineDISEASESClient().associations(["ENSP1"])
        else:
            ask(source, online(source))
    (record,) = run.acquisitions
    assert record["outcome"] == "not_queried" and record["network_attempts"] == 0


def test_different_clinvar_fixture_versions_are_not_silently_combined(tmp_path):
    path = tmp_path / "clinvar"
    path.mkdir()
    for gene, version in (("1", "old"), ("2", "new")):
        (path / f"{gene}.json").write_text(
            json.dumps({"version": version, "record": [], "total_count": 0})
        )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask("ClinVar", fixture("ClinVar", tmp_path), ["1", "2"])
    (record,) = run.acquisitions
    assert (
        record["outcome"] == "partial"
        and not record["association_context"]["versions_consistent"]
    )
    assert record["source_version"]["value"] is None


@pytest.mark.parametrize("source", ["ClinVar", "MedGen", "DISEASES"])
def test_malformed_fixtures_are_failed_not_missing(tmp_path, source):
    directory = tmp_path / source.lower()
    directory.mkdir()
    filename = {
        "ClinVar": "7167.json",
        "MedGen": "concepts.json",
        "DISEASES": "versions.json",
    }[source]
    (directory / filename).write_text("[]")
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        client = fixture(source, tmp_path)
        if source == "DISEASES":
            client.associations(["ENSP1"])
        else:
            ask(source, client)
    assert run.acquisitions[0]["outcome"] == "failed"


@pytest.mark.parametrize("source", ["ClinVar", "MedGen"])
def test_empty_identifier_query_does_not_claim_empty_source_search(monkeypatch, source):
    calls = serve(monkeypatch, ncbi(source))
    with sabueso.attribution() as run:
        ask(source, online(source), [])
    assert len(calls) == 1 and run.acquisitions[0]["outcome"] == "not_queried"
    assert run.acquisitions[0]["provider"]["status"] == "not_attempted"


def test_partial_clinvar_fixture_keeps_received_subset_and_unavailable_terminal(
    tmp_path,
):
    directory = tmp_path / "clinvar"
    directory.mkdir()
    (directory / "1.json").write_text(
        json.dumps(
            {"version": "v1", "total_count": 2, "record": [{"uid": "1"}, {"uid": "2"}]}
        )
    )
    with sabueso.attribution() as run, pytest.raises(ConnectorError):
        ask("ClinVar", fixture("ClinVar", tmp_path), ["1", "2"], limit=1)
    (record,) = run.acquisitions
    assert (
        record["count"] == 1
        and record["outcome"] == "partial"
        and record["terminal_outcome"] == "unavailable"
    )
    assert record["provider"]["status"] == "available"


@pytest.mark.parametrize("source", ["ClinVar", "MedGen", "DISEASES"])
def test_provider_failure_preserves_the_scientific_result(monkeypatch, source):
    client = fixture(source)

    def call():
        return (
            client.associations(["ENSP00000229270"], ["knowledge"])
            if source == "DISEASES"
            else ask(source, client, ["7167"] if source == "ClinVar" else ["C1860808"])
        )

    before = deepcopy(call())
    monkeypatch.setattr(
        adapter,
        "_load_backend",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic provider failure")),
    )
    with sabueso.attribution() as run, pytest.warns(AttributionTrackingWarning):
        after = call()
    assert after == before and run.acquisitions[0]["provider"]["status"] == "failed"


def test_saved_lookup_trace_and_attribution_reader_are_inert(monkeypatch):
    result = clinvar.get_variants(["7167"], limit=2, client=fixture("ClinVar"))
    (record,) = result["acquisition_trace"]["records"]
    assert record["response_identity"]["hash"] == digest(
        canonical_json(result["record"]["variants"])
    )
    frozen = json.dumps(result)
    before = ackredit.get_attribution().to_dict()

    def refuse(*args, **kwargs):
        raise AssertionError("historical read cannot acquire or credit")

    monkeypatch.setattr(ackredit, "track_item", refuse)
    monkeypatch.setattr(_http, "_urlopen", refuse)
    with sabueso.attribution() as run:
        saved = json.loads(frozen)
        ackredit.Attribution.from_dict(
            saved["acquisition_trace"]["records"][0]["provider"]["attribution"]
        )
    assert not run.acquisitions and ackredit.get_attribution().to_dict() == before
