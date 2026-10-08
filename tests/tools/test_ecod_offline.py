"""Qualified ECOD UID scope, native hierarchy and independent source provenance."""

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
from sabueso.mappings.ecod import URL, map_domain, response_query
from sabueso.tools.db.ecod import FixtureECODClient, SnapshotECODClient, get_domain

PATH = Path("temp_data/ecod/domain__80374.json")


def native():
    return json.loads(PATH.read_bytes())


class Client:
    def __init__(self, record, **context):
        self.record, self.context = record, context

    def domain(self, identifier):
        return {
            "record": self.record,
            "retrieved_at": None,
            "version": None,
            **self.context,
        }


def read(record, **context):
    return get_domain("80374", client=Client(record, **context))


def metadata():
    return {"source": "ECOD", "kind": "domain", "query": response_query("80374")}


def test_native_domain_keeps_source_uid_hierarchy_false_flags_and_opaque_range():
    e = get_domain("000080374", client=FixtureECODClient())
    before = copy.deepcopy(e)
    a = map_domain(e)[0]
    v = a["asserted_value"]
    assert e["record"] == native() and e["query"] == {"uid": 80374}
    assert a["subject_ref"] == "ecod:uid:80374"
    assert v["ecod_domain_id"] == "e1iepA1" and v["source_id"] == "1iep_A"
    assert v["range"] == "A:228-498" and v["uniprot_acc"] == "P00520"
    assert v["classification"]["family"] == {
        "id": "206.1.1.20",
        "name": "PK_Tyr_Ser-Thr",
    }
    assert v["is_manual"] is v["is_representative"] is False
    assert a["source"]["version"] is a["retrieved_at"] is None
    assert a["source_metadata"]["native_response"] == native()
    assert "files" not in v and "location" not in v and "sequence" not in v
    trace = e["acquisition_trace"]["records"][0]
    assert trace["count"] == 1 and trace["outcome"] == "received"
    assert trace["access"] == "supplied_file" and trace["network_attempts"] == 0
    assert any(
        b["id"] == "url:http://prodata.swmed.edu/ecod/" for b in trace["bibliography"]
    )
    assert source_terms()["ECOD"]["licence"] == "NOT-STATED"
    a["asserted_value"]["classification"].clear()
    a["source_metadata"]["native_response"].clear()
    assert e == before


def test_discontinuous_other_chain_insertions_null_pointer_and_unassigned_family_survive():
    p = native()
    p.update(range="A:-3A-40,A:90-120,B:4-12", uniprot_acc=None, is_manual=True)
    p["classification"]["family"] = {"id": "206.1.1.0", "name": "NO_F_NAME"}
    p["future_field"] = {"unknown_unit": 4}
    a = map_domain(read(p))[0]
    assert a["asserted_value"]["range"] == p["range"]
    assert a["asserted_value"]["uniprot_acc"] is None
    assert a["asserted_value"]["classification"]["family"]["id"] == "206.1.1.0"
    assert a["source_metadata"]["native_response"]["future_field"] == p["future_field"]
    assert "future_field" not in a["asserted_value"]


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(uid=80375),
        lambda p: p.update(uid=True),
        lambda p: p.update(uid="80374"),
        lambda p: p.update(type="AlphaFold model"),
        lambda p: p.update(type=None),
        lambda p: p.update(ecod_domain_id="e1iepB1"),
        lambda p: p.update(ecod_domain_id="e1iepa1"),
        lambda p: p.update(source_id="1iep_B"),
        lambda p: p.update(chain_id="a"),
        lambda p: p.update(range=None),
        lambda p: p.update(range=""),
        lambda p: p.pop("uniprot_acc"),
        lambda p: p.update(uniprot_acc=[]),
        lambda p: p.update(is_manual=0),
        lambda p: p.pop("is_representative"),
        lambda p: p.update(classification={}),
        lambda p: p["classification"].update(family="PK_Tyr_Ser-Thr"),
        lambda p: p["classification"]["h_group"].update(id="207.1"),
        lambda p: p["classification"]["t_group"].update(id="206.1.1.20"),
        lambda p: p["classification"]["architecture"].update(id="206"),
        lambda p: p["classification"]["family"].update(name=None),
        lambda p: p["files"].update(pdb="/ecod/api/v1/domains/80375/pdb"),
        lambda p: p.update(future=float("nan")),
        lambda p: p.clear(),
    ],
)
def test_identity_origin_hierarchy_flags_and_nonfinite_json_fail_closed(change):
    p = native()
    change(p)
    with pytest.raises(ConnectorError):
        read(p)


