"""Native PRIDE project identity, depositor scope, original bytes and replay."""

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
from sabueso.core.terms import source_terms
from sabueso.mappings.pride import map_project
from sabueso.tools.db.pride import (
    URL,
    FixturePrideClient,
    SnapshotPrideClient,
    get_project,
)

PATH = Path("temp_data/pride/project__PXD013616.json")
TARGET = "PXD013616"


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, payload, **context):
        self.payload, self.context = payload, context

    def project(self, identifier):
        return {
            "record": self.payload,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def metadata():
    return {
        "source": "PRIDE",
        "kind": "project",
        "query": {"project_accession": TARGET},
    }


def test_native_project_preserves_protocols_cv_terms_licence_and_all_original_context():
    raw = PATH.read_bytes()
    assert (
        len(raw) == 8484
        and hashlib.sha256(raw).hexdigest()
        == "b5ff728947d5e0e394633022e26ba57622ccbfad2d6e9da46b8a60add6c2de71"
    )
    e = get_project("pxd013616", client=FixturePrideClient())
    before = copy.deepcopy(e)
    (a,) = map_project(e)
    assert a["asserted_value"] == a["source_metadata"]["native_project"] == native()
    assert a["subject_ref"] == "pride:" + TARGET and a["source"]["version"] is None
    assert a["retrieved_at"] is None and a["acquisition"] == {"method": "database"}
    p = a["asserted_value"]
    assert (
        p["license"] == "Creative Commons Public Domain (CC0)"
        and p["submissionType"] == "PARTIAL"
    )
    assert p["publicationDate"] == "2020-04-02" and p["submissionDate"] == "2020-04-01"
    assert p["doi"] == "" and p["references"][0]["doi"] == "10.1126/sciadv.aay4697"
    assert p["identifiedPTMStrings"][0]["accession"] == "MOD:01892"
    assert p["instruments"][0]["accession"] == "MS:1002634" and isinstance(
        p["instruments"][0], dict
    )
    assert p["additionalAttributes"] == [] and p["quantificationMethods"] == []
    assert "protein_ref" not in p and "evidence_class" not in p
    assert a["source_metadata"]["native_license"] == p["license"]
    trace = e["acquisition_trace"]["records"]
    assert len(trace) == 1 and trace[0]["network_attempts"] == 0
    assert trace[0]["native_license"] == p["license"] and trace[0]["count"] == 1
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    a["asserted_value"]["organisms"].clear()
    a["source_metadata"]["native_project"].clear()
    assert e == before


def test_depositor_text_future_labels_and_missing_license_are_not_interpreted():
    p = native()
    p.update(
        license="future_grant",
        submissionType="future_label",
        future_context={"literal": None},
    )
    p["identifiedPTMStrings"].append(copy.deepcopy(p["identifiedPTMStrings"][0]))
    (a,) = map_project(get_project(TARGET, client=Client(p)))
    assert (
        a["asserted_value"] == p
        and a["source_metadata"]["native_license"] == "future_grant"
    )
    p.pop("license")
    (b,) = map_project(get_project(TARGET, client=Client(p)))
    assert (
        "license" not in b["asserted_value"]
        and b["source_metadata"]["native_license"] is None
    )
    assert len(b["asserted_value"]["identifiedPTMStrings"]) == 2


def test_metadata_changes_preserve_independent_support_without_revision_guess():
    p = native()
    a = map_project(get_project(TARGET, client=Client(p)))[0]
    p["references"].append(copy.deepcopy(p["references"][0]))
    p["totalFileDownloads"] += 1
    b = map_project(get_project(TARGET, client=Client(p)))[0]
    assert a["subject_ref"] == b["subject_ref"] and a["id"] != b["id"]
    assert a["source"]["version"] is b["source"]["version"] is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("accession", "PXD013617"),
        ("accession", "pxd013616"),
        ("title", None),
        ("title", ""),
        ("license", []),
        ("projectDescription", {}),
        ("instruments", ["MS:1002634"]),
        ("softwares", [None]),
        ("references", "doi:10.1126/sciadv.aay4697"),
        ("identifiedPTMStrings", [None]),
        ("additionalAttributes", ""),
        ("keywords", {}),
        ("totalFileDownloads", True),
        ("botCount", -1),
        ("extra", float("inf")),
    ],
)
def test_invalid_native_metadata_does_not_pass_as_a_project(key, value):
    p = native()
    p[key] = value
    with pytest.raises(ConnectorError):
        get_project(TARGET, client=Client(p))


@pytest.mark.parametrize(
    "payload", [None, {}, [], {"detail": "Not Found"}, {"projects": []}]
)
def test_empty_error_and_collection_payloads_are_not_an_identified_project(payload):
    with pytest.raises(ConnectorError):
        get_project(TARGET, client=Client(payload))


