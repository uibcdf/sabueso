"""Native Pharos target fidelity, exact identity, failure states and archive replay."""

import copy
import gzip
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.terms import source_terms, verdict
from sabueso.mappings.pharos import QUERY, URL, map_target, response_query
from sabueso.tools.db.pharos import (
    FixturePharosClient,
    SnapshotPharosClient,
    get_target,
)

PATH = Path("temp_data/pharos/target__P60174.json")
NATIVE = json.loads(PATH.read_text(encoding="utf-8"))


class Client:
    def __init__(self, payload=NATIVE, **context):
        self.payload, self.context = payload, context

    def target(self, identifier):
        return {
            "record": self.payload,
            "version": None,
            "retrieved_at": None,
            **self.context,
        }


def read(payload=NATIVE, **context):
    return get_target("P60174", client=Client(payload, **context))


def metadata():
    return {
        "source": "Pharos/TCRD",
        "kind": "target",
        "query": response_query("P60174"),
    }


def test_original_native_targets_preserve_provider_classes_identity_and_unknown_revision():
    assert (
        hashlib.sha256(PATH.read_bytes()).hexdigest()
        == "e311efdf4da4ce8897b7559b6670cdcf529fa7feb7397e94b163aa27895bb6ed"
    )
    for accession, tdl, symbol in [
        ("P60174", "Tbio", "TPI1"),
        ("P31749", "Tchem", "AKT1"),
    ]:
        envelope = get_target(accession, client=FixturePharosClient())
        before = copy.deepcopy(envelope)
        assertions = map_target(envelope)
        assert len(assertions) == 1
        a = assertions[0]
        assert (
            a["asserted_value"]["tdl"] == tdl and a["asserted_value"]["sym"] == symbol
        )
        assert a["subject_ref"] == f"pharos:target:{accession}"
        assert a["source"]["version"] is envelope["version"] is None
        assert a["source_metadata"]["native_response"] == envelope["record"]
        assert "score" not in a["asserted_value"]
        assert envelope["acquisition_trace"]["records"][0]["count"] == 1
        a["asserted_value"].clear()
        assert envelope == before


def test_native_null_is_received_no_match_not_access_failure():
    envelope = get_target("P00000", client=FixturePharosClient())
    assert envelope["record"] == {"data": {"target": None}}
    assert map_target(envelope) == []
    trace = envelope["acquisition_trace"]["records"][0]
    assert trace["outcome"] == "not_found" and trace["network_attempts"] == 0


@pytest.mark.parametrize("value", [None, "", "future-provider-class"])
def test_native_null_empty_and_future_class_are_not_repaired_or_ranked(value):
    payload = copy.deepcopy(NATIVE)
    payload["data"]["target"]["tdl"] = value
    assert map_target(read(payload))[0]["asserted_value"]["tdl"] == value


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"data": {}},
        {"data": {"target": []}},
        {"errors": [], "data": {"target": None}},
        {"errors": [{"message": "failed"}]},
        {"data": {"target": None, "other": 1}},
        {"data": {"target": {"uniprot": "P60174"}}},
    ],
)
def test_malformed_partial_graphql_errors_never_become_no_match(payload):
    with pytest.raises(ConnectorError):
        read(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("uniprot", "P31749"),
        ("uniprot", "p60174"),
        ("uniprot", None),
        ("tdl", 0),
        ("fam", []),
        ("name", float("nan")),
    ],
)
def test_wrong_identity_type_and_nonfinite_values_fail(field, value):
    payload = copy.deepcopy(NATIVE)
    payload["data"]["target"][field] = value
    with pytest.raises(ConnectorError):
        read(payload)


@pytest.mark.parametrize(
    "identifier",
    [None, "", "p60174", "P60174-1", "uniprot:P60174", "P60174/", "P60174 P31749"],
)
@pytest.mark.parametrize("skip", [False, True])
def test_unsafe_or_nonexact_query_fails_with_and_without_digestion(identifier, skip):
    with pytest.raises((ConnectorError, ArgumentError)):
        get_target(identifier, client=Client(), skip_digestion=skip)