@pytest.mark.parametrize(
    "identifier",
    [
        "e1iepA1",
        "P00520",
        "../80374",
        "80374?x",
        "-1",
        "1.0",
        "١",
        "0000080374",
        None,
        True,
        80374,
    ],
)
def test_non_uid_queries_never_reach_transport_even_without_digestion(identifier):
    class Forbidden:
        def domain(self, identifier):
            pytest.fail("Invalid UID reached ECOD.")

    for skip in (False, True):
        with pytest.raises((ArgumentError, ConnectorError)):
            get_domain(identifier, client=Forbidden(), skip_digestion=skip)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source", "PDB"),
        ("kind", "all_domains"),
        ("query", {"uid": 80375}),
        ("query", {"uid": 80374.0}),
        ("version", "v295.2"),
        ("truncated", True),
    ],
)
def test_foreign_client_context_is_refused_before_source_assertions(key, value):
    with pytest.raises(ConnectorError):
        read(native(), **{key: value})
    e = read(native())
    e[key] = value
    with pytest.raises(ConnectorError):
        map_domain(e)


@pytest.mark.parametrize("compressed", [False, True])
def test_supplied_json_binds_uid_hash_and_original_time_without_network(
    tmp_path, compressed
):
    raw = PATH.read_bytes()
    p = tmp_path / ("domain.json.gz" if compressed else "domain.json")
    data = gzip.compress(raw) if compressed else raw
    p.write_bytes(data)
    m = metadata()
    m["retrieved_at"] = "2026-10-07T08:00:00+00:00"
    checksum = hashlib.sha256(data).hexdigest()
    e = get_domain(
        "80374",
        client=SnapshotECODClient(p, source_metadata=m, expected_sha256=checksum),
    )
    assert e["record"] == native() and e["retrieved_at"] == m["retrieved_at"]
    assert e["snapshot_receipt"]["document_sha256"] == checksum
    assert e["snapshot_receipt"]["source_access_observed"] is False
    assert e["acquisition_trace"]["records"][0]["network_attempts"] == 0
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_domain(
            "80374",
            client=SnapshotECODClient(p, source_metadata=m, expected_sha256="0" * 64),
        )
    m["query"] = {"uid": 80375}
    with pytest.raises(ConnectorError):
        get_domain("80374", client=SnapshotECODClient(p, source_metadata=m))


def test_missing_fixture_is_unavailable_not_an_empty_domain(tmp_path):
    with pytest.raises(ConnectorError) as error:
        get_domain("80374", client=FixtureECODClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 429, 500])
def test_http_errors_are_failed_acquisitions_not_biological_absence(
    status, monkeypatch
):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failure", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_domain("80374")
    trace = error.value.acquisition_trace["records"][0]
    assert trace["outcome"] == "failed" and trace["network_attempts"] == 1


def test_archive_records_one_uid_get_and_replays_same_assertion_with_zero_network(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(PATH.read_bytes())
            self.headers = Message()
            self.headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append((request.get_method(), request.full_url))
        return Response()

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "ecod.db")
    with archive.recording():
        first = get_domain("000080374")

    def forbidden(*args, **kwargs):
        pytest.fail("Replay reached the network.")

    monkeypatch.setattr(http, "_urlopen", forbidden)
    with archive.replaying():
        second = get_domain("80374")
    assert calls == [("GET", URL + "80374")]
    assert first["record"] == second["record"] == native()
    assert first["download_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_domain(first) == map_domain(second)
    assert first["acquisition_trace"]["records"][0]["network_attempts"] == 1
    replay = second["acquisition_trace"]["records"][0]
    assert replay["access"] == "replay" and replay["network_attempts"] == 0