@pytest.mark.parametrize(
    "identifier",
    ["RPA1", "P60174", "PXD01361", "PXD000000", "PXD013616?x", "../PXD013616", True],
)
def test_invalid_project_never_reaches_client_even_with_skip(identifier):
    class Forbidden:
        def project(self, identifier):
            pytest.fail("Invalid project reached client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_project(identifier, client=Forbidden(), skip_digestion=True)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "Proteins API"),
        ("kind", "proteomics"),
        ("version", "3.0"),
        ("truncated", True),
        ("truncated", None),
        ("query", {"project_accession": "PXD013617"}),
    ],
)
def test_mapping_cannot_relabel_source_guess_revision_or_change_scope(key, value):
    e = get_project(TARGET, client=FixturePrideClient())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_project(e)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "3.0"},
        {"truncated": True},
        {"truncated": None},
        {"source": "PeptideAtlas"},
    ],
)
def test_client_revision_or_identity_cannot_override_native_scope(context):
    with pytest.raises(ConnectorError):
        get_project(TARGET, client=Client(native(), **context))


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_snapshot_keeps_original_hash_time_and_depositor_terms(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    raw = gzip.compress(raw) if compressed else raw
    p = tmp_path / ("native.json.gz" if compressed else "native.json")
    p.write_bytes(raw)
    m = metadata()
    m.update(retrieved_at="2026-10-07T12:00:00+00:00", terms={"licence": "CC0-1.0"})
    c = SnapshotPrideClient(
        p, source_metadata=m, expected_sha256=hashlib.sha256(raw).hexdigest()
    )
    m["query"]["project_accession"] = "PXD013617"
    e = get_project(TARGET, client=c)
    assert e["record"] == native() and e["retrieved_at"] == "2026-10-07T12:00:00+00:00"
    assert e["snapshot_receipt"]["declared_terms"] == {"licence": "CC0-1.0"}
    assert e["snapshot_receipt"]["document_sha256"] == hashlib.sha256(raw).hexdigest()
    assert e["snapshot_receipt"]["source_access_observed"] is False
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_project(
            TARGET,
            client=SnapshotPrideClient(
                p, source_metadata=metadata(), expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "other"),
        ("kind", "protein"),
        ("query", {"project_accession": "PXD013617"}),
        ("version", "3.0"),
    ],
)
def test_supplied_snapshot_is_bound_to_its_actual_project(tmp_path, key, value):
    p = tmp_path / "native.json"
    p.write_bytes(PATH.read_bytes())
    m = metadata()
    m[key] = value
    with pytest.raises(ConnectorError):
        get_project(TARGET, client=SnapshotPrideClient(p, source_metadata=m))


@pytest.mark.parametrize(
    "raw",
    [
        b'{"accession":"PXD013616","accession":"PXD013617"}',
        b'{"extra":NaN}',
        b"\xff",
        b"<html>blocked</html>",
    ],
)
def test_invalid_original_json_bytes_are_rejected(tmp_path, raw):
    p = tmp_path / "native.json"
    p.write_bytes(raw)
    with pytest.raises(ConnectorError):
        get_project(TARGET, client=SnapshotPrideClient(p, source_metadata=metadata()))


def test_missing_fixture_and_snapshot_are_unavailable_not_empty(tmp_path):
    for c in [
        FixturePrideClient(tmp_path),
        SnapshotPrideClient(tmp_path / "missing.json", source_metadata=metadata()),
    ]:
        with pytest.raises(ConnectorError):
            get_project(TARGET, client=c)


@pytest.mark.parametrize("status", [404, 429, 503])
def test_unavailable_http_does_not_become_an_empty_object(monkeypatch, status):
    from sabueso.tools.db import _http

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, status, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_project(TARGET)


def test_one_get_replay_preserves_original_time_without_file_or_analysis_requests(
    monkeypatch, tmp_path
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        r = io.BytesIO(PATH.read_bytes())
        r.status = 200
        r.headers = Message()
        r.headers["Content-Type"] = "application/json"
        return r

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "pride.db")
    with archive.recording():
        first = get_project(TARGET)

    def forbidden(*args, **kwargs):
        pytest.fail("Replay fetched linked files or analysis")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_project(TARGET)
    assert calls == [URL + TARGET]
    assert (
        first["record"] == second["record"] == native()
        and first["retrieved_at"] == second["retrieved_at"]
    )
    assert (
        first["download_sha256"]
        == second["download_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert map_project(first) == map_project(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    assert second["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["PRIDE"]["licence"] == "DEPOSITOR-TERMS"