@pytest.mark.parametrize(
    "context",
    [
        {"version": "current"},
        {"truncated": True},
        {"source": "other"},
        {"kind": "search"},
        {"query": {"uniprot": "P31749"}},
    ],
)
def test_foreign_client_context_is_not_resealed(context):
    with pytest.raises(ConnectorError):
        read(**context)


@pytest.mark.parametrize("compressed", [False, True])
def test_bound_native_snapshot_hash_time_and_terms(tmp_path, compressed):
    raw = PATH.read_bytes()
    if compressed:
        raw = gzip.compress(raw)
    path = tmp_path / ("native.json.gz" if compressed else "native.json")
    path.write_bytes(raw)
    declaration = metadata()
    declaration.update(
        retrieved_at="2026-10-07T22:00:00+00:00",
        terms={"licence": "caller declaration"},
    )
    before = copy.deepcopy(declaration)
    envelope = get_target(
        "P60174",
        client=SnapshotPharosClient(
            path,
            source_metadata=declaration,
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    assert envelope["retrieved_at"] == declaration["retrieved_at"]
    assert envelope["snapshot_receipt"]["source_access_observed"] is False
    assert envelope["snapshot_receipt"]["declared_terms"] == declaration["terms"]
    assert declaration == before
    with pytest.raises(ConnectorError):
        get_target(
            "P60174",
            client=SnapshotPharosClient(
                path, source_metadata=declaration, expected_sha256="0" * 64
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "Other"),
        ("kind", "search"),
        ("query", response_query("P31749")),
        ("version", "new"),
    ],
)
def test_bound_snapshot_source_query_revision_fail(tmp_path, field, value):
    path = tmp_path / "native.json"
    path.write_bytes(PATH.read_bytes())
    declaration = metadata()
    declaration[field] = value
    with pytest.raises(ConnectorError):
        get_target(
            "P60174", client=SnapshotPharosClient(path, source_metadata=declaration)
        )


def test_missing_fixture_and_http_error_do_not_mean_absence(tmp_path, monkeypatch):
    from sabueso.tools.db import _http

    with pytest.raises(ConnectorError):
        get_target("P60174", client=FixturePharosClient(tmp_path))

    def fail(request, **kwargs):
        raise HTTPError(request.full_url, 403, "Unavailable", {}, None)

    monkeypatch.setattr(_http, "_urlopen", fail)
    with pytest.raises(ConnectorError):
        get_target("P60174")


def test_one_exact_get_replay_keeps_original_time_and_native_identity(
    tmp_path, monkeypatch
):
    from sabueso.tools.db import _http

    calls = []

    def wire(request, **kwargs):
        calls.append(request.full_url)
        response = io.BytesIO(PATH.read_bytes())
        response.status = 200
        response.headers = Message()
        return response

    monkeypatch.setattr(_http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "archive.sqlite")
    with archive.recording():
        first = get_target("P60174")
    assert len(calls) == 1 and calls[0].startswith(URL + "?")
    wire_query = parse_qs(urlparse(calls[0]).query)
    assert wire_query["query"] == [QUERY]
    assert json.loads(wire_query["variables"][0]) == {"accession": "P60174"}

    def forbidden(*args, **kwargs):
        raise AssertionError("Replay attempted network")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    with archive.replaying():
        replay = get_target("P60174")
    assert first["record"] == replay["record"]
    assert first["retrieved_at"] == replay["retrieved_at"]
    assert first["download_sha256"] == replay["download_sha256"]
    assert map_target(first) == map_target(replay)
    assert replay["acquisition_trace"]["records"][0]["network_attempts"] == 0
    assert source_terms()["Pharos/TCRD"]["licence"] == "NOT-STATED"
    assert verdict("Pharos/TCRD", "redistribution")["verdict"] == "unknown"
