"""EMA native page occurrences, procedural scope, declared totals and replay."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import retention, source_terms
from sabueso.mappings.ema_orphan import map_designations, response_query
from sabueso.tools.db.ema_orphan import (
    URL,
    FixtureEmaOrphanClient,
    SnapshotEmaOrphanClient,
    get_designations,
)

PATH = Path("temp_data/ema_orphan/designations.json")
TARGET = "EU/3/23/2858"
SOURCE = "EMA Orphan Designations"


def native():
    return json.loads(PATH.read_bytes())


def small():
    p = native()
    p["data"] = [x for x in p["data"] if x["eu_designation_number"] == TARGET]
    p["meta"]["total_records"] = len(p["data"])
    return p


class Client:
    def __init__(self, payload, **context):
        self.payload, self.context = payload, context

    def designations(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": SOURCE,
        "kind": "designations",
        "query": response_query(TARGET),
        "retrieved_at": "2026-10-06T12:00:00+00:00",
    }


def test_full_native_export_retains_duplicates_dates_and_original_page_identity():
    assert len(PATH.read_bytes()) == 2070548
    assert (
        hashlib.sha256(PATH.read_bytes()).hexdigest()
        == "8a83500533765c0d43a63b58581ef9c51d2df6f709fdc1d61c6f0ac74a80fd54"
    )
    e = get_designations(TARGET, client=FixtureEmaOrphanClient())
    before = copy.deepcopy(e)
    a = map_designations(e)
    assert len(a) == len({x["id"] for x in a}) == 2
    assert [x["asserted_value"] for x in a] == small()["data"]
    assert [x["asserted_value"]["date_of_designation_or_refusal"] for x in a] == [
        "22/06/2025",
        "08/11/2023",
    ]
    assert len({x["subject_ref"] for x in a}) == 2
    assert all(
        x["subject_ref"]
        == "ema:orphan_page:" + x["asserted_value"]["orphan_designation_url"]
        for x in a
    )
    assert all(
        x["asserted_value"]["status"] == "Positive"
        and x["asserted_value"]["medicine_name"] == ""
        for x in a
    )
    assert all(
        x["source"]["version"] is None
        and x["retrieved_at"] is None
        and "knowledge_class" not in x
        for x in a
    )
    assert e["record"] == native()
    assert e["record"]["meta"] == {
        "total_records": 3310,
        "timestamp": "2026-10-06T18:05:23Z",
    }
    trace = e["acquisition_trace"]["records"][0]
    assert (
        trace["count"] == 2
        and trace["received_export_rows"] == 3310
        and trace["network_attempts"] == 0
    )
    assert (
        e["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert e == before
    a[0]["asserted_value"].clear()
    assert e == before


def test_withdrawn_designation_does_not_create_drug_or_protein_intervention():
    a = map_designations(
        get_designations("EU/3/18/2020", client=FixtureEmaOrphanClient())
    )
    assert len(a) == 1
    row = a[0]["asserted_value"]
    assert row["status"] == "Withdrawn" and row["active_substance"] == "daratumumab"
    assert row["intended_use"] == "Treatment of AL amyloidosis"
    assert (
        "modality" not in row
        and "target_ref" not in row
        and "intervention_ref" not in row
    )


def test_native_product_reference_is_literal_without_product_status_transfer():
    a = map_designations(
        get_designations("EU/3/18/2115", client=FixtureEmaOrphanClient())
    )
    assert a[0]["asserted_value"]["related_ema_product_number"] == "EMEA/H/C/005909"
    assert a[0]["asserted_value"]["medicine_name"] == "Isembyld"
    assert "marketing_authorisation" not in a[0]["asserted_value"]


def test_unresolved_native_references_are_retained_in_the_full_export():
    e = get_designations(TARGET, client=FixtureEmaOrphanClient())
    refs = [r["eu_designation_number"] for r in e["record"]["data"]]
    assert refs.count("-") == 35 and refs.count("N/A") == 1
    assert "EMA/OD/0000149115" in refs


def test_equal_repeated_conflicting_and_future_fields_are_not_collapsed():
    p = small()
    p["data"].append(copy.deepcopy(p["data"][0]))
    p["data"].append(copy.deepcopy(p["data"][0]))
    p["data"][-1]["status"] = "Future procedure label"
    p["data"][-1]["date_of_designation_or_refusal"] = "unknown native date"
    p["data"][-1]["additional_native_context"] = {"label": "original"}
    p["meta"]["total_records"] = 4
    a = map_designations(get_designations(TARGET, client=Client(p)))
    assert len(a) == len({x["id"] for x in a}) == 4
    assert a[0]["asserted_value"] == a[2]["asserted_value"]
    assert a[0]["subject_ref"] == a[2]["subject_ref"]
    assert a[3]["asserted_value"]["status"] == "Future procedure label"
    assert a[3]["asserted_value"]["additional_native_context"] == {"label": "original"}


def test_not_listed_and_empty_declared_export_are_not_biological_negatives():
    e = get_designations("EU/3/99/999999", client=FixtureEmaOrphanClient())
    assert map_designations(e) == []
    assert (
        e["acquisition_trace"]["records"][0]["native_result_declaration"]
        == "not_listed_in_received_export"
    )
    p = small()
    p["data"] = []
    p["meta"]["total_records"] = 0
    assert map_designations(get_designations(TARGET, client=Client(p))) == []


@pytest.mark.parametrize(
    "identifier",
    [
        "daratumumab",
        "P00533",
        "EU/3/18/2020,EU/3/23/2858",
        "eu/3/23/2858",
        "EU/3/2023/2858",
        "EU/3/23/2858/x",
        "EU/3/23",
        "-",
        "N/A",
        None,
        2858,
    ],
)
def test_exact_query_identity_is_required(identifier):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_designations(identifier, client=Client(small()))


def test_backend_checks_survive_skipped_digestion():
    assert (
        len(
            map_designations(
                get_designations(" " + TARGET + " ", client=Client(small()))
            )
        )
        == 2
    )
    with pytest.raises(ConnectorError):
        get_designations(
            " " + TARGET + " ", client=Client(small()), skip_digestion=True
        )
    assert (
        map_designations(get_designations("EU/3/23/02858", client=Client(small())))
        == []
    )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"data": []},
        {"meta": {}},
        {"meta": {"total_records": 0, "timestamp": "2026-10-06T18:05:23Z"}, "data": {}},
    ],
)
def test_native_export_shape_is_required(payload):
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=Client(payload))


@pytest.mark.parametrize(
    "key,value",
    [
        ("total_records", 1),
        ("total_records", "2"),
        ("total_records", True),
        ("total_records", -1),
        ("timestamp", "2026-10-06"),
        ("timestamp", "2026-13-06T18:05:23Z"),
        ("timestamp", None),
    ],
)
def test_declared_coverage_and_generation_time_fail_closed(key, value):
    p = small()
    p["meta"][key] = value
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=Client(p))


@pytest.mark.parametrize(
    "key,value",
    [
        ("active_substance", None),
        ("status", 7),
        ("eu_designation_number", ""),
        ("orphan_designation_url", "https://other.invalid/page"),
        (
            "orphan_designation_url",
            "https://www.ema.europa.eu/en/medicines/human/orphan-designations/../other",
        ),
        ("extra", float("nan")),
    ],
)
def test_unrelated_bad_row_is_rejected_before_query_selection(key, value):
    p = small()
    p["data"][1]["eu_designation_number"] = "EU/3/99/9"
    p["data"][1][key] = value
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=Client(p))


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "medicines"),
        ("query", {"eu_designation_number": TARGET, "dataset": "medicines"}),
        ("version", "2026-10-06T18:05:23Z"),
        ("truncated", True),
        ("truncated", None),
    ],
)
def test_mapping_rechecks_scope_and_generation_is_not_revision(key, value):
    e = get_designations(TARGET, client=Client(small()))
    e[key] = value
    with pytest.raises(ConnectorError):
        map_designations(e)


@pytest.mark.parametrize(
    "context",
    [{"version": "2026-10-06T18:05:23Z"}, {"truncated": True}, {"truncated": None}],
)
def test_lookup_rejects_invented_revision_or_cut(context):
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=Client(small(), **context))


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_hash_time_terms_and_no_new_access_credit(tmp_path, compressed):
    b = PATH.read_bytes()
    b = gzip.compress(b) if compressed else b
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(b)
    m = metadata()
    m["terms"] = {"licence": "FREE-WITH-ACKNOWLEDGEMENT"}
    c = SnapshotEmaOrphanClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(b).hexdigest()
    )
    m["query"]["eu_designation_number"] = "EU/3/99/9"
    e = get_designations(TARGET, client=c)
    assert e["record"] == native() and e["retrieved_at"] == metadata()["retrieved_at"]
    assert e["retrieved_at"] != e["record"]["meta"]["timestamp"]
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(b).hexdigest()
    assert e["snapshot_receipt"]["declared_terms"] == {
        "licence": "FREE-WITH-ACKNOWLEDGEMENT"
    }
    assert e["snapshot_receipt"]["source_access_observed"] is False
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_designations(
            TARGET,
            client=SnapshotEmaOrphanClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "medicines"),
        ("query", response_query("EU/3/99/9")),
        ("version", "2026-10-06T18:05:23Z"),
    ],
)
def test_supplied_snapshot_binding_is_exact(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_bytes(PATH.read_bytes())
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=SnapshotEmaOrphanClient(p, source_metadata=m))


@pytest.mark.parametrize(
    "raw",
    [
        b'{"meta":{},"meta":{},"data":[]}',
        b'{"meta":{"total_records":NaN},"data":[]}',
        b"\xff",
        b"<html>blocked</html>",
    ],
)
def test_invalid_json_bytes_are_not_valid_supplied_records(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_designations(
            TARGET, client=SnapshotEmaOrphanClient(p, source_metadata=metadata())
        )


def test_missing_fixture_and_corrupt_gzip_are_not_no_designations(tmp_path):
    with pytest.raises(ConnectorError):
        get_designations(TARGET, client=FixtureEmaOrphanClient(tmp_path))
    p = tmp_path / "bad.json.gz"
    p.write_bytes(b"not gzip")
    with pytest.raises(ConnectorError):
        get_designations(
            TARGET, client=SnapshotEmaOrphanClient(p, source_metadata=metadata())
        )


@pytest.mark.parametrize("status", [404, 429, 503])
def test_failed_http_access_is_not_empty_export(monkeypatch, status):
    from sabueso.tools.db import _http as http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_designations(TARGET)


def test_one_get_replay_retains_original_response_identity_time_and_terms(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http as http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "ema.db")
    with archive.recording():
        first = get_designations(TARGET)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Replay must not fetch EMA pages, medicine data or linked documents."
        )

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_designations(TARGET)
    assert calls == [URL]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_designations(first) == map_designations(second)
    observed = first["acquisition_trace"]["records"][0]
    replayed = second["acquisition_trace"]["records"][0]
    assert observed["network_attempts"] == observed["received_responses"] == 1
    assert replayed["network_attempts"] == 0 and replayed["access"] == "replay"
    assert observed["response_identity"] == replayed["response_identity"]
    assert source_terms()[SOURCE]["licence"] == "FREE-WITH-ACKNOWLEDGEMENT"
    assert retention(SOURCE)["keep"] == "yes"
